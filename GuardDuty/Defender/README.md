# GuardDuty Defender

This project provides an example Lambda function to action GuardDuty findings.

Included is a Cloudformation template to deploy the Lambda function and associated CloudWatch event rule.

### How it Works

The Lambda function is invoked when new GuardDuty findings are generated. When a GuardDuty finding indicates an EC2 instance is the ACTOR for a High severity finding, all existing security groups will be removed from the instance and a restricted security group is assigned. This retains the running state of the instance for forensics while mitigating the risk it poses.

The restricted security group will be automatically created, and all ingress and egress traffic will be denied.

The template also creates an SNS topic that you can subscribe to for email notifications when any action is taken.

### Cloudformation Template Parameters
|Parameter|Purpose|
|---------|-------|
|Role|ARN of the IAM role that provides Lambda execution access|

### Permissions

The role used by Defender requires the following IAM permissions:
- logs:CreateLogStream
- logs:PutLogEvents
- ec2:Describe*
- ec2:AuthorizeSecurityGroupEgress
- ec2:AuthorizeSecurityGroupIngress
- ec2:CreateSecurityGroup
- ec2:RevokeSecurityGroupEgress
- ec2:RevokeSecurityGroupIngress
- ec2:ModifyNetworkInterfaceAttribute
- sns:Publish

### Deploy
The Cloudformation template references the local source directory and can be deployed using aws cloudformation package command.

Example commands to package and deploy the template:

```
aws cloudformation package \
    --template-file stack.yaml \
    --s3-bucket my-lambda-code-bucket \
    --output-template-file deploy.yaml

aws cloudformation deploy \
    --template-file deploy.yaml \
    --stack-name guardduty-defender \
    --parameter-overrides \
    Role=arn:aws:iam::xxxxxxxxxxxx:role/lambda_execution_role
```

To simplify deployment you can use deploy.sh, a wrapper script around aws cloudformation cli tool.
