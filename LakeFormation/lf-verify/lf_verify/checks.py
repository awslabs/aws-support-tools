"""Core verification logic: verify_principal, audit_resource, tag grant matching."""

from .utils import retry_api_call
from .resources import get_resource_tags
from .permissions import (
    _principal_identifiers,
    list_all_permissions,
    list_all_tag_policy_grants,
    list_permissions_for_principal,
    is_data_lake_admin,
    check_iam_allowed,
)


def tags_match_expression(resource_tags, expression):
    """Check if a resource's tags satisfy an LF-Tag policy expression."""
    resource_tag_map = {}
    for t in resource_tags:
        if isinstance(t, dict) and "TagKey" in t:
            resource_tag_map[t["TagKey"]] = set(t.get("TagValues", []))

    for expr_tag in expression:
        key = expr_tag.get("TagKey", "")
        vals = set(expr_tag.get("TagValues", []))
        if key not in resource_tag_map:
            return False
        if not vals.intersection(resource_tag_map[key]):
            return False
    return True


def find_tag_grants_for_resource(client, resource, resource_type, catalog_id=None, principal=None, debug=False):
    """Find all LF-Tag policy grants that apply to a resource based on its tags."""
    tag_info = get_resource_tags(client, resource)
    all_tags = tag_info["database"] + tag_info["table"]

    if debug:
        print(f"\n  [DEBUG] LF-Tags on resource:")
        print(f"    Database-level: {tag_info['database']}")
        print(f"    Table-level:    {tag_info['table']}")

    if not all_tags:
        if debug:
            print(f"  [DEBUG] No LF-Tags found on resource \u2014 skipping tag expression check")
        return tag_info, []

    policy_types_to_check = set()
    if tag_info["database"]:
        policy_types_to_check.add("LF_TAG_POLICY_DATABASE")
    if tag_info["table"]:
        policy_types_to_check.add("LF_TAG_POLICY_TABLE")
    if resource_type in ("table", "column") and tag_info["database"]:
        policy_types_to_check.add("LF_TAG_POLICY_DATABASE")

    if debug:
        print(f"  [DEBUG] Querying policy types: {policy_types_to_check}")

    all_grants = []
    for ptype in policy_types_to_check:
        grants = list_all_tag_policy_grants(client, ptype, catalog_id)
        if debug:
            print(f"  [DEBUG] {ptype}: found {len(grants)} tag policy grants")
        all_grants.extend(grants)

    if debug:
        for g in all_grants:
            expr = g.get("Resource", {}).get("LFTagPolicy", {}).get("Expression", [])
            pid = g.get("Principal", {}).get("DataLakePrincipalIdentifier", "?")
            print(f"    Grant: principal={pid}, expression={expr}")

    matching = []
    for grant in all_grants:
        expr = grant.get("Resource", {}).get("LFTagPolicy", {}).get("Expression", [])
        grant_rtype = grant.get("Resource", {}).get("LFTagPolicy", {}).get("ResourceType", "")

        if grant_rtype == "DATABASE":
            tags_to_match = tag_info["database"]
        elif grant_rtype == "TABLE":
            tags_to_match = tag_info["table"] if tag_info["table"] else tag_info["database"]
        else:
            tags_to_match = all_tags

        if not tags_match_expression(tags_to_match, expr):
            continue
        if principal:
            pid = grant.get("Principal", {}).get("DataLakePrincipalIdentifier", "")
            if pid not in _principal_identifiers(principal):
                continue

        expr_label = "; ".join(f"{e['TagKey']}={e.get('TagValues', [])}" for e in expr)
        grant["_via_tag"] = f"{expr_label} ({grant_rtype})"
        matching.append(grant)

    if debug:
        print(f"  [DEBUG] Matching tag grants: {len(matching)}")

    return tag_info, matching


def audit_resource(client, resource, resource_type, catalog_id=None, debug=False):
    """Find all principals with access to a resource (direct + tag-based)."""
    direct_perms = list_all_permissions(client, resource, catalog_id)

    tag_perms = []
    tag_info = {"database": [], "table": [], "columns": []}
    if resource_type in ("database", "table", "column", "s3table"):
        tag_info, tag_perms = find_tag_grants_for_resource(client, resource, resource_type, catalog_id, debug=debug)

    principals = {}
    for p in direct_perms:
        pid = p.get("Principal", {}).get("DataLakePrincipalIdentifier", "unknown")
        principals.setdefault(pid, {"direct": [], "via_tags": {}})
        principals[pid]["direct"].extend(p.get("Permissions", []))
    for p in tag_perms:
        pid = p.get("Principal", {}).get("DataLakePrincipalIdentifier", "unknown")
        tag_label = p.get("_via_tag", "unknown")
        principals.setdefault(pid, {"direct": [], "via_tags": {}})
        principals[pid]["via_tags"].setdefault(tag_label, []).extend(p.get("Permissions", []))

    return principals, tag_info


def verify_principal(client, resource, principal, catalog_id, resource_type, debug=False):
    """Verify whether a specific principal has access to a resource."""
    result = {
        "principal": principal,
        "is_admin": False,
        "has_named_access": False,
        "named_permissions": [],
        "resource_tags": [],
        "tag_access": {},
        "iam_allowed_principals": False,
    }

    if is_data_lake_admin(client, principal, catalog_id):
        result["is_admin"] = True

    direct = list_permissions_for_principal(client, resource, principal, catalog_id)
    if direct:
        result["has_named_access"] = True
        result["named_permissions"] = sorted(set(p for d in direct for p in d.get("Permissions", [])))

    if resource_type in ("database", "table", "column", "s3table"):
        tag_info, matching_grants = find_tag_grants_for_resource(client, resource, resource_type, catalog_id, principal=principal, debug=debug)
        result["resource_tags"] = tag_info.get("database", []) + tag_info.get("table", [])
        for grant in matching_grants:
            label = grant.get("_via_tag", "unknown")
            perms = grant.get("Permissions", [])
            result["tag_access"].setdefault(label, []).extend(perms)
        for k in result["tag_access"]:
            result["tag_access"][k] = sorted(set(result["tag_access"][k]))

    if resource_type in ("database", "table", "column", "s3table"):
        if check_iam_allowed(client, resource, catalog_id):
            result["iam_allowed_principals"] = True

    return result
