"""SSO principal resolution, group listing, and permission set roles."""

from .utils import RED, YELLOW, RESET


def resolve_sso_principal(session, principal, sso_instance_id):
    """Resolve a friendly SSO user/group name to an Identity Store ARN.

    Accepts:
      - sso:user/john.doe       → looks up user by UserName
      - sso:group/DataEngineers → looks up group by DisplayName
      - Anything else           → returned as-is
    """
    if not principal.startswith("sso:"):
        return principal

    ids_client = session.client("identitystore")
    kind, name = principal.split("/", 1) if "/" in principal else (principal, "")
    kind = kind.replace("sso:", "")

    if kind in ("user", "group") and "-" in name and name.replace("-", "").isalnum():
        try:
            if kind == "user":
                ids_client.describe_user(IdentityStoreId=sso_instance_id, UserId=name)
            else:
                ids_client.describe_group(IdentityStoreId=sso_instance_id, GroupId=name)
            print(f"  {YELLOW}Using bare SSO {kind} ID: {name}{RESET}")
            return name
        except Exception:
            print(f"  {RED}SSO {kind} ID '{name}' not found{RESET}")
            return None

    if kind == "user":
        resp = ids_client.list_users(
            IdentityStoreId=sso_instance_id,
            Filters=[{"AttributePath": "UserName", "AttributeValue": name}],
        )
        users = resp.get("Users", [])
        if not users:
            print(f"  {RED}SSO user '{name}' not found{RESET}")
            return None
        return users[0]["UserId"]

    if kind == "group":
        resp = ids_client.list_groups(
            IdentityStoreId=sso_instance_id,
            Filters=[{"AttributePath": "DisplayName", "AttributeValue": name}],
        )
        groups = resp.get("Groups", [])
        if not groups:
            print(f"  {RED}SSO group '{name}' not found{RESET}")
            return None
        return groups[0]["GroupId"]

    return principal


def list_sso_permission_set_roles(session):
    """List all SSO-created IAM roles in the current account."""
    iam = session.client("iam")
    roles = []
    params = {"PathPrefix": "/aws-reserved/sso.amazonaws.com/"}
    while True:
        resp = iam.list_roles(**params)
        for r in resp.get("Roles", []):
            roles.append(r["Arn"])
        if not resp.get("IsTruncated"):
            break
        params["Marker"] = resp["Marker"]
    return roles


def list_sso_user_groups(session, sso_instance_id, user_id):
    """Return list of (group_id, group_name) for groups the SSO user belongs to."""
    ids_client = session.client("identitystore")
    groups = []
    params = {"IdentityStoreId": sso_instance_id, "MemberId": {"UserId": user_id}}
    while True:
        resp = ids_client.list_group_memberships_for_member(**params)
        for m in resp.get("GroupMemberships", []):
            gid = m["GroupId"]
            try:
                g = ids_client.describe_group(IdentityStoreId=sso_instance_id, GroupId=gid)
                groups.append((gid, g.get("DisplayName", gid)))
            except Exception as e:
                print(f"  {YELLOW}\u26a0\ufe0f  Could not describe group {gid}: {e}{RESET}")
                groups.append((gid, gid))
        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token
    return groups
