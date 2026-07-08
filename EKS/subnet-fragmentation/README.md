# Subnet Fragmentation Analyzer

Diagnoses /28 block fragmentation in AWS VPC subnets for prefix delegation compatibility.

## Problem

EKS prefix delegation and EKS Auto Mode allocate /28 prefixes (16 contiguous IPs) to nodes. A subnet can show thousands of free IPs but fail prefix allocation with `InsufficientCidrBlocks` if those IPs are scattered across /28 blocks. Even one IP in a block makes it unusable for prefix delegation.

## How It Works

The tool queries the EC2 API (`DescribeNetworkInterfaces`) to discover every ENI and its private IPs in the subnet. It maps each IP to its /28 block, classifies every ENI by owner using the `InterfaceType` API field, detects /28 prefixes via the `Ipv4Prefixes` field, and identifies which blocks are free, fragmented, full, reserved, or prefix-allocated. All data comes directly from AWS API responses.

## Requirements

- Python 3.10+
- boto3 1.35.68+
- Read-only IAM permissions:
  - `ec2:DescribeSubnets`
  - `ec2:DescribeNetworkInterfaces`
  - `ec2:DescribeInstances`
  - `ec2:GetSubnetCidrReservations`
  - When using `--cluster` (EKS auto-discovery):
    - `eks:DescribeCluster`
    - `eks:ListNodegroups`
    - `eks:DescribeNodegroup`
    - `eks:ListFargateProfiles`
    - `eks:DescribeFargateProfile`

## Install

Requires Python 3.10+. From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install "boto3>=1.35.68"
python subnet_frag.py --help
```

## Usage

```bash
python3 subnet_frag.py --cluster my-cluster --region us-east-1
python3 subnet_frag.py --subnet-id subnet-abc123 subnet-def456 --region us-east-1
python3 subnet_frag.py --subnet-id subnet-abc123 --region us-east-1 --list-enis --node-recs
```

`--subnet-id` and `--cluster` are mutually exclusive: pass one or the other.

| Flag | Description |
|------|-------------|
| `--subnet-id` | One or more subnet IDs |
| `--cluster` | EKS cluster name or ARN; auto-discovers subnets from the EKS API and tags |
| `--region` | AWS region (extracted from ARN when `--cluster` is an ARN) |
| `--profile` | AWS CLI profile |
| `--list-enis` | Full ENI inventory with owner attribution |
| `--node-recs` | Node drain recommendations ranked by recoverable blocks |
| `--no-tag-scan` | With `--cluster`: skip tag-based discovery (EKS API only) |
| `--dry-run` | With `--cluster`: print discovered subnets and exit |
| `--json` | Structured JSON output |

### Cluster auto-discovery

Passing `--cluster` (a name or an EKS cluster ARN) unions four sources to find every subnet associated with an EKS cluster, then analyzes each. Each discovered subnet is labeled with the source(s) it was found in (`control-plane`, `nodegroup:<name>`, `fargate:<name>`, `tag:cluster`, `tag:karpenter`, `tag:cni-role`); a subnet found in multiple sources keeps all labels.

1. `eks:DescribeCluster` -> control plane subnets (defines the cluster VPC; also detects EKS Auto Mode)
2. `eks:ListNodegroups` + `DescribeNodegroup` -> managed node group subnets
3. `eks:ListFargateProfiles` + `DescribeFargateProfile` -> Fargate profile subnets
4. `ec2:DescribeSubnets` in the cluster VPC, one call per tag (see Discovery tags below)

Sources 2-4 degrade independently: if one is denied or fails, discovery warns and continues with the rest (only `DescribeCluster` is fatal). `--no-tag-scan` skips source 4; `--dry-run` prints the discovered subnets and exits.

#### Discovery tags

The tag scan runs one `ec2:DescribeSubnets` call per tag key, each filtered by `vpc-id = <cluster VPC>` AND the tag:

| Tag | Value matched | Meaning | Cluster-specific | Source label |
|-----|---------------|---------|------------------|--------------|
| `kubernetes.io/cluster/<cluster-name>` | `owned` or `shared` | Canonical EKS subnet tag | Yes (name is in the key) | `tag:cluster` |
| `karpenter.sh/discovery` | `<cluster-name>` | Karpenter subnet discovery convention | Yes (value is the cluster name) | `tag:karpenter` |
| `kubernetes.io/role/cni` | `1` | Pod / VPC CNI custom-networking subnets (also the EKS Auto Mode data plane) | No (cluster-agnostic) | `tag:cni-role` |

`kubernetes.io/role/elb` and `kubernetes.io/role/internal-elb` are intentionally not used: they mark load-balancer subnets, not pod IP space.

For **EKS Auto Mode** clusters there are no managed node groups or Fargate profiles, so the data plane is found via the tag scan; the discovery header shows `[EKS Auto Mode]`.

#### Over-reporting in a shared VPC

Discovery favors recall: it would rather include a subnet than miss a data-plane subnet. Two of the three tags are tied to the cluster identity, but `kubernetes.io/role/cni=1` is cluster-agnostic (it only marks "pod subnet"), scoped only by VPC. When several clusters share one VPC, discovery for cluster A can pick up a `role/cni` subnet that belongs to cluster B. Such a subnet is still included, and you can spot it from its source labels: a subnet whose only source is `tag:cni-role` was matched solely by the agnostic tag and is not otherwise confirmed as belonging to this cluster.

## Output

### Fragmentation Analysis

```
══════════════════════════════════════════════════════════════════════
  Subnet: example-eks-pods (subnet-0abc123def)
  CIDR:   10.0.0.0/22  AZ: us-east-1a
