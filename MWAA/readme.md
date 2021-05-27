# MWAA(Amazon Managed Workflows for Apache Airflow)

## verify environment
An environment can fail to create for the following reasons [documented here](https://docs.aws.amazon.com/mwaa/latest/userguide/troubleshooting.html#t-create-environ-failed)

The `verify_env.py` script will print information support needs to debug these issues. Additionally it will perform checks along with the documented reasons on a best effort basis to help identify the failure. If encountering the error 

```
The scheduler does not appear to be running. Last heartbeat was received XXXXXX ago.

The DAGs list may not update, and new tasks will not be scheduled.
```

This script may identify why.

### Prerequisites
- Python3 is required to run this script
- boto3 1.16.25 or newer

### How to install and run
```
pip3 install boto3 --upgrade --user
git clone https://github.com/awslabs/aws-support-tools.git
python3 aws-support-tools/MWAA/verify_env/verify_env.py --envname YOUR_ENV_NAME_HERE
```

#### How can I send the output to a file automatically?

##### Use a redirection operator
python3 aws-support-tools/MWAA/verify_env/verify_env.py --envname YOUR_ENV_NAME_HERE > output.log

##### Use vscode or codium
python3 aws-support-tools/MWAA/verify_env/verify_env.py --envname YOUR_ENV_NAME_HERE | code -

### Logic and api calls
The following actions will be performed in this order:

- print out MWAA environment details to be copies to a support case
- confirm if the role's policies are valid using [IAM policy simulation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html)
- confirm that the KMS CMK has a resource policy allowing airflow's CloudWatch log groups
- confirm that the log groups were created for the environment
    - if the number of current log groups is less than the configured number, the script will check CloudTrail for the failing CreateLogGroup API call.
- confirm that the nACLs allow port 5432 ingress and egress traffic
- confirm the route tables have a route to a NAT gateway if the environment is public
- confirm if the MWAA VPC endpoints(api, ops, env) exist in the MWAA VPC
- confirm that the Amazon VPC network includes 2 private subnets that can access the Internet(if public environment) for creating containers.
- confirm the s3 bucket is blocking public access
- confirm the security groups have
  - at least 1 rule
  - an ingress rule that allows itself
- Call SSM with the document [AWSSupport-ConnectivityTroubleshooter](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-awssupport-connectivitytroubleshooter.html) to confirm connectivity between MWAA and different services
- search logs for any errors and print those to standard output

**Note: SSM automation is charged to the AWS account. For more information [please follow this link](https://aws.amazon.com/systems-manager/pricing/#Automation)**.

This script requires permission to the following API calls:
- [ec2:DescribeNetworkAcls](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkAcls.html)
- [ec2:DescribeNetworkInterfaces](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkInterfaces.html)
- [ec2:DescribeRouteTables](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html)
- [ec2:DescribeSecurityGroups](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSecurityGroups.html)
- [ec2:DescribeSubnets](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSubnets.html)
- [ec2:DescribeVpcEndpoints](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcEndpoints.html)
- [airflow:GetEnvironment](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-actions-resources.html)
- [s3:GetBucketPublicAccessBlock](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetPublicAccessBlock.html)
- [logs:DescribeLogGroups](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DescribeLogGroups.html)
- [logs:FilterLogEvents](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_FilterLogEvents.html)
- [cloudtrail:LookupEvents](https://docs.aws.amazon.com/awscloudtrail/latest/APIReference/API_LookupEvents.html)
- [ssm:StartAutomationExecution](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_StartAutomationExecution.html)
- [kms:GetKeyPolicy](https://docs.aws.amazon.com/kms/latest/APIReference/API_GetKeyPolicy.html)
- [iam:ListAttachedRolePolicies](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAttachedRolePolicies.html)
- [iam:GetPolicy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetPolicy.html)
- [iam:GetPolicyVersion](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetPolicyVersion.html)
- [iam:ListRolePolicies](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListRolePolicies.html)
- [iam:GetRolePolicy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetRolePolicy.html)
- [iam:SimulateCustomPolicy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_SimulateCustomPolicy.html)

### example usage:

`python3 verify_env.py -h`
```
usage: verify_env.py [-h] --envname ENVNAME [--region REGION]
                     [--profile PROFILE]

optional arguments:
  -h, --help         show this help message and exit
  --envname ENVNAME  name of the MWAA environment
  --region REGION    region, Ex: us-east-1
  --profile PROFILE  profile, Ex: dev
```

### example output:

`python3 verify_env.py --envname test --region us-east-1`
```
please send support the following information
If a case is not opened you may open one here https://console.aws.amazon.com/support/home#/case/create
Please make sure to NOT include any personally identifiable information in the case

AirflowConfigurationOptions :  {}
AirflowVersion :  1.10.12
Arn :  arn:aws:airflow:us-east-1:111122223333:environment/test
CreatedAt :  2021-01-01 16:47:56-05:00
DagS3Path :  dags
EnvironmentClass :  mw1.small
ExecutionRoleArn :  arn:aws:iam::111122223333:role/service-role/AmazonMWAA-test-O2gIU8
LastUpdate :  {'CreatedAt': datetime.datetime(2021, 1, 21, 10, 11, 4, tzinfo=tzlocal()), 'Status': 'SUCCESS'}
LoggingConfiguration :  {'DagProcessingLogs': {'CloudWatchLogGroupArn': 'arn:aws:logs::111122223333:log-group:airflow-test-DAGProcessing', 'Enabled': True, 'LogLevel': 'WARNING'}, 'SchedulerLogs': {'CloudWatchLogGroupArn': 'arn:aws:logs::111122223333:log-group:airflow-test-Scheduler', 'Enabled': True, 'LogLevel': 'WARNING'}, 'TaskLogs': {'CloudWatchLogGroupArn': 'arn:aws:logs::111122223333:log-group:airflow-test-Task', 'Enabled': True, 'LogLevel': 'INFO'}, 'WebserverLogs': {'CloudWatchLogGroupArn': 'arn:aws:logs::111122223333:log-group:airflow-test-WebServer', 'Enabled': True, 'LogLevel': 'WARNING'}, 'WorkerLogs': {'CloudWatchLogGroupArn': 'arn:aws:logs::111122223333:log-group:airflow-test-Worker', 'Enabled': True, 'LogLevel': 'WARNING'}}
MaxWorkers :  10
Name :  test
NetworkConfiguration :  {'SecurityGroupIds': ['sg-00f282e3f1cb821f3'], 'SubnetIds': ['subnet-0c32d5b057c851f2e', 'subnet-02752c9df247ffa0d']}
ServiceRoleArn :  arn:aws:iam::111122223333:role/aws-service-role/airflow.amazonaws.com/AWSServiceRoleForAmazonMWAA
SourceBucketArn :  arn:aws:s3:::airflow-your-bucket-mwaa
Status :  AVAILABLE
Tags :  {}
WebserverAccessMode :  PUBLIC_ONLY
WebserverUrl :  11112222-5e9d-4203-b247-c078ed1b60cf.c4.us-east-1.airflow.amazonaws.com
WeeklyMaintenanceWindowStart :  THU:15:00
VPC:  vpc-09b69221ce542334c 

### Checking the IAM role arn:aws:iam::111122223333:role/service-role/AmazonMWAA-test-123455 using iam policy simulation
Using AWS CMK
Action: airflow:PublishMetrics is allowed on resource arn:aws:airflow:us-east-1:111122223333:environment/test ✅
Action: s3:ListAllMyBuckets is blocked successfully on resource arn:aws:s3:::airflow-your-bucket-mwaa ✅
Action: s3:ListAllMyBuckets is blocked successfully on resource arn:aws:s3:::airflow-your-bucket-mwaa/ ✅
Action: s3:GetObject* is allowed on resource arn:aws:s3:::airflow-your-bucket-mwaa ✅
Action: s3:GetObject* is allowed on resource arn:aws:s3:::airflow-your-bucket-mwaa/ ✅
Action: s3:GetBucket* is allowed on resource arn:aws:s3:::airflow-your-bucket-mwaa ✅
Action: s3:GetBucket* is allowed on resource arn:aws:s3:::airflow-your-bucket-mwaa/ ✅
Action: s3:List* is allowed on resource arn:aws:s3:::airflow-your-bucket-mwaa ✅
Action: s3:List* is allowed on resource arn:aws:s3:::airflow-your-bucket-mwaa/ ✅
Action: logs:CreateLogStream is allowed on resource arn:aws:logs:us-east-1:111122223333:log-group:airflow-test-* ✅
Action: logs:CreateLogGroup is allowed on resource arn:aws:logs:us-east-1:111122223333:log-group:airflow-test-* ✅
Action: logs:PutLogEvents is allowed on resource arn:aws:logs:us-east-1:111122223333:log-group:airflow-test-* ✅
Action: logs:GetLogEvents is allowed on resource arn:aws:logs:us-east-1:111122223333:log-group:airflow-test-* ✅
Action: logs:GetLogGroupFields is allowed on resource arn:aws:logs:us-east-1:111122223333:log-group:airflow-test-* ✅
Action: logs:DescribeLogGroups is not allowed on resource *
failed with implicitDeny 🚫
Action: cloudwatch:PutMetricData is allowed on resource * ✅
Action: sqs:ChangeMessageVisibility is allowed on resource arn:aws:sqs:us-east-1:*:airflow-celery-* ✅
Action: sqs:DeleteMessage is allowed on resource arn:aws:sqs:us-east-1:*:airflow-celery-* ✅
Action: sqs:GetQueueAttributes is allowed on resource arn:aws:sqs:us-east-1:*:airflow-celery-* ✅
Action: sqs:GetQueueUrl is allowed on resource arn:aws:sqs:us-east-1:*:airflow-celery-* ✅
Action: sqs:ReceiveMessage is allowed on resource arn:aws:sqs:us-east-1:*:airflow-celery-* ✅
Action: sqs:SendMessage is allowed on resource arn:aws:sqs:us-east-1:*:airflow-celery-* ✅
Action: kms:Decrypt is allowed on resource arn:aws:kms:*:111122223333:key/* ✅
Action: kms:DescribeKey is allowed on resource arn:aws:kms:*:111122223333:key/* ✅
Action: kms:Encrypt is allowed on resource arn:aws:kms:*:111122223333:key/* ✅
Action: kms:GenerateDataKey* is allowed on resource arn:aws:kms:*:111122223333:key/* ✅
If the policy is denied you can investigate more at 
https://policysim.aws.amazon.com/home/index.jsp?#roles/AmazonMWAA-test-111123

These simulations are based off of the sample policies here 
https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json

### Checking if log groups were created successfully...

The number of log groups is less than the number of enabled suggesting an error creating 🚫
checking cloudtrail for CreateLogGroup/DeleteLogGroup requests...

if events are failing, try creating the log groups manually

### Trying to verify nACLs on subnets...
nacl: acl-1111111111111111 allows port 5432 on egress ✅
nacl: acl-1111111111111112 denied port 5432 on ingress 🚫

missing VPC endpoints, only found 🚫
### Trying to verify if route tables are valid...
Route Table:  rtb-11111111111111111 does not have a route to a NAT Gateway 🚫 

Route Table:  rtb-11111111111111112 does have a route to a NAT Gateway ✅ 

### Verifying 'block public access' is enabled on the s3 bucket...
s3 bucket arn:aws:s3:::airflow-your-bucket-mwaa blocks public access: BlockPublicAcls ✅
s3 bucket arn:aws:s3:::airflow-your-bucket-mwaa blocks public access: IgnorePublicAcls ✅
s3 bucket arn:aws:s3:::airflow-your-bucket-mwaa blocks public access: BlockPublicPolicy ✅
s3 bucket arn:aws:s3:::airflow-your-bucket-mwaa blocks public access: RestrictPublicBuckets ✅

### Trying to verifying ingress on security groups...
ingress for security group:  sg-00f282e3f1cb821f3  does allow itself ✅ 

### Testing connectivity to the following service endpoints from MWAA enis...
['sqs.us-east-1.amazonaws.com', 'ecr.us-east-1.amazonaws.com', 'monitoring.us-east-1.amazonaws.com', 'kms.us-east-1.amazonaws.com', 's3.us-east-1.amazonaws.com', 'env.airflow.us-east-1.amazonaws.com']
Testing connectivity between eni  eni-0edefdfd24bded4de  with private ip of  10.192.21.51  and  sqs.us-east-1.amazonaws.com
https://console.aws.amazon.com/systems-manager/automation/execution/a9ff7cf6-49c2-477c-88ba-2627f450d471?REGION=us-east-1

Testing connectivity between eni  eni-0edefdfd24bded4de  with private ip of  10.192.21.51  and  ecr.us-east-1.amazonaws.com
https://console.aws.amazon.com/systems-manager/automation/execution/7e5e8197-afa9-4fc0-a9cd-6dda07692334?REGION=us-east-1

no enis found for MWAA, exiting test for  monitoring.us-east-1.amazonaws.com
no enis found for MWAA, exiting test for  kms.us-east-1.amazonaws.com
no enis found for MWAA, exiting test for  s3.us-east-1.amazonaws.com
no enis found for MWAA, exiting test for  env.airflow.us-east-1.amazonaws.com

### Checking CloudWatch logs for any errors less than 1 day old
Found the following failing logs in cloudwatch:
```

### Development

#### Dependencies
The unit tests depend on the following Python modules, please install them with pip3 before proceeding:
- [pytest](https://docs.pytest.org/en/stable/usage.html#calling-pytest-through-python-m-pytest) a unit testing framework.
- [moto mock](http://docs.getmoto.org/en/latest/) a library for mocking the APIs of AWS services.

#### Unit tests
Run the unit tests using the command: `MOTO_ACCOUNT_ID=123456789123 python3 -m pytest`

Note: the account id above is used to create a "virtual" Moto account. It can be any id, but one *must* be provided.
