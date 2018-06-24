# DeploymentPackages

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
    --region us-east-1 --image-id ami-4fffc834 \
    --key-name $KEY --iam-instance-profile Name=$ROLE \
    --output text --query "Instances[].[InstanceId]" \
    --user-data file://lambda-user-data.txt

  # See options such as VPC subnet-id, and security-group-ids
  aws ec2 run-instances --generate-cli-skeleton
```

After a few minutes, the instance will be ready. Log in via SSH and run the Python 2.7 example:
```bash
  cd examples/apps/hello-world-python/ 
  echo '{"key1":"value1","key2":"value2","key3":"value3"}' > event.json
  sam local invoke -e event.json
```

You may need to download and install additional libraries or other runtimes for your use case.

For additional details about locking the Amazon Linux AMI yum repository to a specific version and executing commands on instance launch:
* https://aws.amazon.com/amazon-linux-ami/faqs/#lock
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html

## Amazon Linux AMI amzn-ami-hvm-2017.03.1.20170812-x86_64-gp2

| Region | AMI Image ID |
| :---: | --- |
| ap-northeast-1| ami-4af5022c |
| ap-northeast-2| ami-8663bae8 |
| ap-south-1| ami-d7abd1b8 |
| ap-southeast-1| ami-fdb8229e |
| ap-southeast-2| ami-30041c53 |
| ca-central-1| ami-5ac17f3e |
| eu-central-1| ami-657bd20a |
| eu-west-1| ami-ebd02392 |
| eu-west-2| ami-489f8e2c |
| sa-east-1| ami-d27203be |
| us-east-1| ami-4fffc834 |
| us-east-2| ami-ea87a78f |
| us-west-1| ami-3a674d5a |
| us-west-2| ami-aa5ebdd2 |