══════════════════════════════════════════════════════════════════════

  IPs:  78 used | 845 free | 5 AWS-reserved
  /28 blocks: 64 total | 44 free | 8 fragmented | 4 full | 2 reserved | 6 prefix-allocated
  Fragmentation: [████░░░░░░░░░░░░░░░░] 21% (HEALTHY)

  Owner Type             ENIs    IPs
  ────────────────────────────────────
  eks pod                   8     52
  ec2 primary               6      6
  lambda                    4      4
  elb                       2      8
  rds                       2      4
  nat gateway               1      1
  vpc endpoint              2      3

  /28 Block Map:  ■ full  ▣ fragmented  □ free  R reserved  A prefix-allocated  P prefix-reserved
  R □ □ □ ▣ □ □ □ □ □ ▣ □ □ □ □ □
  □ □ ▣ □ □ □ A A A □ □ ■ □ ▣ □ □
  □ ▣ □ □ □ □ A A A □ ▣ □ □ □ ■ □
  □ □ □ ▣ □ □ □ ■ □ □ □ ▣ ■ □ □ R
```

Each square is one /28 block (16 IPs).

### Fragmentation Score

The headline percentage answers one question: *of the blocks that could serve a new prefix-delegation request right now, what fraction would fail?*

```
fragmentation_score = ceil((fragmented + full) / (free + fragmented + full) * 100)
```

A `fragmented` block fails because it has scattered IPs in use; a `full` block fails because every IP is taken. From a prefix-delegation standpoint both are equally fatal - only `free` blocks can satisfy a prefix request. AWS-reserved (`R`) and already-prefix-allocated (`A`) blocks are excluded from numerator and denominator since neither is a candidate for a *new* allocation.


| Score | Severity | Meaning |
|------|----------|---------|
| 0-24% | HEALTHY | Plenty of free blocks; prefix delegation reliable |
| 25-49% | LOW | Free blocks exist but fragmentation is creeping in |
| 50-74% | MEDIUM | Roughly half of candidate blocks are unusable |
| 75-99% | HIGH | Few free blocks remain |
| 100% (with fragmentation) | CRITICAL | Every candidate block is fragmented or full - drain or migrate |
| 100% (no fragmentation) | EXHAUSTED | Subnet is fully consumed; add capacity |
| N/A | - | No candidate blocks at all (every block AWS-reserved or prefix-allocated) |

### ENI Inventory

```
$ python3 subnet_frag.py --subnet-id subnet-abc123 --region us-east-1 --list-enis

  ── ENI Inventory (20 ENIs) ──

  ENI ID                       Status       Type             Owner                                     IPs
  ────────────────────────────────────────────────────────────────────────────────────────────────────────
  eni-0a1b2c3d4e5f60001        in-use       eks managed      Amazon EKS example-cluster                  1
    primary:   10.0.0.45
  eni-0a1b2c3d4e5f60008        in-use       lambda           AWS Lambda VPC ENI-example-function         1
    primary:   10.0.0.120
  eni-0a1b2c3d4e5f60015        available    orphaned         eni-0a1b2c3d4e5f60015                       1
    primary:   10.0.0.200
```

### Node Drain Recommendations

```
$ python3 subnet_frag.py --subnet-id subnet-abc123 --region us-east-1 --node-recs

  ── Node Drain Recommendations ──

    example-node-1 (i-0node1aaa)
      State: running | IPs held: 7 | Blocks recoverable: 6
        → 10.0.0.64/28
        → 10.0.0.96/28
        → 10.0.0.128/28
```

Nodes ranked by how many /28 blocks would be fully recovered if drained. Only recommends where a single node owns all IPs in a fragmented block.

> Warning: draining a node evicts and reschedules the pods running on it, which interrupts those workloads. Treat these as candidates only: cordon and drain during a maintenance window, after confirming the pods can reschedule elsewhere.

### Prefix-Allocated Blocks

When prefix delegation is active, the tool detects /28 prefixes assigned to ENIs and marks them `A` in the block map:

```
  Prefix-allocated blocks (3):
    10.0.0.32/28  → eks_pod (eni-0a1b2c3d4e5f60002)
    10.0.0.96/28  → eks_pod (eni-0a1b2c3d4e5f60002)
    10.0.0.176/28 → eks_pod (eni-0a1b2c3d4e5f60003)
```

The free IP count accounts for prefix-allocated IPs and matches the `AvailableIpAddressCount` reported by `DescribeSubnets`.

## Block Map Legend

| Symbol | Meaning |
|--------|---------|
| `□` | Free - all 16 IPs are available and the block can satisfy a prefix allocation request |
| `▣` | Fragmented - at least one IP is in use, making the entire block unusable for prefix delegation |
| `■` | Full - all 16 IPs are occupied |
| `R` | Reserved - overlaps with AWS-reserved IPs at the start or end of the subnet |
| `A` | Prefix-allocated - already assigned as a /28 prefix to an ENI via prefix delegation |
| `P` | Prefix-reserved - falls within a CIDR reservation designated for prefix delegation |

## Limitations

- IPv4 only. The tool analyzes IPv4 /28 prefix-delegation fragmentation. For a dual-stack subnet it emits a warning and reports IPv4 only; IPv6 pod-IP consumption is not measured. IPv6-only subnets are skipped with a notice.
