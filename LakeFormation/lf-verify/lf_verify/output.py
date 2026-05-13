"""Output formatting: print_result, print_audit, print_what_can_access."""

from .utils import RED, GREEN, YELLOW, RESET, print_table_fmt
from .resources import describe_resource


def print_result(result):
    """Print verification result for a single principal."""
    p = result["principal"]
    has_access = result["is_admin"] or result["has_named_access"] or result["tag_access"] or result["iam_allowed_principals"]

    status = f"{GREEN}\u2705 ACCESS GRANTED{RESET}" if has_access else f"{RED}\u274c NO ACCESS{RESET}"
    print(f"\n  Principal: {p}")
    print(f"  Status:    {status}")

    if result["is_admin"]:
        print(f"  {YELLOW}\U0001f451 Data Lake Administrator \u2014 implicit full access to all resources{RESET}")

    if result["has_named_access"]:
        print(f"  {GREEN}[Named Grant]{RESET}  {', '.join(result['named_permissions'])}")

    if result["resource_tags"]:
        tags_str = ", ".join(f"{t['TagKey']}={t.get('TagValues', [])}" for t in result["resource_tags"] if isinstance(t, dict))
        print(f"  LF-Tags on resource: {tags_str}")

    if result["tag_access"]:
        for tag_label, perms in sorted(result["tag_access"].items()):
            print(f"  {GREEN}[LF-Tag Expression: {tag_label}]{RESET}  {', '.join(perms)}")
    elif result["resource_tags"] and not result["is_admin"]:
        print(f"  {RED}[LF-Tag Expression]{RESET}  No matching tag policy grants found")

    if result["iam_allowed_principals"]:
        print(f"  {YELLOW}\u26a0\ufe0f  IAMAllowedPrincipals is set \u2014 LF not enforced, IAM policies control access{RESET}")


def print_audit(principals, tag_info):
    """Print audit results showing all principals with access."""
    if not principals:
        print(f"\n{RED}No principals have access to this resource.{RESET}")
        return

    all_tags = tag_info.get("database", []) + tag_info.get("table", [])
    if all_tags:
        tags_str = ", ".join(f"{t['TagKey']}={t.get('TagValues', [])}" for t in all_tags if isinstance(t, dict))
        print(f"\nLF-Tags on resource: {tags_str}")

    print(f"\n{'='*60}")
    print(f"Principals with access ({len(principals)} found)")
    print(f"{'='*60}")

    for pid, access in sorted(principals.items()):
        is_iam_all = "IAMAllowedPrincipals" in pid
        direct = sorted(set(access["direct"])) if access["direct"] else []
        via_tags = access.get("via_tags", {})

        print(f"\n  {pid}")
        if is_iam_all:
            print(f"    {YELLOW}\u26a0\ufe0f  IAMAllowedPrincipals \u2014 LF not enforced{RESET}")
        if direct:
            print(f"    {GREEN}[Named Grant]{RESET}  {', '.join(direct)}")
        for tag_label, perms in sorted(via_tags.items()):
            print(f"    {GREEN}[LF-Tag: {tag_label}]{RESET}  {', '.join(sorted(set(perms)))}")


def print_what_can_access(principal, perms):
    """Print all resources a principal can access."""
    if not perms:
        print(f"\n  {RED}No Lake Formation permissions found for {principal}{RESET}")
        return
    print(f"\n{'='*60}")
    print(f"Resources accessible by: {principal}")
    print(f"{'='*60}")
    rows = []
    for p in perms:
        res_label = describe_resource(p.get("Resource", {}))
        grants = ", ".join(sorted(p.get("Permissions", [])))
        grantable = ", ".join(sorted(p.get("PermissionsWithGrantOption", [])))
        rows.append([res_label, grants, grantable or "\u2014"])
    print_table_fmt(["Resource", "Permissions", "Grantable"], rows)
