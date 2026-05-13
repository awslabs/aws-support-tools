"""CLI argument parsing and main entry point."""

import argparse
import json
import sys

from .utils import RED, YELLOW, GREEN, RESET, print_table_fmt, write_csv, retry_api_call
from .config import load_config
from .aws_client import get_client, validate_iam_principal
from .sso import resolve_sso_principal, list_sso_permission_set_roles, list_sso_user_groups
from .resources import build_resource, describe_resource
from .permissions import (
    _principal_identifiers,
    is_data_lake_admin,
    list_all_tag_policy_grants,
    list_principal_all_resources,
    search_resources_by_lf_tags,
)
from .checks import verify_principal, audit_resource
from .output import print_result, print_audit, print_what_can_access

__version__ = "0.1.0"


def list_tables_in_database(session, database, catalog_id=None, s3_table_bucket=None, region=None):
    """List all table names in a database using Glue API."""
    glue = session.client("glue", region_name=region) if region else session.client("glue")
    cat = f"{catalog_id}:s3tablescatalog/{s3_table_bucket}" if s3_table_bucket else catalog_id
    params = {"DatabaseName": database}
    if cat:
        params["CatalogId"] = cat
    tables = []
    while True:
        resp = retry_api_call(glue.get_tables, **params)
        tables.extend(t["Name"] for t in resp.get("TableList", []))
        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token
    return tables


def main():
    parser = argparse.ArgumentParser(description="Verify Lake Formation access for principals on a resource")
    parser.add_argument("--resource-type",
                        choices=["catalog", "s3", "database", "table", "column", "s3table", "lf-tag", "lf-tag-policy", "lf-tag-expression"])
    parser.add_argument("--database", help="Database name")
    parser.add_argument("--table", help="Table name")
    parser.add_argument("--columns", help="Comma-separated column names")
    parser.add_argument("--s3-path", help="S3 ARN for data location")
    parser.add_argument("--s3-table-bucket", help="S3 table bucket name")
    parser.add_argument("--tag-key", help="LF-Tag key")
    parser.add_argument("--tag-values", help="Comma-separated LF-Tag values")
    parser.add_argument("--expression-name", help="Named LF-Tag expression name")
    parser.add_argument("--policy-resource-type", choices=["database", "table"], default="table")
    parser.add_argument("--principal", nargs="+", help="One or more: IAM ARN, account ID, sso:user/<username>, or sso:group/<groupname>")
    parser.add_argument("--who-has-access", action="store_true", help="List all principals with access to the resource")
    parser.add_argument("--what-can-access", action="store_true", help="List all resources the principal(s) can access")
    parser.add_argument("--tag-grants-only", action="store_true", help="With --what-can-access: only show LF-Tag policy grants")
    parser.add_argument("--find-resources", action="store_true", help="Find all databases/tables matching an LF-Tag expression")
    parser.add_argument("--all-tables", action="store_true", help="Check access for all tables under the specified --database")
    parser.add_argument("--sso-instance-id", help="Identity Store ID (e.g. d-1234567890)")
    parser.add_argument("--catalog-id", help="AWS catalog/account ID")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS CLI profile")
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table", help="Output format")
    parser.add_argument("--json", action="store_true", dest="json_flag", help="(deprecated) Alias for --output json")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--debug", action="store_true", help="Show debug output")
    parser.add_argument("--wizard", action="store_true", help="Launch interactive wizard")

    config = load_config()
    if config:
        parser.set_defaults(**config)

    args = parser.parse_args()

    # Wizard mode
    if args.wizard:
        from .wizard import main as wizard_main
        wizard_main()
        return

    if args.json_flag:
        args.output = "json"

    # Validation
    if args.what_can_access:
        if not args.principal:
            parser.error("--principal required with --what-can-access")
    elif not args.resource_type:
        parser.error("--resource-type is required (unless using --what-can-access)")
    else:
        if args.resource_type in ("database", "table", "column") and not args.database:
            parser.error(f"--database required for {args.resource_type}")
        if args.resource_type in ("table", "column") and not args.table and not args.all_tables:
            parser.error(f"--table required for {args.resource_type} (or use --all-tables)")
        if args.resource_type == "s3" and not args.s3_path:
            parser.error("--s3-path required for s3")
        if args.resource_type == "s3table" and (not args.s3_table_bucket or not args.database):
            parser.error("--s3-table-bucket and --database required for s3table")
        if args.resource_type in ("lf-tag", "lf-tag-policy") and (not args.tag_key or not args.tag_values):
            parser.error("--tag-key and --tag-values required")
        if args.resource_type == "lf-tag-expression" and not args.expression_name:
            parser.error("--expression-name required for lf-tag-expression")
        if not args.principal and not args.who_has_access and not args.find_resources:
            parser.error("Provide --principal or --who-has-access")

    client, session = get_client(args)

    # Mode: what can a principal access?
    if args.what_can_access:
        _handle_what_can_access(client, session, args, parser)
        return

    # Mode: find resources matching an LF-Tag expression
    if args.find_resources:
        _handle_find_resources(client, args, parser)
        return

    resource = build_resource(args)

    if args.output == "table":
        print(f"Resource: {json.dumps(resource, indent=2)}")
        print(f"{'='*60}")

    # Mode: all tables in a database
    if args.all_tables:
        _handle_all_tables(client, session, args, resource, parser)
        return

    # Mode: who has access (audit)
    if args.who_has_access:
        _handle_who_has_access(client, args, resource)
        return

    # Mode: verify specific principals
    _handle_verify_principals(client, session, args, resource, parser)


