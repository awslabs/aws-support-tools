# DeploymentPackages

When creating deployment packages for AWS Lambda, any native binaries must be compiled to match the underlying AWS Lambda execution environment.
Please see the AWS Lambda Developer Guide section
"[Execution Environment and Available Libraries](http://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html)"
for additional details.

You can launch an EC2 instance locked to the correct AMI with [aws-sam-cli](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) to build and test.

*Requirements*

`NOTE`: If you have not created a KeyPair and IAM Role for EC2, first follow the following guides:
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html#working-with-iam-roles

The IAM Instance Profile Role is optional. To troubleshoot IAM Policies, attach the same policies that you 
use with your Lambda Execution Role to the IAM Instance Profile Role.

*Deployment Package helpers for AWS Lambda*

You can use the `lambda-user-data.txt` script by uploading the file in the "Advanced Details" of the [AWS Console EC2 Launch Wizard](https://console.aws.amazon.com/ec2/v2/home#Images:visibility=public-images;search=amzn-ami-hvm-2018.03.0.20181129-x86_64-gp2) or use the AWS CLI like this:
```bash
  aws ec2 run-instances --instance-type t3.medium \
    --region us-east-1 --image-id ami-0080e4c5bc078760e \
    --key-name $KEY --iam-instance-profile Name=$ROLE \
    --output text --query "Instances[].[InstanceId]" \
    --user-data file://lambda-user-data.txt

  # See options such as VPC subnet-id, and security-group-ids
  aws ec2 run-instances --generate-cli-skeleton
```

After a few minutes, the instance will be ready. Log in via SSH and run the Python example:
```bash
  cd $HOME/serverless-app-examples/python/hello-world-python3
  echo '{"key1":"value1","key2":"value2","key3":"value3"}' > event.json
  sam local invoke -e event.json
```

You may need to download and install additional libraries or other runtimes for your use case.

For additional details about locking the Amazon Linux AMI yum repository to a specific version and executing commands on instance launch:
* https://aws.amazon.com/amazon-linux-ami/faqs/#lock
* http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html

## Amazon Linux AMI amzn-ami-hvm-2018.03.0.20181129-x86_64-gp2

| Region | AMI Image ID |
| :---: | --- |
| ap-northeast-1| ami-00a5245b4816c38e6 |
| ap-northeast-2| ami-00dc207f8ba6dc919 |
| ap-northeast-3| ami-0b65f69a5c11f3522 |
| ap-south-1| ami-0ad42f4f66f6c1cc9 |
| ap-southeast-1| ami-05b3bcf7f311194b3 |
| ap-southeast-2| ami-02fd0b06f06d93dfc |
| ca-central-1| ami-07423fb63ea0a0930 |
| eu-central-1| ami-0cfbf4f6db41068ac |
| eu-north-1| ami-86fe70f8 |
| eu-west-1| ami-08935252a36e25f85 |
| eu-west-2| ami-01419b804382064e4 |
| eu-west-3| ami-0dd7e7ed60da8fb83 |
| sa-east-1| ami-05145e0b28ad8e0b2 |
| us-east-1| ami-0080e4c5bc078760e |
| us-east-2| ami-0cd3dfa4e37921605 |
| us-west-1| ami-0ec6517f6edbf8044 |
| us-west-2| ami-01e24be29428c15b2 |
