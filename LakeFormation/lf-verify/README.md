# lf-verify

**Verify and troubleshoot AWS Lake Formation access permissions from the command line.**

`lf-verify` checks whether specific AWS principals (IAM roles, users, SSO groups) have access to Lake Formation resources — databases, tables, columns, S3 locations, and LF-Tag policies. It detects direct grants, LF-Tag-based access, data lake admin status, and IAMAllowedPrincipals.

## Installation

```bash
pip install lf-verify
```

Optional — for config file support:
```bash
pip install lf-verify[yaml]
```

## Quick Start

```bash
# Check if a role can access a database
lf-verify --resource-type database --database my_database \
  --principal arn:aws:iam::123456789012:role/GlueRole --region us-east-1

# Who has access to a table?
lf-verify --resource-type table --database my_database --table my_table \
  --who-has-access --region us-east-1

# What can a principal access?
lf-verify --what-can-access \
  --principal arn:aws:iam::123456789012:role/AnalystRole --region us-east-1

# Find all resources tagged with environment=production
lf-verify --resource-type lf-tag-policy --tag-key environment --tag-values production \
  --find-resources --region us-east-1

# Interactive wizard mode
lf-verify --wizard
```

## Troubleshooting Common Issues

### Access Denied on Glue/Athena queries

```bash
# Check if the role has SELECT on the table
lf-verify --resource-type table --database mydb --table mytable \
  --principal arn:aws:iam::123456789012:role/GlueJobRole --region us-east-1
```

### Cross-account access issues

```bash
# Check if an external account has been granted access
lf-verify --resource-type database --database shared_db \
  --principal 987654321098 --region us-east-1
```

### LF-Tag based access not working

```bash
# Verify tag grants for a principal
lf-verify --what-can-access \
  --principal arn:aws:iam::123456789012:role/AnalystRole \
  --tag-grants-only --region us-east-1
```

### IAMAllowedPrincipals warnings

```bash
# Audit a database for IAMAllowedPrincipals (indicates LF not enforced)
lf-verify --resource-type database --database mydb --who-has-access --region us-east-1
```

## Features

- **Verify access** — check if a principal has access to a specific resource
- **Audit mode** (`--who-has-access`) — list all principals with access to a resource
- **Discovery mode** (`--what-can-access`) — list all resources a principal can access
- **Resource search** (`--find-resources`) — find databases/tables matching an LF-Tag expression
- **Interactive wizard** (`--wizard`) — guided troubleshooting flow
- **SSO support** — resolve `sso:user/name` and `sso:group/name`, auto-discover group memberships
- **LF-Tag awareness** — detects access granted through tag-based policies
- **S3 Tables support** — works with S3 table buckets and namespaces
- **Multiple output formats** — table (default), JSON, or CSV
- **Rate limiting** — automatic retry with exponential backoff for large catalogs
- **Config file** — `.lf-verify.yaml` for shared defaults

## Output Formats

```bash
# Formatted table (default)
lf-verify --resource-type database --database mydb --who-has-access

# JSON
lf-verify --resource-type database --database mydb --who-has-access --output json

# CSV (for spreadsheets / security reports)
lf-verify --resource-type database --database mydb --who-has-access --output csv > report.csv
```

## Supported Resource Types

| Type | Description | Example |
|------|-------------|---------|
| `database` | Glue database | `--database mydb` |
| `table` | Glue table | `--database mydb --table mytable` |
| `column` | Table columns | `--database mydb --table mytable --columns col1,col2` |
| `s3` | S3 data location | `--s3-path arn:aws:s3:::bucket/prefix/` |
| `s3table` | S3 Tables | `--s3-table-bucket mybucket --database namespace` |
| `catalog` | Glue catalog | *(no extra args)* |
| `lf-tag` | LF-Tag | `--tag-key env --tag-values prod` |
| `lf-tag-policy` | LF-Tag policy | `--tag-key env --tag-values prod --policy-resource-type table` |
| `lf-tag-expression` | Named expression | `--expression-name MyExpression` |

## Principal Formats

```bash
# IAM
arn:aws:iam::123456789012:role/MyRole
arn:aws:iam::123456789012:user/MyUser

# Cross-account
123456789012

# SSO (requires --sso-instance-id)
sso:user/john.doe
sso:group/DataEngineers

# Multiple principals
--principal arn:aws:iam::123456789012:role/RoleA sso:group/DataEngineers
```

## Configuration File

Create `.lf-verify.yaml` in your project or home directory:

```yaml
region: us-east-1
profile: prod
catalog_id: "123456789012"
sso_instance_id: d-1234567890
```

CLI arguments override config file values.

## IAM Permissions Required

The tool is **fully read-only**. Minimum permissions needed:

| Service | Actions |
|---------|---------|
| Lake Formation | `ListPermissions`, `GetDataLakeSettings`, `GetResourceLFTags`, `SearchDatabasesByLFTags`, `SearchTablesByLFTags` |
| Glue | `GetTables`, `GetDatabases` |
| STS | `GetCallerIdentity` |
| IAM *(optional)* | `GetRole`, `GetUser`, `GetGroup`, `ListRoles` |
| Identity Store *(optional)* | `ListUsers`, `ListGroups`, `DescribeUser`, `DescribeGroup`, `ListGroupMembershipsForMember` |

A ready-to-use IAM policy template is included: [`iam-policy-template.json`](iam-policy-template.json).

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT
