Auto Shut EC2
=============
This script will automatically shutdown running AWS EC2 instance if not tagged with **noshut** keyword. Useful to ensure test instance don't keep running unintended. This can be deployed as an AWS Lambda function without any modification and scheduled to run at specific a time and frequency.
