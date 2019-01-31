# Setup IAM Authentication for RDS / Aurora Postgresql

## Pre-requisites:
AWS CLI must be installed and configured properly. User/profile configured with AWS CLI must be able to create IAM resources.

## Limitations:
* EC2 Roles currently not supported.
* Tested on version 10.6 only, should work with 9.6.11 or higher, and 9.5.15 or higher. [Documentation here](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html#UsingWithRDS.IAMDBAuth.Availability)

## Usage:
Step 1: Go to RDS Console, select the instance, click on "Modify", "Enable IAM Authentication", "Next", "Apply immediately".

Step 2: Open up a terminal and run the command below and follow the instructions.
```
curl -L https://raw.githubusercontent.com/awslabs/aws-support-tools/master/RDS/Postgres/setupIAM-Postgres.sh > /tmp/setupIAM-Postgres.sh && \
chmod +x /tmp/setupIAM-Postgres.sh && /tmp/setupIAM-Postgres.sh
```
Step 3: Connect to the database using your master user, create the database user and grant the rds_iam role:
```
iamdemo=> create user <USER> with login;
CREATE ROLE
iamdemo=> grant rds_iam to <USER>;
GRANT ROLE
iamdemo=> \q
```
Step 4: Use the script created under the home directory to generate the authentication token and connection string
```
$ . ~/.pg_<USER>
```
Example:
```
$ . ~/.pg_bruno 
psql "host=postgres-13279.c3zv6fovsjeu.ap-southeast-2.rds.amazonaws.com dbname=IAMDB user=bruno sslrootcert=rds-combined-ca-bundle.pem sslmode=verify-full"
```