def _handle_what_can_access(client, session, args, parser):
    if any(p.startswith("sso:") for p in args.principal) and not args.sso_instance_id:
        parser.error("--sso-instance-id is required when using sso:user/ or sso:group/ principals")

    resolved = []
    sso_user_ids = []
    for p in args.principal:
        is_sso_user = p.startswith("sso:user/")
        r = resolve_sso_principal(session, p, args.sso_instance_id) if p.startswith("sso:") else p
        if not r:
            continue
        if p != r:
            print(f"  Resolved {p} \u2192 {r}")
        exists, warning = validate_iam_principal(session, r)
        if warning:
            print(f"  {RED}\u26a0\ufe0f  {warning}{RESET}")
        if not exists:
            continue
        resolved.append(r)
        if is_sso_user:
            sso_user_ids.append(r)

    group_ids = []
    if sso_user_ids and args.sso_instance_id:
        for uid in sso_user_ids:
            groups = list_sso_user_groups(session, args.sso_instance_id, uid)
            if groups:
                print(f"\n  SSO user {uid} is a member of {len(groups)} group(s):")
                for gid, gname in groups:
                    group_arn = f"arn:aws:identitystore:::group/{gid}"
                    print(f"    - {gname} ({group_arn})")
                    if group_arn not in resolved and group_arn not in group_ids:
                        group_ids.append(group_arn)

    sso_role_arns = []
    if sso_user_ids:
        roles = list_sso_permission_set_roles(session)
        if roles:
            print(f"\n  Found {len(roles)} SSO permission set role(s) in this account:")
            for r in roles:
                print(f"    - {r}")
            sso_role_arns = roles

    all_results = {}
    principals_to_check = []
    for pid in resolved:
        if pid.startswith("arn:"):
            principals_to_check.append((pid, pid))
        else:
            user_arn = f"arn:aws:identitystore:::user/{pid}"
            principals_to_check.append((user_arn, user_arn))
    for gid in group_ids:
        principals_to_check.append((gid, f"{gid} (via group membership)"))
    for r in sso_role_arns:
        principals_to_check.append((r, f"{r} (SSO permission set role)"))

    for pid in resolved:
        if is_data_lake_admin(client, pid, args.catalog_id):
            if args.output == "table":
                print(f"\n  {pid}")
                print(f"  {YELLOW}\U0001f451 Data Lake Administrator \u2014 implicit full access to all resources{RESET}")
            all_results[pid] = "DATA_LAKE_ADMIN"

    all_perms = list_principal_all_resources(client, None, args.catalog_id)
    tag_db = list_all_tag_policy_grants(client, "LF_TAG_POLICY_DATABASE", args.catalog_id)
    tag_tbl = list_all_tag_policy_grants(client, "LF_TAG_POLICY_TABLE", args.catalog_id)
    seen = set()
    combined = []
    for p in all_perms + tag_db + tag_tbl:
        key = (p.get("Principal", {}).get("DataLakePrincipalIdentifier", ""),
               str(p.get("Resource", {})), str(sorted(p.get("Permissions", []))))
        if key not in seen:
            seen.add(key)
            combined.append(p)

    for pid, label in principals_to_check:
        if label in all_results:
            continue
        if is_data_lake_admin(client, pid, args.catalog_id):
            if args.output == "table":
                print(f"\n  {label}")
                print(f"  {YELLOW}\U0001f451 Data Lake Administrator \u2014 implicit full access to all resources{RESET}")
            all_results[label] = "DATA_LAKE_ADMIN"
            continue
        matched = [p for p in combined if p.get("Principal", {}).get("DataLakePrincipalIdentifier") == pid]
        if args.tag_grants_only:
            matched = [p for p in matched if "LFTagPolicy" in p.get("Resource", {}) or "LFTagExpression" in p.get("Resource", {})]
        all_results[label] = matched
        if args.output == "table" and matched:
            print_what_can_access(label, matched)

    any_access = any(v == "DATA_LAKE_ADMIN" or (isinstance(v, list) and v) for v in all_results.values())
    if args.output == "table" and not any_access:
        print(f"\n  {RED}No Lake Formation permissions found for any checked principal{RESET}")
    if args.output == "json":
        print(json.dumps(all_results, indent=2, default=str))
    elif args.output == "csv":
        csv_rows = []
        for label, v in all_results.items():
            if v == "DATA_LAKE_ADMIN":
                csv_rows.append([label, "ALL (implicit)", "ALL", "Yes"])
            elif isinstance(v, list):
                for p in v:
                    res_label = describe_resource(p.get("Resource", {}))
                    grants = ", ".join(sorted(p.get("Permissions", [])))
                    grantable = ", ".join(sorted(p.get("PermissionsWithGrantOption", []))) or "\u2014"
                    csv_rows.append([label, res_label, grants, grantable])
        write_csv(["Principal", "Resource", "Permissions", "Grantable"], csv_rows)


