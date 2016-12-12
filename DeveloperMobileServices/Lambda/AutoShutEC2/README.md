Auto Shut EC2
=============
This script will automatically shutdown running AWS EC2 instance if not tagged with **noshut** keyword. Useful to ensure test instances don't continue running unintended. This can be deployed as an AWS Lambda function in your test AWS account and scheduled to run at specific time and frequency.
