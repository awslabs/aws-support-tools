# Lake Formation Troubleshooting Guide

Common Lake Formation issues and how to diagnose them with `lf-verify`.

## 1. "Access Denied" on Athena/Glue queries

**Symptom:** `ACCESS_DENIED: User does not have sufficient access to the table`

**Diagnose:**
```bash
lf-verify --resource-type table --database mydb --table mytable \
  --principal arn:aws:iam::123456789012:role/AthenaQueryRole --region us-east-1
```

**Common causes:**
- Principal missing `SELECT` grant on the table
- LF-Tag grant exists but tag not applied to the table
- Database-level grant exists but `--all-tables` not checked
- IAMAllowedPrincipals removed but no explicit grant added

## 2. Cross-account access not working

**Symptom:** External account can't query shared tables

**Diagnose:**
```bash
# Check from the data owner account
lf-verify --resource-type table --database shared_db --table shared_table \
  --principal 987654321098 --region us-east-1
```

**Common causes:**
- Grant given to account but not to specific role in that account
- RAM share not accepted
- Consumer account hasn't created resource link

## 3. Glue Crawler can't access S3 location

**Symptom:** Crawler fails with Lake Formation permission error

**Diagnose:**
```bash
lf-verify --resource-type s3 \
  --s3-path arn:aws:s3:::my-data-bucket/prefix/ \
  --principal arn:aws:iam::123456789012:role/GlueCrawlerRole --region us-east-1
```

**Common causes:**
- S3 location not registered in Lake Formation
- Role missing `DATA_LOCATION_ACCESS` grant
- S3 location registered with a different role

## 4. LF-Tags not granting expected access

**Symptom:** Tag-based policy exists but principal can't access resources

**Diagnose:**
```bash
# Check what tags are on the resource
lf-verify --resource-type table --database mydb --table mytable \
  --who-has-access --region us-east-1

# Check what the principal can access via tags
lf-verify --what-can-access \
  --principal arn:aws:iam::123456789012:role/AnalystRole \
  --tag-grants-only --region us-east-1
```

**Common causes:**
- Tag values on resource don't match the grant expression
- Grant is on `database` level but table has different tag values
- Tag not assigned to the resource (only to the grant)

## 5. IAMAllowedPrincipals — Lake Formation not enforced

**Symptom:** All IAM principals can access the table regardless of LF grants

**Diagnose:**
```bash
lf-verify --resource-type database --database mydb --who-has-access --region us-east-1
```

If you see `IAMAllowedPrincipals` in the output, Lake Formation governance is not enforced for that resource. Any IAM principal with Glue permissions can access it.

**Fix:** Remove the `IAMAllowedPrincipals` grant and add explicit grants.

## 6. SSO user/group access issues

**Symptom:** SSO user can't access resources despite being in a group with grants

**Diagnose:**
```bash
lf-verify --resource-type table --database mydb --table mytable \
  --principal sso:user/john.doe --sso-instance-id d-1234567890 --region us-east-1
```

**Common causes:**
- User not in the expected SSO group
- Grant given to SSO group ARN but with wrong format
- Identity Store ID mismatch

## 7. Column-level access issues

**Symptom:** Query works but specific columns return access denied

**Diagnose:**
```bash
lf-verify --resource-type column --database mydb --table mytable \
  --columns sensitive_col1,sensitive_col2 \
  --principal arn:aws:iam::123456789012:role/AnalystRole --region us-east-1
```

**Common causes:**
- Column inclusion filter doesn't include the column
- Column exclusion filter explicitly excludes it
- Table-level SELECT exists but column filter restricts it

## 8. Data Lake Admin not working as expected

**Diagnose:**
```bash
lf-verify --resource-type catalog \
  --principal arn:aws:iam::123456789012:role/AdminRole --region us-east-1
```

**Common causes:**
- Role is listed as admin but the ARN has a typo
- Admin was set in a different region
- Admin role exists but the user is assuming a different role
