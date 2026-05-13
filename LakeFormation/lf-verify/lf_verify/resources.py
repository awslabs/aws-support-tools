"""Resource building, description, and tag retrieval."""

import sys

from .utils import YELLOW, RESET, retry_api_call


def build_resource(args):
    """Build a Lake Formation resource dict from CLI args."""
    cat = {"CatalogId": args.catalog_id} if args.catalog_id else {}

    if args.resource_type == "catalog":
        cat_id = args.catalog_id if args.catalog_id else None
        return {"Catalog": {"Id": cat_id}} if cat_id else {"Catalog": {}}

    if args.resource_type == "s3":
        return {"DataLocation": {**cat, "ResourceArn": args.s3_path}}

    if args.resource_type == "database":
        return {"Database": {**cat, "Name": args.database}}

    if args.resource_type == "table":
        return {"Table": {**cat, "DatabaseName": args.database, "Name": args.table or "__ALL_TABLES__"}}

    if args.resource_type == "column":
        r = {**cat, "DatabaseName": args.database, "Name": args.table}
        if args.columns:
            r["ColumnNames"] = [c.strip() for c in args.columns.split(",")]
        return {"TableWithColumns": r}

    if args.resource_type == "s3table":
        s3t_catalog = f"{args.catalog_id}:s3tablescatalog/{args.s3_table_bucket}" if args.catalog_id else args.s3_table_bucket
        if args.table:
            return {"Table": {"CatalogId": s3t_catalog, "DatabaseName": args.database, "Name": args.table}}
        return {"Database": {"CatalogId": s3t_catalog, "Name": args.database}}

    if args.resource_type == "lf-tag":
        return {"LFTag": {**cat, "TagKey": args.tag_key, "TagValues": [v.strip() for v in args.tag_values.split(",")]}}

    if args.resource_type == "lf-tag-policy":
        expr = [{"TagKey": args.tag_key, "TagValues": [v.strip() for v in args.tag_values.split(",")]}]
        return {"LFTagPolicy": {**cat, "ResourceType": args.policy_resource_type.upper(), "Expression": expr}}

    if args.resource_type == "lf-tag-expression":
        return {"LFTagExpression": {**cat, "Name": args.expression_name}}

    sys.exit(f"Unknown resource type: {args.resource_type}")


def describe_resource(res):
    """Return a short human-readable label for a LF resource dict."""
    if "Database" in res:
        return f"database: {res['Database'].get('Name', '?')}"
    if "Table" in res:
        t = res["Table"]
        return f"table: {t.get('DatabaseName', '?')}.{t.get('Name', '?')}"
    if "TableWithColumns" in res:
        t = res["TableWithColumns"]
        cols = t.get("ColumnNames", ["*"])
        return f"columns: {t.get('DatabaseName', '?')}.{t.get('Name', '?')} ({', '.join(cols)})"
    if "DataLocation" in res:
        return f"s3: {res['DataLocation'].get('ResourceArn', '?')}"
    if "LFTag" in res:
        tag = res["LFTag"]
        return f"lf-tag: {tag.get('TagKey', '?')}={tag.get('TagValues', [])}"
    if "LFTagPolicy" in res:
        p = res["LFTagPolicy"]
        expr = "; ".join(f"{e['TagKey']}={e.get('TagValues', [])}" for e in p.get("Expression", []))
        return f"lf-tag-policy ({p.get('ResourceType', '?')}): {expr}"
    if "Catalog" in res:
        return "catalog"
    return str(res)


def get_resource_tags(client, resource):
    """Get LF-Tags attached to a resource, separated by level."""
    kwargs = {}
    if "Database" in resource:
        kwargs["Resource"] = {"Database": resource["Database"]}
    elif "Table" in resource:
        kwargs["Resource"] = {"Table": resource["Table"]}
    elif "TableWithColumns" in resource:
        tbl = {"DatabaseName": resource["TableWithColumns"]["DatabaseName"], "Name": resource["TableWithColumns"]["Name"]}
        if resource["TableWithColumns"].get("CatalogId"):
            tbl["CatalogId"] = resource["TableWithColumns"]["CatalogId"]
        kwargs["Resource"] = {"Table": tbl}
    else:
        return {"database": [], "table": [], "columns": []}
    try:
        resp = retry_api_call(client.get_resource_lf_tags, **kwargs)
        return {
            "database": resp.get("LFTagOnDatabase", []),
            "table": resp.get("LFTagsOnTable", []),
            "columns": resp.get("LFTagsOnColumns", []),
        }
    except Exception as e:
        print(f"  {YELLOW}Note: Could not retrieve LF-Tags ({type(e).__name__}): {e}{RESET}")
        return {"database": [], "table": [], "columns": []}
