# DeploymentPackages

**UPDATE** Please see the blog post "[Upcoming updates to the AWS Lambda and AWS Lambda@Edge execution environment](https://aws.amazon.com/blogs/compute/upcoming-updates-to-the-aws-lambda-execution-environment/)"

*Deployment Package helpers for AWS Lambda.*

When creating deployment packages for AWS Lambda, any native binaries must be compiled to match the underlying AWS Lambda execution environment.
Please see the AWS Lambda Developer Guide section
"[Execution Environment and Available Libraries](http://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html)"
for additional details.

`NOTE`: If you have not created a KeyPair and IAM Role for EC2, first follow the following guides:
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html#working-with-iam-roles

The IAM Instance Profile Role is optional. To troubleshoot IAM Policies, attach the same policies that you 
use with your Lambda Execution Role to the IAM Instance Profile Role.

You can use the `lambda-user-data.txt` script to launch an EC2 instance locked to the correct base AMI with [aws-sam-cli](https://github.com/awslabs/aws-sam-cli). You can upload the file in the AWS Console EC2 Launch Wizard under "Advanced Details" or use the AWS CLI like this:
```bash
  aws ec2 run-instances --instance-type t2.medium \
    --region us-east-1 --image-id ami-0756fbca465a59a30 \
    --key-name $KEY --iam-instance-profile Name=$ROLE \
    --output text --query "Instances[].[InstanceId]" \
    --user-data file://lambda-user-data.txt

  # See options such as VPC subnet-id, and security-group-ids
  aws ec2 run-instances --generate-cli-skeleton
```

After a few minutes, the instance will be ready. Log in via SSH and run the Python example:
```bash
  cd examples/apps/hello-world-python3/
  echo '{"key1":"value1","key2":"value2","key3":"value3"}' > event.json
  sam local invoke -e event.json
```

You may need to download and install additional libraries or other runtimes for your use case.

For additional details about locking the Amazon Linux AMI yum repository to a specific version and executing commands on instance launch:
* https://aws.amazon.com/amazon-linux-ami/faqs/#lock
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html

## Amazon Linux AMI amzn-ami-hvm-2018.03.0.20190514-x86_64-gp2

| Region | AMI Image ID |
| :---: | --- |
| ap-northeast-1| ami-0ccdbc8c1cb7957be |
| ap-northeast-2| ami-082b5ca9ff663f3b8 |
| ap-northeast-3| ami-004176091a55d5176 |
| ap-south-1| ami-0eacc5b7915ba9921 |
| ap-southeast-1| ami-03097abf0db1cdff2 |
| ap-southeast-2| ami-05067171f4230ac41 |
| ca-central-1| ami-07ab3281411d31d04 |
| eu-central-1| ami-03a71cec707bfc3d7 |
| eu-north-1| ami-be4bc3c0 |
| eu-west-1| ami-03c242f4af81b2365 |
| eu-west-2| ami-05663d374a152d239 |
| eu-west-3| ami-0f962299dc4d90c81 |
| sa-east-1| ami-0eb2a191bf5e40e10 |
| us-east-1| ami-0756fbca465a59a30 |
| us-east-2| ami-04768381bf606e2b3 |
| us-west-1| ami-063dd30adbb186909 |
| us-west-2| ami-07a0c6e669965bb7c |