def _handle_find_resources(client, args, parser):
    if args.resource_type != "lf-tag-policy" or not args.tag_key or not args.tag_values:
        parser.error("--find-resources requires --resource-type lf-tag-policy with --tag-key and --tag-values")
    expr = [{"TagKey": args.tag_key, "TagValues": [v.strip() for v in args.tag_values.split(",")]}]
    databases, tables = search_resources_by_lf_tags(client, expr, args.catalog_id)
    if args.output == "json":
        print(json.dumps({"databases": databases, "tables": tables}, indent=2, default=str))
    else:
        rows = []
        for d in databases:
            db = d.get("Database", {})
            tags = ", ".join(f"{t['TagKey']}={t.get('TagValues', [])}" for t in d.get("LFTags", []))
            rows.append(["database", db.get("Name", "?"), "\u2014", tags])
        for t in tables:
            tbl = t.get("Table", {})
            tags = ", ".join(f"{t2['TagKey']}={t2.get('TagValues', [])}" for t2 in t.get("LFTags", []))
            rows.append(["table", tbl.get("DatabaseName", "?"), tbl.get("Name", "?"), tags])
        headers = ["Type", "Database", "Table", "LF-Tags"]
        if args.output == "csv":
            write_csv(headers, rows)
        else:
            print_table_fmt(headers, rows)


