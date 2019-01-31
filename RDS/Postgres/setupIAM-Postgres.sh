#!/bin/bash
## Functions ##
getAccountID(){
    # This requires AWS CLI to be properly configured!
    ACC_ID="$(aws sts get-caller-identity --query "[Account]" --output text)"
    echo "Account ID: ${ACC_ID}"
    return 0
}
loadVariables() {
    read -p "Role Name [IAMDBAuthPostgresRole]: " ROLE_NAME; ROLE_NAME=${ROLE_NAME:-IAMDBAuthPostgresRole}
    read -p "Policy Name [IAMDBAuthPostgresPolicy]: " POLICY_NAME; POLICY_NAME=${POLICY_NAME:-IAMDBAuthPostgresPolicy}
    read -p "Region [us-east-1]: " REGION; REGION=${REGION:-us-east-1}
    read -p "DB Resource ID [*]: " DB_RES_ID; DB_RES_ID=${DB_RES_ID:-*}
    read -p "IAM User: " IAM_USER
    return 0
}
createJSONPolicy() {
cat << EOF > rds-iam-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": [
                "arn:aws:rds:${REGION}:${ACC_ID}:dbuser:${DB_RES_ID}/${IAM_USER}"
            ]
        }
    ]
}
EOF
POLICY_ARN="arn:aws:iam::${ACC_ID}:policy/${POLICY_NAME}"
return 0
}
createJSONRole() {
cat << EOF > rds-iam-role.json
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::${ACC_ID}:root" },
    "Action": "sts:AssumeRole"
  }
}
EOF
ROLE_ARN="arn:aws:iam::${ACC_ID}:role/${POLICY_NAME}"
return 0
}
createIAMPolicy() {
    aws iam create-policy --policy-name ${POLICY_NAME} --policy-document file://rds-iam-policy.json
    return 0
}
createIAMRole() {
    aws iam create-role --role-name ${ROLE_NAME} --assume-role-policy-document file://rds-iam-role.json
    return 0
}
attachIAMPolicyToRole(){
    aws iam attach-role-policy --policy-arn ${POLICY_ARN} --role-name ${ROLE_NAME}
    return 0
}
getSSLCertificate(){
    if [[ -f rds-combined-ca-bundle.pem ]] 
    then 
        return 0
    else 
        wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem -o /tmp/ssl.log
        if [[ $? > 0 ]]; then echo "Failed to download SSL Certificate" && exit 1; else return 0; fi
    fi
}
createParameterFile() {
if [[ -f ~/.pg_${IAM_USER} ]]; then exit 0; fi
    echo "Please provide database details to create the parameter file that will be used to generate the authentication token."
    read -p "Database Endpoint: " RDSHOST
    read -p "Database Port: [5432] " RDSPORT; RDSPORT=${RDSPORT:-5432}
    read -p "Database Name: " RDSDB
cat << EOF > ~/.pg_${IAM_USER} 
export RDSHOST="${RDSHOST}"
export RDSPORT="${RDSPORT}"
export RDSDB="${RDSDB}"
export REGION="${REGION}"
export IAM_USER="${IAM_USER}"
export CONN="psql \"host=$RDSHOST dbname=$RDSDB user=$IAM_USER sslrootcert=rds-combined-ca-bundle.pem sslmode=verify-full\""
EOF
echo "export PGPASSWORD=\"\$(aws rds generate-db-auth-token --hostname \$RDSHOST --port \$RDSPORT --region \$REGION --username \$IAM_USER)\"" >> ~/.pg_${IAM_USER}
echo "echo \$CONN" >> ~/.pg_${IAM_USER} 
return 0
}
validateSettings(){
    if [[ -z $ACC_ID ]]; then echo "Failed to get Account ID, make sure your AWS CLI is properly configured." && exit 1; fi
    if [[ -z $IAM_USER ]]; then echo "No IAM user was entered. Rerun the script and enter the IAM User." && exit 1; fi
}

## MAIN Workflow ##
getAccountID
loadVariables
createJSONPolicy
createJSONRole
validateSettings
createIAMPolicy
createIAMRole
attachIAMPolicyToRole
createParameterFile
getSSLCertificate
. ~/.pg_${IAM_USER} > /dev/null
if [[ -z $PGPASSWORD ]] 
then 
    echo "Environment configured, but token creation failed."
    echo "Try again later by running the command below:"
    echo ". ~/.pg_${IAM_USER}"
    exit 1
else
    echo ''
    echo "*** Environment configured successfully ***"
    echo ''
    echo "Please connect with the master user to your database and execute the following commands: "
    echo "create user ${IAM_USER} with login;"
    echo "grant rds_iam to ${IAM_USER};"
    echo ''
    echo "You can connect to the database now with the following connection string: "
    echo "${CONN}"
    echo ''
    echo "You can generate tokens and get the connection string at any time by running: "
    echo ". ~/.pg_${IAM_USER}"
    exit 0
fi