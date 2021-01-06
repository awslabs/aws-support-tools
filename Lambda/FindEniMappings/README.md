# Lambda ENI Finder

This is a simple bash script that when given an ENI identifier and an AWS region will find if there are any Lambda functions currently using the specified ENI.

Requirements:
- The [jq library](https://stedolan.github.io/jq/)
- The [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
- An IAM role configured with the AWS CLI that has permissions to query Lambda and EC2/VPC/ENIs

Arguments:
- `--eni` the id of the ENI to check, __required__
- `--region` the region to search lambda for, __required__