def _handle_all_tables(client, session, args, resource, parser):
    if not args.database:
        parser.error("--database required with --all-tables")
    tables = list_tables_in_database(session, args.database, args.catalog_id,
                                     getattr(args, "s3_table_bucket", None), args.region)
    print(f"Found {len(tables)} tables in {args.database}\n")
    all_rows = []
    for tbl in tables:
        rtype = "s3table" if args.resource_type == "s3table" else "table"
        if rtype == "s3table":
            cat = f"{args.catalog_id}:s3tablescatalog/{args.s3_table_bucket}" if args.catalog_id else None
            tbl_resource = {"Table": {"CatalogId": cat, "DatabaseName": args.database, "Name": tbl}} if cat else {"Table": {"DatabaseName": args.database, "Name": tbl}}
        else:
            cat = {"CatalogId": args.catalog_id} if args.catalog_id else {}
            tbl_resource = {"Table": {**cat, "DatabaseName": args.database, "Name": tbl}}

        if args.who_has_access:
            principals, tags = audit_resource(client, tbl_resource, rtype, args.catalog_id, debug=args.debug)
            for pid, access in principals.items():
                direct = sorted(set(access.get("direct", [])))
                via_tags = access.get("via_tags", {})
                if direct:
                    all_rows.append([tbl, pid, ", ".join(direct), "Named Grant"])
                for tag_label, perms in via_tags.items():
                    all_rows.append([tbl, pid, ", ".join(sorted(set(perms))), f"LF-Tag: {tag_label}"])
        elif args.principal:
            for p in args.principal:
                r = verify_principal(client, tbl_resource, p, args.catalog_id, rtype, debug=args.debug)
                if r["is_admin"]:
                    all_rows.append([tbl, p, "ALL (implicit)", "Data Lake Admin"])
                if r["has_named_access"]:
                    all_rows.append([tbl, p, ", ".join(r["named_permissions"]), "Named Grant"])
                for tag_label, perms in r.get("tag_access", {}).items():
                    all_rows.append([tbl, p, ", ".join(perms), f"LF-Tag: {tag_label}"])
                if r["iam_allowed_principals"]:
                    all_rows.append([tbl, p, "ALL (IAM)", "IAMAllowedPrincipals"])
                if not r["is_admin"] and not r["has_named_access"] and not r["tag_access"] and not r["iam_allowed_principals"]:
                    all_rows.append([tbl, p, "\u2014", "\u274c No Access"])

    headers = ["Table", "Principal", "Permissions", "Access Type"]
    if args.output == "json":
        print(json.dumps([dict(zip(headers, r)) for r in all_rows], indent=2))
    elif args.output == "csv":
        write_csv(headers, all_rows)
    else:
        print_table_fmt(headers, all_rows)


def _handle_who_has_access(client, args, resource):
    principals, tags = audit_resource(client, resource, args.resource_type, args.catalog_id, debug=args.debug)
    if args.output == "json":
        print(json.dumps({"principals": principals, "lf_tags": tags}, indent=2, default=str))
    elif args.output == "csv":
        csv_rows = []
        for pid, access in sorted(principals.items()):
            direct = sorted(set(access.get("direct", [])))
            via_tags = access.get("via_tags", {})
            if direct:
                csv_rows.append([pid, "Named Grant", ", ".join(direct)])
            for tag_label, perms in via_tags.items():
                csv_rows.append([pid, f"LF-Tag: {tag_label}", ", ".join(sorted(set(perms)))])
        write_csv(["Principal", "Access Type", "Permissions"], csv_rows)
    else:
        print_audit(principals, tags)


def _handle_verify_principals(client, session, args, resource, parser):
    if any(p.startswith("sso:") for p in args.principal) and not args.sso_instance_id:
        parser.error("--sso-instance-id is required when using sso:user/ or sso:group/ principals")

    resolved_principals = []
    for p in args.principal:
        resolved = resolve_sso_principal(session, p, args.sso_instance_id) if p.startswith("sso:") else p
        if not resolved:
            continue
        if p != resolved:
            print(f"  Resolved {p} \u2192 {resolved}")
        exists, warning = validate_iam_principal(session, resolved)
        if warning:
            print(f"  {RED}\u26a0\ufe0f  {warning}{RESET}")
        if not exists:
            continue
        resolved_principals.append(resolved)

    results = []
    for principal in resolved_principals:
        r = verify_principal(client, resource, principal, args.catalog_id, args.resource_type, debug=args.debug)
        results.append(r)

    if args.output == "json":
        print(json.dumps(results, indent=2, default=str))
    elif args.output == "csv":
        csv_rows = []
        for r in results:
            p = r["principal"]
            has_access = r["is_admin"] or r["has_named_access"] or r["tag_access"] or r["iam_allowed_principals"]
            status = "ACCESS GRANTED" if has_access else "NO ACCESS"
            if r["is_admin"]:
                csv_rows.append([p, status, "Data Lake Admin", "ALL (implicit)"])
            if r["has_named_access"]:
                csv_rows.append([p, status, "Named Grant", ", ".join(r["named_permissions"])])
            for tag_label, perms in r.get("tag_access", {}).items():
                csv_rows.append([p, status, f"LF-Tag: {tag_label}", ", ".join(perms)])
            if r["iam_allowed_principals"]:
                csv_rows.append([p, status, "IAMAllowedPrincipals", "ALL (IAM)"])
            if not has_access:
                csv_rows.append([p, status, "\u2014", "\u2014"])
        write_csv(["Principal", "Status", "Access Type", "Permissions"], csv_rows)
    else:
        for r in results:
            print_result(r)
        print()
