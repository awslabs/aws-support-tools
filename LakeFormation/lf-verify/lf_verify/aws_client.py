"""AWS client creation and IAM principal validation."""

import boto3

from .utils import RED, RESET


def get_client(args):
    """Create a Lake Formation client and session from CLI args."""
    kw = {}
    if args.profile:
        kw["profile_name"] = args.profile
    if args.region:
        kw["region_name"] = args.region
    session = boto3.Session(**kw)
    return session.client("lakeformation"), session


def validate_iam_principal(session, principal):
    """Check if an IAM principal ARN exists. Returns (exists, warning_msg).
    Skips validation for cross-account ARNs.
    """
    if not principal.startswith("arn:aws:iam:"):
        return True, None
    arn_parts = principal.split(":")
    if len(arn_parts) >= 5:
        principal_account = arn_parts[4]
        try:
            caller = session.client("sts").get_caller_identity()["Account"]
            if principal_account != caller:
                return True, None
        except Exception:
            return True, None
    iam = session.client("iam")
    try:
        if ":role/" in principal:
            iam.get_role(RoleName=principal.rsplit("/", 1)[-1])
        elif ":user/" in principal:
            iam.get_user(UserName=principal.rsplit("/", 1)[-1])
        elif ":group/" in principal:
            iam.get_group(GroupName=principal.rsplit("/", 1)[-1])
        return True, None
    except iam.exceptions.NoSuchEntityException:
        return False, f"IAM principal not found: {principal}"
    except Exception as e:
        return True, f"Could not validate principal (proceeding anyway): {e}"
