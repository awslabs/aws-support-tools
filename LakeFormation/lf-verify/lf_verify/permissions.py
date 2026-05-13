"""Lake Formation permission listing and checking."""

import botocore.exceptions

from .utils import YELLOW, RESET, retry_api_call


def _safe_catalog_id(catalog_id):
    """Only use catalog_id as top-level CatalogId if it's a plain account ID."""
    if catalog_id and ":" not in catalog_id:
        return catalog_id
    return None


def _principal_identifiers(principal):
    """Return all forms a principal might be stored as in LF grants."""
    ids = {principal}
    if not principal.startswith("arn:") and "-" in principal and principal.replace("-", "").isalnum():
        ids.add(f"arn:aws:identitystore:::user/{principal}")
        ids.add(f"arn:aws:identitystore:::group/{principal}")
    if principal.startswith("arn:aws:identitystore:::"):
        bare = principal.rsplit("/", 1)[-1]
        ids.add(bare)
    return ids


def list_all_permissions(client, resource, catalog_id=None):
    """List all permissions on a resource (no principal filter)."""
    query_resource = resource
    if "TableWithColumns" in resource:
        twc = resource["TableWithColumns"]
        tbl = {"DatabaseName": twc["DatabaseName"], "Name": twc["Name"]}
        if "CatalogId" in twc:
            tbl["CatalogId"] = twc["CatalogId"]
        query_resource = {"Table": tbl}
    params = {"Resource": query_resource, "MaxResults": 1000}
    safe_cat = _safe_catalog_id(catalog_id)
    if safe_cat:
        params["CatalogId"] = safe_cat
    results = []
    while True:
        resp = retry_api_call(client.list_permissions, **params)
        results.extend(resp.get("PrincipalResourcePermissions", []))
        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token
    return results


def list_permissions_for_principal(client, resource, principal, catalog_id=None):
    """List permissions on a resource filtered to a specific principal."""
    all_perms = list_all_permissions(client, resource, catalog_id)
    ids = _principal_identifiers(principal)
    return [p for p in all_perms if p.get("Principal", {}).get("DataLakePrincipalIdentifier") in ids]


def is_data_lake_admin(client, principal, catalog_id=None):
    """Check if the principal is a Lake Formation data lake administrator."""
    try:
        params = {}
        safe_cat = _safe_catalog_id(catalog_id)
        if safe_cat:
            params["CatalogId"] = safe_cat
        resp = retry_api_call(client.get_data_lake_settings, **params)
        admins = resp.get("DataLakeSettings", {}).get("DataLakeAdmins", [])
        return any(a.get("DataLakePrincipalIdentifier") == principal for a in admins)
    except botocore.exceptions.ClientError as e:
        if e.response.get("Error", {}).get("Code") == "AccessDeniedException":
            return False
        raise


def check_iam_allowed(client, resource, catalog_id=None):
    """Check if IAMAllowedPrincipals has access (LF not enforced)."""
    query_resource = resource
    if "TableWithColumns" in resource:
        twc = resource["TableWithColumns"]
        tbl = {"DatabaseName": twc["DatabaseName"], "Name": twc["Name"]}
        if "CatalogId" in twc:
            tbl["CatalogId"] = twc["CatalogId"]
        query_resource = {"Table": tbl}
    params = {"Resource": query_resource, "MaxResults": 1000}
    safe_cat = _safe_catalog_id(catalog_id)
    if safe_cat:
        params["CatalogId"] = safe_cat
    results = []
    while True:
        resp = retry_api_call(client.list_permissions, **params)
        for p in resp.get("PrincipalResourcePermissions", []):
            if "IAMAllowedPrincipals" in p.get("Principal", {}).get("DataLakePrincipalIdentifier", ""):
                results.append(p)
        if not resp.get("NextToken"):
            break
        params["NextToken"] = resp["NextToken"]
    return results


def list_all_tag_policy_grants(client, resource_type_filter, catalog_id=None):
    """List ALL LF-Tag policy grants for a given resource type."""
    params = {"ResourceType": resource_type_filter, "MaxResults": 1000}
    safe_cat = _safe_catalog_id(catalog_id)
    if safe_cat:
        params["CatalogId"] = safe_cat
    results = []
    while True:
        resp = retry_api_call(client.list_permissions, **params)
        for p in resp.get("PrincipalResourcePermissions", []):
            if "LFTagPolicy" in p.get("Resource", {}):
                results.append(p)
        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token
    return results


def list_principal_all_resources(client, principal=None, catalog_id=None):
    """List all LF permissions, optionally filtered to a specific principal."""
    params = {"MaxResults": 1000}
    safe_cat = _safe_catalog_id(catalog_id)
    if safe_cat:
        params["CatalogId"] = safe_cat
    results = []
    try:
        while True:
            resp = retry_api_call(client.list_permissions, **params)
            for p in resp.get("PrincipalResourcePermissions", []):
                if principal is None or p.get("Principal", {}).get("DataLakePrincipalIdentifier") == principal:
                    results.append(p)
            token = resp.get("NextToken")
            if not token:
                break
            params["NextToken"] = token
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("Throttling", "TooManyRequestsException"):
            print(f"  {YELLOW}\u26a0\ufe0f  Could not list permissions: {e}{RESET}")
        else:
            raise
    return results


def search_resources_by_lf_tags(client, expression, catalog_id=None):
    """Search databases and tables matching an LF-Tag expression."""
    safe_cat = _safe_catalog_id(catalog_id)
    params = {"Expression": expression, "MaxResults": 100}
    if safe_cat:
        params["CatalogId"] = safe_cat
    databases, tables = [], []
    p = dict(params)
    while True:
        resp = retry_api_call(client.search_databases_by_lf_tags, **p)
        databases.extend(resp.get("DatabaseList", []))
        token = resp.get("NextToken")
        if not token:
            break
        p["NextToken"] = token
    p = dict(params)
    while True:
        resp = retry_api_call(client.search_tables_by_lf_tags, **p)
        tables.extend(resp.get("TableList", []))
        token = resp.get("NextToken")
        if not token:
            break
        p["NextToken"] = token
    return databases, tables
