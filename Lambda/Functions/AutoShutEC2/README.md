Auto Shut EC2
=============
This script will automatically shutdown running AWS EC2 instance if not tagged with **noshut** keyword. Useful to ensure test instances don't continue running unintended. This can be deployed as an AWS Lambda function in your test AWS account and scheduled to run at specific time and frequency. The IAM role for Lambda function should allow `ec2:StopInstances` action.

**Warning**: This script is intended to be used in test environments only where keeping ec2 instances running unintended for long periods of time is not desirable. This script will **STOP** all ec2 instances in all AWS regions if the name tag does not contain the keyword **noshut**. Please use with care.