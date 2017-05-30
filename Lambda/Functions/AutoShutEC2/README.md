Auto Shut EC2
=============
This script will automatically shut down running AWS EC2 instances that are not tagged with the **noshut** keyword. Useful to ensure test instances don't continue running unintended. This can be deployed as an AWS Lambda function in your test AWS account and scheduled to run at specific time and frequency. The IAM role for Lambda function should allow the `ec2:StopInstances` and `ec2:DescribeInstances` actions.

**Warning**: This script is intended to be used in test environments only where keeping EC2 instances running unintended for long periods of time is not desirable. This script will **STOP** all EC2 instances in all AWS regions if the EC2 instance is not tagged with the keyword **noshut**. Please use with care.
