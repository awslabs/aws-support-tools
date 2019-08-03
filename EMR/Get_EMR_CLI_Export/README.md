# Get EMR CLI Export #

EMR provides AWS CLI export using the console.

![Image of AWS CLI export](./aws-cli-export.png)

You will then get a single line of AWS CLI to create a cluster with the same settings.

However, there is no API for command line tool. So this code is making AWS CLI for create-cluster programmatically.

## What this script does:

- At first, it works parsing the parameters from “aws cli describe-cluster”.
- And then it creates a parameter string to be appended after "aws cli create-cluster".
- Example:
```
aws emr create-cluster --auto-scaling-role EMR_AutoScaling_DefaultRole \
--applications Name=Spark Name=Hadoop Name=Hive \
--ebs-root-volume-size 10 \
--ec2-attributes ... \
--service-role EMR_DefaultRole \
--release-label emr-5.25.0 \
--name 'test-emr-2019-08-04' \
--instance-groups ... \
--scale-down-behavior TERMINATE_AT_TASK_COMPLETION \
--region ap-northeast-2
```

## Pre-requisition:

- Python: https://www.python.org/
- boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html?id=docs_gateway
- A cluster id that was already configured.

## How to use:

Run following commands `python get_emr_cli_export.py YOUR-CLUSTER-ID`

- Example:
```
python get_emr_cli_export.py j-2ABCABCABC
```

