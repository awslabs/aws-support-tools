#!/usr/bin/env python3

import argparse
import ipaddress
import json
import math
import re
import sys
from collections import defaultdict

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

PREFIX_SIZE = 28

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def _sanitize(text):
    """Strip control characters from AWS-sourced strings before printing."""
    if not isinstance(text, str):
        text = str(text)
    return _CONTROL_CHARS.sub("", text)


def _force_utf8_output():
    """Reconfigure stdout and stderr to UTF-8 so the block-map glyphs print on
    any platform. On Windows the default encoding is cp1252, which raises
    UnicodeEncodeError on the box-drawing glyphs when output is redirected or
    piped; UTF-8 avoids that."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


def get_session(profile=None, region=None):
    kw = {}
    if profile:
        kw["profile_name"] = profile
    if region:
        kw["region_name"] = region
    return boto3.Session(**kw)


def parse_cluster_arg(value, region_arg):
    """Resolve --cluster value (name or ARN) to (cluster_name, region).

    Bare names rely on the caller's region (--region, AWS_REGION env, or
    profile default) - we don't enforce --region here so behavior matches
    the existing --subnet-id path. If neither side resolves, boto raises
    NoRegionError on the first call and main() surfaces it.

    ARN form encodes the region; if both an ARN region and --region are
    given and they differ, the ARN wins (more specific) and we warn.
    """
    if not value or not value.strip():
        raise ValueError("--cluster must not be empty")
    value = value.strip()
    if value.startswith("arn:"):
        # arn:aws:eks:REGION:ACCT:cluster/NAME
        parts = value.split(":")
        if len(parts) < 6 or parts[2] != "eks" or not parts[5].startswith("cluster/"):
            raise ValueError(f"not an EKS cluster ARN: {value}")
        arn_region = parts[3]
        name = parts[5].split("/", 1)[1]
        if not name:
            raise ValueError(f"EKS cluster ARN missing cluster name: {value}")
        if region_arg and region_arg != arn_region:
            print(
                f"  Warning: --region {region_arg} differs from ARN region "
                f"{arn_region}; using {arn_region}",
                file=sys.stderr,
            )
        return name, arn_region
    return value, region_arg

def get_subnet_info(ec2, subnet_id):
    subnets = ec2.describe_subnets(SubnetIds=[subnet_id]).get("Subnets") or []
    if not subnets:
        raise ValueError(f"no subnet returned for {subnet_id}")
    s = subnets[0]
    sid = s.get("SubnetId")
    if not sid:
        raise ValueError(f"DescribeSubnets returned an entry with no SubnetId for {subnet_id}")
    cidr = s.get("CidrBlock")
    if not cidr:
        # IPv6-only subnet: there is no IPv4 space to analyze. This tool
        # measures IPv4 /28 prefix-delegation fragmentation only, so skip it
        # rather than crash on the missing CidrBlock key.
        raise ValueError(
            f"{subnet_id} has no IPv4 CIDR (IPv6-only); IPv4 /28 analysis skipped"
        )
    tags = {}
    for t in s.get("Tags", []):
        key = t.get("Key")
        if key is not None:
            tags[key] = t.get("Value", "")
    return {
        "subnet_id": sid,
        "cidr": cidr,
        "az": s.get("AvailabilityZone", ""),
        "vpc_id": s.get("VpcId", ""),
        "tags": tags,
        "has_ipv6": any(
            a.get("Ipv6CidrBlockState", {}).get("State") in ("associating", "associated")
            for a in s.get("Ipv6CidrBlockAssociationSet") or []
        ),
    }


def get_enis(ec2, subnet_id):
    enis = []
    for page in ec2.get_paginator("describe_network_interfaces").paginate(
        Filters=[{"Name": "subnet-id", "Values": [subnet_id]}]
    ):
        enis.extend(page["NetworkInterfaces"])
    return enis


def get_instance_info(ec2, instance_ids):
    if not instance_ids:
        return {}
    info = {}
    ids_list = list(instance_ids)
    paginator = ec2.get_paginator("describe_instances")

    def fetch(ids):
        try:
            for page in paginator.paginate(InstanceIds=ids):
                for r in page.get("Reservations", []):
                    for inst in r.get("Instances", []):
                        iid = inst.get("InstanceId")
                        if not iid:
                            continue
                        name = next(
                            (t.get("Value") for t in inst.get("Tags", []) if t.get("Key") == "Name"),
                            None,
                        )
                        info[iid] = {
                            "name": name,
                            "state": inst.get("State", {}).get("Name", "unknown"),
                        }
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code == "InvalidInstanceID.NotFound":
                return False  # retry per-id
            print(f"  Warning: instance lookup failed ({code}): {e.response['Error'].get('Message', '')}", file=sys.stderr)
            return True
        except BotoCoreError as e:
            # Instance metadata is cosmetic; warn and skip rather than aborting
            # the whole subnet analysis on a transient network error.
            print(f"  Warning: instance metadata lookup failed: {e}", file=sys.stderr)
            return True

    for i in range(0, len(ids_list), 50):
        batch = ids_list[i : i + 50]
        # On NotFound for any ID in the batch, retry per-id so survivors resolve.
        if not fetch(batch):
            for iid in batch:
                fetch([iid])
    return info


def get_cidr_reservations(ec2, subnet_id):
    # boto3 doesn't ship a paginator for this op; iterate NextToken manually.
    reservations = []
    next_token = None
    try:
        while True:
            kw = {"SubnetId": subnet_id}
            if next_token:
                kw["NextToken"] = next_token
            resp = ec2.get_subnet_cidr_reservations(**kw)
            for r in resp.get("SubnetIpv4CidrReservations", []):
                reservations.append({
                    "cidr": r["Cidr"],
                    "type": r.get("ReservationType", "unknown"),
                    "description": r.get("Description", ""),
                    "id": r.get("SubnetCidrReservationId", ""),
                })
            next_token = resp.get("NextToken")
            if not next_token:
                break
        return reservations
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("UnauthorizedOperation", "AccessDenied"):
            print(
                f"  Warning ({subnet_id}): cannot read CIDR reservations "
                f"({code}). Block map will not show 'P' (prefix-reserved) marks. "
                f"Add ec2:GetSubnetCidrReservations to grant access.",
                file=sys.stderr,
            )
        else:
            print(
                f"  Warning ({subnet_id}): CIDR reservations lookup failed "
                f"({code}): {e.response['Error'].get('Message', '')}",
                file=sys.stderr,
            )
        return reservations
    except BotoCoreError as e:
        print(
            f"  Warning ({subnet_id}): CIDR reservations lookup failed "
            f"(ConnectionError): {e}. Block map will not show 'P' marks.",
            file=sys.stderr,
        )
        return reservations

def _client_error_code(e):
    return e.response.get("Error", {}).get("Code", "") if hasattr(e, "response") else ""


def _is_iam_denial(code):
    return code in ("AccessDenied", "AccessDeniedException", "UnauthorizedOperation")


def discover_cluster_subnets(eks, ec2, cluster_name, *, tag_scan=True):
    """Discover all subnets associated with an EKS cluster.

    Sources unioned:
      1. eks:DescribeCluster.resourcesVpcConfig.subnetIds  (control plane)
      2. eks:ListNodegroups + DescribeNodegroup.subnets    (managed node groups)
      3. eks:ListFargateProfiles + DescribeFargateProfile.subnets
      4. ec2:DescribeSubnets in the cluster VPC, one call per tag key:
           tag:kubernetes.io/cluster/<name> in (owned, shared)
           tag:karpenter.sh/discovery = <name>
           tag:kubernetes.io/role/cni = 1   (cluster-agnostic pod/CNI marker)

    DescribeCluster failure is fatal - we cannot resolve the VPC without it.
    Other steps degrade gracefully: AccessDenied or other ClientError -> warn
    and skip.

    Returns:
      dict with keys:
        cluster_name, vpc_id
        auto_mode:      bool, True when EKS Auto Mode (computeConfig.enabled)
        subnets:        {subnet_id: [source_label, ...]}
        warnings:       [str]
    """
    warnings = []
    sources = defaultdict(list)  # subnet_id -> [source_label, ...]

    # 1. Control plane / cluster VPC
    resp = eks.describe_cluster(name=cluster_name)
    cluster = resp.get("cluster")
    if not cluster:
        raise RuntimeError(f"DescribeCluster for {cluster_name!r} returned no cluster object")
    vpc_cfg = cluster.get("resourcesVpcConfig", {})
    vpc_id = vpc_cfg.get("vpcId")
    if not vpc_id:
        raise RuntimeError(f"EKS cluster {cluster_name!r} has no vpcId in resourcesVpcConfig")
    auto_mode = bool((cluster.get("computeConfig") or {}).get("enabled"))
    for sid in vpc_cfg.get("subnetIds", []) or []:
        sources[sid].append("control-plane")

    # 2. Managed node groups
    try:
        ng_names = []
        for page in eks.get_paginator("list_nodegroups").paginate(clusterName=cluster_name):
            ng_names.extend(page.get("nodegroups", []))
        for ng in ng_names:
            try:
                ng_desc = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng)["nodegroup"]
                for sid in ng_desc.get("subnets", []) or []:
                    sources[sid].append(f"nodegroup:{ng}")
            except ClientError as e:
                code = _client_error_code(e)
                warnings.append(f"DescribeNodegroup({ng}) failed ({code}); skipping")
    except ClientError as e:
        code = _client_error_code(e)
        if _is_iam_denial(code):
            warnings.append(f"ListNodegroups: {code} - skipped managed node group discovery")
        else:
            warnings.append(f"ListNodegroups failed ({code}); skipped node group discovery")

    # 3. Fargate profiles
    try:
        fg_names = []
        for page in eks.get_paginator("list_fargate_profiles").paginate(clusterName=cluster_name):
            fg_names.extend(page.get("fargateProfileNames", []))
        for fg in fg_names:
            try:
                fg_desc = eks.describe_fargate_profile(
                    clusterName=cluster_name, fargateProfileName=fg
                )["fargateProfile"]
                for sid in fg_desc.get("subnets", []) or []:
                    sources[sid].append(f"fargate:{fg}")
            except ClientError as e:
                code = _client_error_code(e)
                warnings.append(f"DescribeFargateProfile({fg}) failed ({code}); skipping")
    except ClientError as e:
        code = _client_error_code(e)
        if _is_iam_denial(code):
            warnings.append(f"ListFargateProfiles: {code} - skipped Fargate discovery")
        else:
            warnings.append(f"ListFargateProfiles failed ({code}); skipped Fargate discovery")

    # 4. Tag scan, scoped to the cluster VPC. EKS doesn't support cross-VPC
    # subnets and the kubernetes.io/cluster/<name> tag has no documented
    # effect outside the cluster VPC, so a region-wide scan would produce
    # at best stale-tag noise and at worst false positives when two clusters
    # share a name across environments.
    if tag_scan:
        # Each tag key is a separate DescribeSubnets call (EC2 ANDs filters
        # within a call, so OR across keys requires separate requests), all
        # scoped to the cluster VPC. kubernetes.io/cluster and karpenter.sh
        # are cluster-specific; kubernetes.io/role/cni is cluster-agnostic
        # (a pod/CNI subnet marker, also the EKS Auto Mode data plane).
        tag_specs = [
            ("tag:cluster", f"kubernetes.io/cluster/{cluster_name}", ["owned", "shared"]),
            ("tag:karpenter", "karpenter.sh/discovery", [cluster_name]),
            ("tag:cni-role", "kubernetes.io/role/cni", ["1"]),
        ]
        # tag_key is the bare AWS tag key; the EC2 filter Name needs a "tag:" prefix.
        for label, tag_key, values in tag_specs:
            try:
                tag_filters = [
                    {"Name": f"tag:{tag_key}", "Values": values},
                    {"Name": "vpc-id", "Values": [vpc_id]},
                ]
                for page in ec2.get_paginator("describe_subnets").paginate(Filters=tag_filters):
                    for s in page.get("Subnets", []):
                        sources[s["SubnetId"]].append(label)
            except ClientError as e:
                code = _client_error_code(e)
                if _is_iam_denial(code):
                    warnings.append(f"DescribeSubnets (tag:{tag_key}): {code} - skipped this tag")
                else:
                    warnings.append(f"DescribeSubnets (tag:{tag_key}) failed ({code}); skipped this tag")

    return {
        "cluster_name": cluster_name,
        "vpc_id": vpc_id,
        "auto_mode": auto_mode,
        "subnets": {sid: srcs for sid, srcs in sources.items()},
        "warnings": warnings,
    }


def classify_eni(eni):
    itype = eni.get("InterfaceType", "interface")
    desc = eni.get("Description", "")
    status = eni.get("Status", "")
    attachment = eni.get("Attachment", {})
    instance_id = attachment.get("InstanceId")
    requester = eni.get("RequesterId", "")

    if status == "available":
        return "orphaned", eni["NetworkInterfaceId"], "detached/unused", requester

    type_map = {
        "lambda": ("lambda", desc, "VPC Lambda"),
        "nat_gateway": ("nat_gateway", desc, "NAT Gateway"),
        "gateway_load_balancer": ("gwlb", desc, "Gateway LB"),
        "gateway_load_balancer_endpoint": ("gwlb_endpoint", desc, "Gateway LB Endpoint"),
        "load_balancer": ("elb", desc, "Load Balancer"),
        "network_load_balancer": ("nlb", desc, "Network Load Balancer"),
        "transit_gateway": ("transit_gw", desc, "Transit Gateway"),
        "vpc_endpoint": ("vpc_endpoint", desc, "VPC Endpoint"),
        "api_gateway_managed": ("api_gw", desc, "API Gateway"),
        "efs": ("efs", desc, "EFS Mount Target"),
        "trunk": ("trunk", instance_id or desc, "Trunk ENI (SGP)"),
        "branch": ("branch", instance_id or desc, "Branch ENI (SGP)"),
        "efa": ("efa", instance_id or desc, "Elastic Fabric Adapter"),
        "efa-only": ("efa", instance_id or desc, "Elastic Fabric Adapter"),
        "evs": ("evs", desc, "Elastic VMware Service"),
        "global_accelerator_managed": ("global_accel", desc, "Global Accelerator"),
        "ec2_instance_connect_endpoint": ("eice", desc, "EC2 Instance Connect Endpoint"),
        "quicksight": ("quicksight", desc, "QuickSight"),
        "iot_rules_managed": ("iot", desc, "IoT Rules"),
        "aws_codestar_connections_managed": ("codestar", desc, "CodeStar Connections"),
    }
    if itype in type_map:
        t = type_map[itype]
        return t[0], t[1], t[2], requester

    if desc.startswith("ELB ") or desc.startswith("aws-elb"):
        return "elb", desc, "Elastic Load Balancer", requester
    if desc.startswith("arn:aws:ecs:"):
        return "ecs_task", desc, "ECS Fargate task", requester
    if desc.startswith("aws-K8S-"):
        return "eks_pod", instance_id or desc, "EKS pod ENI", requester
    if desc.startswith("Amazon EKS"):
        return "eks_managed", desc, "EKS control plane", requester
    if desc.startswith("RDSNetworkInterface"):
        return "rds", desc, "RDS", requester
    if desc.startswith("ElastiCache"):
        return "elasticache", desc, "ElastiCache", requester
    if desc.startswith("RedshiftNetworkInterface"):
        return "redshift", desc, "Redshift", requester
    if desc.startswith("AWS CodeBuild"):
        return "codebuild", desc, "CodeBuild", requester
    if desc.startswith("DAX"):
        return "dax", desc, "DAX", requester
    if instance_id:
        idx = attachment.get("DeviceIndex", 0)
        kind = "ec2_primary" if idx == 0 else "ec2_secondary"
        return kind, instance_id, f"device index {idx}", requester
    return "other", desc or eni["NetworkInterfaceId"], itype, requester


def build_ip_map(enis):
    """Return {ip_str: {eni_id, owner_type, owner_id, detail, requester, is_primary}}."""
    ip_map = {}
    for eni in enis:
        owner_type, owner_id, detail, requester = classify_eni(eni)
        for addr in eni.get("PrivateIpAddresses", []):
            ip_map[addr["PrivateIpAddress"]] = {
                "eni_id": eni["NetworkInterfaceId"],
                "owner_type": owner_type,
                "owner_id": str(owner_id),
                "detail": detail,
                "requester": requester,
                "is_primary": addr.get("Primary", False),
            }
    return ip_map


def build_prefix_map(enis):
    """Return {prefix_cidr_str: {eni_id, owner_type, owner_id, detail, requester}}."""
    prefix_map = {}
    for eni in enis:
        prefixes = eni.get("Ipv4Prefixes") or []
        if not prefixes:
            continue
        owner_type, owner_id, detail, requester = classify_eni(eni)
        for pfx in prefixes:
            cidr_str = pfx.get("Ipv4Prefix", "")
            try:
                ipaddress.ip_network(cidr_str, strict=False)
            except (ValueError, TypeError):
                print(f"  Warning: skipping malformed prefix '{cidr_str}' on {eni['NetworkInterfaceId']}", file=sys.stderr)
                continue
            prefix_map[cidr_str] = {
                "eni_id": eni["NetworkInterfaceId"],
                "owner_type": owner_type,
                "owner_id": str(owner_id),
                "detail": detail,
                "requester": requester,
            }
    return prefix_map

def analyze_subnet(cidr, ip_map, cidr_reservations=None, prefix_map=None):
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except (ValueError, TypeError) as e:
        raise ValueError(f"invalid subnet CIDR {cidr!r}: {e}") from e
    # All IPs in the subnet range (not just hosts) for consistency with /28 block analysis
    all_ips = {str(ip) for ip in network}
    # AWS reserves 5 IPs per subnet: .0 (network), .1 (router), .2 (DNS),
    # .3 (future), and last IP (broadcast).
    reserved = {str(network.network_address + i) for i in range(0, 4)} | {str(network.broadcast_address)}
    used = set(ip_map.keys())

    # Build set of IPs consumed by /28 prefixes. build_prefix_map() validates
    # CIDRs upstream, but parse defensively here so a hand-built prefix_map
    # passed by a caller can't crash analysis.
    prefix_ips = set()
    prefix_blocks = set()
    if prefix_map:
        for pfx_cidr in prefix_map:
            try:
                pfx_net = ipaddress.ip_network(pfx_cidr, strict=False)
            except (ValueError, TypeError):
                print(f"  Warning: skipping malformed prefix CIDR '{pfx_cidr}'", file=sys.stderr)
                continue
            prefix_blocks.add(str(pfx_net))
            for ip in pfx_net:
                prefix_ips.add(str(ip))

    # Reserved IPs that are not also used or prefix-allocated (for clean accounting)
    effective_reserved = reserved - used - prefix_ips
    free = all_ips - used - reserved - prefix_ips

    reservation_nets = []
    if cidr_reservations:
        for r in cidr_reservations:
            try:
                reservation_nets.append(ipaddress.ip_network(r["cidr"], strict=False))
            except (ValueError, TypeError, KeyError):
                print(f"  Warning: skipping malformed CIDR reservation {r!r}", file=sys.stderr)

    blocks = list(network.subnets(new_prefix=PREFIX_SIZE)) if network.prefixlen <= PREFIX_SIZE else []
    # IPs that EC2 considers reserved and will reject for prefix allocation.
    reserved_all = {network.network_address, network.broadcast_address} | {
        network.network_address + i for i in range(1, 4)
    }
    block_analysis = []
    for block in blocks:
        # All 16 IPs in the /28 range are usable within the parent subnet.
        # block.hosts() excludes network/broadcast of the /28, but those are
        # regular IPs within the larger subnet - only the parent subnet's
        # 5 reserved IPs (.0, .1, .2, .3, broadcast) are actually reserved.
        bips = {str(ip) for ip in block}
        b_used = [ip for ip in bips if ip in used]
        b_res = [ip for ip in bips if ip in reserved and ip not in used and ip not in prefix_ips]
        b_prefix = [ip for ip in bips if ip in prefix_ips]
        b_free = [ip for ip in bips if ip in free]
        block_has_reserved = b_res or any(ip in block for ip in reserved_all)
        is_prefix_allocated = str(block) in prefix_blocks

        # Check if this block overlaps with a CIDR reservation
        in_reservation = any(block.overlaps(rnet) for rnet in reservation_nets)

        if is_prefix_allocated:
            status = "prefix_allocated"
        elif block_has_reserved:
            status = "has_reserved"
        elif not b_used:
            status = "free"
        elif not b_free:
            status = "full"
        else:
            status = "fragmented"

        block_analysis.append({
            "block": str(block),
            "status": status,
            "used": len(b_used),
            "free": len(b_free),
            "reserved": len(b_res),
            "prefix": len(b_prefix),
            "used_ips": b_used,
            "free_ips": b_free,
            "in_reservation": in_reservation,
        })

    free_blocks = sum(1 for b in block_analysis if b["status"] == "free")
    frag_blocks = sum(1 for b in block_analysis if b["status"] == "fragmented")
    full_blocks = sum(1 for b in block_analysis if b["status"] == "full")
    reserved_blocks = sum(1 for b in block_analysis if b["status"] == "has_reserved")
    prefix_allocated_blocks = sum(1 for b in block_analysis if b["status"] == "prefix_allocated")
    total = len(block_analysis)

    # Fragmentation score: of the blocks that could *ever* serve a new
    # prefix request (free + fragmented + full), what fraction is contended -
    # taken (full) or unusable due to fragmentation? Both reject prefix
    # allocation. AWS-reserved (R) and already-prefix-allocated (A) blocks
    # aren't candidates for *new* prefix requests, so they're excluded from
    # both numerator and denominator. None when no candidate blocks exist.
    #
    # Round up: a single fragmented block in a /22 subnet is 1/510 ≈ 0.2%,
    # which would round to 0% (HEALTHY) and hide a real allocation failure.
    # ceil ensures any non-zero contention reads as >=1%.
    candidate_blocks = free_blocks + frag_blocks + full_blocks
    if candidate_blocks == 0:
        fragmentation_score = None
    else:
        fragmentation_score = math.ceil((frag_blocks + full_blocks) / candidate_blocks * 100)

    return {
        "total_ips": len(all_ips),
        "used": len(used),
        "free": len(free),
        "reserved": len(effective_reserved),
        "blocks": block_analysis,
        "total_blocks": total,
        "free_blocks": free_blocks,
        "fragmented_blocks": frag_blocks,
        "full_blocks": full_blocks,
        "reserved_blocks": reserved_blocks,
        "prefix_allocated_blocks": prefix_allocated_blocks,
        "fragmentation_score": fragmentation_score,
    }

def node_recommendations(analysis, ip_map, instance_info):
    frag_blocks = [b for b in analysis["blocks"] if b["status"] == "fragmented"]
    if not frag_blocks:
        return []

    node_recoverable = defaultdict(set)
    for b in frag_blocks:
        owners = set()
        for ip in b["used_ips"]:
            info = ip_map.get(ip, {})
            oid = info.get("owner_id", "")
            if oid.startswith("i-"):
                owners.add(oid)
            else:
                owners.add(f"_undrainable_{oid}")

        drainable_owners = {o for o in owners if o.startswith("i-")}
        if drainable_owners == owners:
            for node in drainable_owners:
                node_ips_in_block = [
                    ip for ip in b["used_ips"]
                    if ip_map.get(ip, {}).get("owner_id") == node
                ]
                if len(node_ips_in_block) == len(b["used_ips"]):
                    node_recoverable[node].add(b["block"])

    recs = []
    for node_id, recoverable_blocks in sorted(
        node_recoverable.items(), key=lambda x: -len(x[1])
    ):
        inst = instance_info.get(node_id, {})
        total_ips = sum(1 for v in ip_map.values() if v["owner_id"] == node_id)
        recs.append({
            "node_id": node_id,
            "node_name": inst.get("name", node_id),
            "state": inst.get("state", "unknown"),
            "blocks_recoverable": len(recoverable_blocks),
            "block_cidrs": sorted(recoverable_blocks),
            "total_ips_held": total_ips,
        })

    return recs

def print_analysis(subnet_info, analysis, ip_map, instance_info, cidr_reservations=None, prefix_map=None):
    name = _sanitize(subnet_info["tags"].get("Name", subnet_info["subnet_id"]))
    print(f"\n{'═' * 70}")
    print(f"  Subnet: {name} ({subnet_info['subnet_id']})")
    print(f"  CIDR:   {subnet_info['cidr']}  AZ: {subnet_info['az']}")
    print(f"{'═' * 70}")

    if cidr_reservations:
        print("\n  CIDR Reservations:")
        for r in cidr_reservations:
            rtype = r["type"]
            print(f"    {r['cidr']} ({rtype}) {_sanitize(r['description'] or r['id'])}")

    print(f"\n  IPs:  {analysis['used']} used | {analysis['free']} free | "
          f"{analysis['reserved']} AWS-reserved")
    print(f"  /28 blocks: {analysis['total_blocks']} total | "
          f"{analysis['free_blocks']} free | "
          f"{analysis['fragmented_blocks']} fragmented | "
          f"{analysis['full_blocks']} full | "
          f"{analysis['reserved_blocks']} reserved | "
          f"{analysis['prefix_allocated_blocks']} prefix-allocated")

    score = analysis["fragmentation_score"]
    if score is None:
        print("  Fragmentation: N/A (no candidate blocks - all reserved or already prefix-allocated)")
    else:
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        if score == 100:
            severity = "EXHAUSTED" if analysis["fragmented_blocks"] == 0 else "CRITICAL"
        elif score >= 75:
            severity = "HIGH"
        elif score >= 50:
            severity = "MEDIUM"
        elif score >= 25:
            severity = "LOW"
        else:
            severity = "HEALTHY"
        print(f"  Fragmentation: [{bar}] {score}% ({severity})")

    # Owner summary
    owners = defaultdict(lambda: {"enis": set(), "ips": 0})
    for ip, info in ip_map.items():
        owners[info["owner_type"]]["enis"].add(info["eni_id"])
        owners[info["owner_type"]]["ips"] += 1

    print(f"\n  {'Owner Type':<20} {'ENIs':>6} {'IPs':>6}")
    print(f"  {'─' * 36}")
    for otype, data in sorted(owners.items(), key=lambda x: -x[1]["ips"]):
        print(f"  {otype.replace('_', ' '):<20} {len(data['enis']):>6} {data['ips']:>6}")

    # Block map - P marks blocks inside a CIDR reservation
    print("\n  /28 Block Map:  ■ full  ▣ fragmented  □ free  R reserved  A prefix-allocated  P prefix-reserved\n  ", end="")
    for i, b in enumerate(analysis["blocks"]):
        if b["in_reservation"] and b["status"] == "free":
            sym = "P"
        else:
            sym = {"free": "□", "full": "■", "fragmented": "▣", "has_reserved": "R", "prefix_allocated": "A"}[b["status"]]
        print(sym, end=" ")
        if (i + 1) % 16 == 0:
            print("\n  ", end="")
    print()

    # Fragmented block details
    frag = [b for b in analysis["blocks"] if b["status"] == "fragmented"]
    if frag:
        print("\n  Fragmented blocks:")
        for b in frag[:10]:
            res_tag = " [in prefix reservation]" if b["in_reservation"] else ""
            print(f"    {b['block']}: {b['used']} used, {b['free']} free{res_tag}")
            for ip in b["used_ips"][:3]:
                info = ip_map.get(ip, {})
                oid = info.get("owner_id", "?")
                if oid in instance_info:
                    oid = instance_info[oid].get("name") or oid
                req = info.get("requester", "")
                req_str = f" [requester: {_sanitize(req)}]" if req else ""
                print(f"      {ip} → {info.get('owner_type', '?')} ({_sanitize(oid)}){req_str}")
            if len(b["used_ips"]) > 3:
                print(f"      ... +{len(b['used_ips']) - 3} more")

    # Prefix-allocated blocks
    pfx = [b for b in analysis["blocks"] if b["status"] == "prefix_allocated"]
    if pfx:
        print(f"\n  Prefix-allocated blocks ({len(pfx)}):")
        for b in pfx[:10]:
            pfx_info = prefix_map.get(b["block"], {}) if prefix_map else {}
            eni_id = pfx_info.get("eni_id", "?")
            owner = pfx_info.get("owner_type", "?")
            req = pfx_info.get("requester", "")
            req_str = f" [requester: {_sanitize(req)}]" if req else ""
            print(f"    {b['block']} → {owner} ({eni_id}){req_str}")


def print_node_recs(recs):
    if not recs:
        print("\n  No single-node drain would recover a /28 block.")
        return
    print("\n  ── Node Drain Recommendations ──")
    print("  Nodes whose drain would free contiguous /28 blocks:\n")
    for r in recs[:10]:
        print(f"    {_sanitize(r['node_name'])} ({r['node_id']})")
        print(f"      State: {r['state']} | IPs held: {r['total_ips_held']} | "
              f"Blocks recoverable: {r['blocks_recoverable']}")
        for cidr in r["block_cidrs"][:5]:
            print(f"        → {cidr}")
        if len(r["block_cidrs"]) > 5:
            print(f"        ... +{len(r['block_cidrs']) - 5} more")


def print_discovery(discovered, region):
    print(f"\n{'═' * 70}")
    mode = "  [EKS Auto Mode]" if discovered.get("auto_mode") else ""
    print(f"  Cluster: {discovered['cluster_name']} ({region}){mode}")
    print(f"  VPC:     {discovered['vpc_id']}")
    print(f"{'═' * 70}")

    subnets = discovered["subnets"]
    if not subnets:
        print("\n  No subnets discovered for this cluster.")
    else:
        print(f"\n  Discovered {len(subnets)} subnet(s):")
        for sid in sorted(subnets):
            srcs = ", ".join(subnets[sid])
            print(f"    {sid}  [{srcs}]")

    if discovered["warnings"]:
        print("\n  Warnings:")
        for w in discovered["warnings"]:
            print(f"    {w}")


def print_enis(enis, ip_map, instance_info):
    if not enis:
        print("\n  No ENIs found in this subnet.")
        return

    eni_ips = defaultdict(list)
    for ip, info in ip_map.items():
        eni_ips[info["eni_id"]].append((ip, info["is_primary"]))

    print(f"\n  ── ENI Inventory ({len(enis)} ENIs) ──\n")
    print(f"  {'ENI ID':<28} {'Status':<12} {'Type':<16} {'Owner':<40} {'IPs':>4}")
    print(f"  {'─' * 104}")

    for eni in sorted(enis, key=lambda e: classify_eni(e)[0]):
        eni_id = eni["NetworkInterfaceId"]
        status = eni.get("Status", "?")
        owner_type, owner_id, detail, requester = classify_eni(eni)
        managed = eni.get("RequesterManaged", False)

        owner_display = _sanitize(str(owner_id))
        if owner_id in instance_info:
            inst = instance_info[owner_id]
            name = _sanitize(inst.get("name") or owner_id)
            state = inst.get("state", "")
            owner_display = f"{name} ({state})"

        ips = eni_ips.get(eni_id, [])
        ip_count = len(ips)
        label = owner_type.replace("_", " ")

        print(f"  {eni_id:<28} {status:<12} {label:<16} {owner_display:<40} {ip_count:>4}")

        if requester:
            managed_str = " [managed]" if managed else ""
            print(f"    requester: {_sanitize(requester)}{managed_str}")

        primary = [ip for ip, is_p in ips if is_p]
        secondary = [ip for ip, is_p in ips if not is_p]
        if primary:
            print(f"    primary:   {', '.join(primary)}")
        if secondary:
            print(f"    secondary: {', '.join(secondary[:6])}")
            if len(secondary) > 6:
                print(f"               ... +{len(secondary) - 6} more")
    print()

def main():
    _force_utf8_output()
    p = argparse.ArgumentParser(
        description="Detect subnet IP fragmentation for AWS VPC prefix delegation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --subnet-id subnet-abc123 --region us-east-1
  %(prog)s --subnet-id subnet-abc123 subnet-def456 --region us-east-1
  %(prog)s --cluster my-cluster --region us-east-1
  %(prog)s --cluster arn:aws:eks:us-east-1:123:cluster/my-cluster
  %(prog)s --cluster my-cluster --region us-east-1 --dry-run
  %(prog)s --subnet-id subnet-abc123 --region us-east-1 --list-enis --node-recs
  %(prog)s --subnet-id subnet-abc123 --region us-east-1 --json

required IAM permissions (read-only):
  ec2:DescribeSubnets
  ec2:DescribeNetworkInterfaces
  ec2:DescribeInstances
  ec2:GetSubnetCidrReservations
  # additional, only when using --cluster:
  eks:DescribeCluster
  eks:ListNodegroups
  eks:DescribeNodegroup
  eks:ListFargateProfiles
  eks:DescribeFargateProfile"""
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--subnet-id", nargs="+", help="One or more subnet IDs")
    src.add_argument("--cluster", metavar="NAME_OR_ARN",
                     help="EKS cluster name or ARN; auto-discovers subnets")
    p.add_argument("--profile", help="AWS profile")
    p.add_argument("--region", help="AWS region")
    p.add_argument("--list-enis", action="store_true", help="Show full ENI inventory with owner attribution")
    p.add_argument("--node-recs", action="store_true", help="Show node drain recommendations")
    p.add_argument("--no-tag-scan", action="store_true",
                   help="With --cluster: skip tag-based subnet discovery (EKS API only)")
    p.add_argument("--dry-run", action="store_true",
                   help="With --cluster: print discovered subnets and exit")
    p.add_argument("--json", action="store_true", help="JSON output")
    args = p.parse_args()

    # --no-tag-scan / --dry-run are no-ops without --cluster. Reject
    # explicitly so users don't silently get the wrong behavior.
    if not args.cluster and (args.no_tag_scan or args.dry_run):
        print(
            "  Error: --no-tag-scan / --dry-run require --cluster",
            file=sys.stderr,
        )
        sys.exit(2)

    # Resolve region from --cluster ARN if given, then build session.
    region = args.region
    cluster_name = None
    if args.cluster:
        try:
            cluster_name, region = parse_cluster_arg(args.cluster, args.region)
        except ValueError as e:
            print(f"  Error: {e}", file=sys.stderr)
            sys.exit(2)

    # Adaptive retry handles EC2 throttling more aggressively than the legacy
    # default - useful when scanning many subnets in a single invocation.
    try:
        session = get_session(args.profile, region)
        ec2 = session.client(
            "ec2", config=Config(retries={"max_attempts": 10, "mode": "adaptive"})
        )
    except BotoCoreError as e:
        print(f"  Error: failed to create AWS client: {e}", file=sys.stderr)
        sys.exit(2)

    discovery = None
    if args.cluster:
        try:
            eks = session.client(
                "eks", config=Config(retries={"max_attempts": 10, "mode": "adaptive"})
            )
            discovery = discover_cluster_subnets(
                eks, ec2, cluster_name,
                tag_scan=not args.no_tag_scan,
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"].get("Message", "")
            print(f"  Error: cluster discovery failed ({code}): {msg}", file=sys.stderr)
            sys.exit(2)
        except BotoCoreError as e:
            print(f"  Error: cluster discovery failed: {e}", file=sys.stderr)
            sys.exit(2)
        except RuntimeError as e:
            print(f"  Error: {e}", file=sys.stderr)
            sys.exit(2)

        if not args.json:
            print_discovery(discovery, region or "default-region")

        if args.dry_run:
            if args.json:
                print(json.dumps({"cluster": discovery}, indent=2, default=str))
            sys.exit(0)

        subnet_ids = sorted(discovery["subnets"].keys())
        if not subnet_ids:
            print(
                f"  Error: no subnets discovered for cluster {cluster_name}. "
                f"Verify cluster name, IAM permissions, or try --no-tag-scan to isolate the failure.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        subnet_ids = args.subnet_id

    json_results = []
    errors = 0

    def _record_error(subnet_id, code, message):
        nonlocal errors
        errors += 1
        print(f"  Error ({subnet_id}): {code} - {message}", file=sys.stderr)
        if args.json:
            json_results.append({"subnet_id": subnet_id, "error": code})

    for subnet_id in subnet_ids:
        try:
            subnet_info = get_subnet_info(ec2, subnet_id)
        except ClientError as e:
            _record_error(subnet_id, e.response["Error"]["Code"], e.response["Error"]["Message"])
            continue
        except BotoCoreError as e:
            _record_error(subnet_id, "ConnectionError", str(e))
            continue
        except ValueError as e:
            # get_subnet_info normalizes a malformed/unexpected DescribeSubnets
            # payload (e.g. an IPv6-only subnet with no IPv4 CIDR) into
            # ValueError. Skip this subnet; do not abort the rest of the run.
            _record_error(subnet_id, "SkippedSubnet", str(e))
            continue

        if subnet_info.get("has_ipv6"):
            print(
                f"  Warning ({subnet_id}): subnet is dual-stack (has an IPv6 CIDR). "
                f"This tool measures IPv4 /28 prefix-delegation fragmentation only; "
                f"IPv6 pod-IP consumption is not reflected.",
                file=sys.stderr,
            )

        try:
            enis = get_enis(ec2, subnet_id)
        except ClientError as e:
            _record_error(subnet_id, e.response["Error"]["Code"], e.response["Error"]["Message"])
            continue
        except BotoCoreError as e:
            _record_error(subnet_id, "ConnectionError", str(e))
            continue

        ip_map = build_ip_map(enis)
        prefix_map = build_prefix_map(enis)
        cidr_reservations = get_cidr_reservations(ec2, subnet_id)

        instance_ids = {
            v["owner_id"] for v in ip_map.values()
            if v["owner_type"] in ("ec2_primary", "ec2_secondary", "eks_pod")
            and v["owner_id"].startswith("i-")
        }
        inst_info = get_instance_info(ec2, instance_ids)
        for iid in instance_ids:
            if iid not in inst_info:
                inst_info[iid] = {"name": iid, "state": "terminated"}

        analysis = analyze_subnet(subnet_info["cidr"], ip_map, cidr_reservations, prefix_map)

        if args.json:
            out = {
                "subnet": subnet_info,
                "analysis": {k: v for k, v in analysis.items() if k != "blocks"},
                "blocks": analysis["blocks"],
                "ip_map": ip_map,
                "cidr_reservations": cidr_reservations,
            }
            if args.list_enis:
                out["enis"] = [{
                    "eni_id": e["NetworkInterfaceId"],
                    "status": e.get("Status", ""),
                    "owner_type": classify_eni(e)[0],
                    "owner_id": str(classify_eni(e)[1]),
                    "detail": classify_eni(e)[2],
                    "requester": classify_eni(e)[3],
                    "managed": e.get("RequesterManaged", False),
                    "ips": [a["PrivateIpAddress"] for a in e.get("PrivateIpAddresses", [])],
                } for e in enis]
            if args.node_recs:
                out["node_recommendations"] = node_recommendations(analysis, ip_map, inst_info)
            json_results.append(out)
            continue

        print_analysis(subnet_info, analysis, ip_map, inst_info, cidr_reservations, prefix_map)

        if args.list_enis:
            print_enis(enis, ip_map, inst_info)

        if args.node_recs:
            recs = node_recommendations(analysis, ip_map, inst_info)
            print_node_recs(recs)

    if args.json:
        # Wrap with cluster discovery context only when --cluster was used,
        # so existing --subnet-id consumers see the same shape as before.
        if discovery is not None:
            payload = {"cluster": discovery, "subnets": json_results}
            print(json.dumps(payload, indent=2, default=str))
        else:
            print(json.dumps(json_results, indent=2, default=str))
    else:
        print()

    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
