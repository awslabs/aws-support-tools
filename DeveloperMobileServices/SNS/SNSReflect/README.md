SNS Reflect
-----------
This lambda function will reflect back a SNS notification by publishing to another topic. This is useful if you'd like to receive SMS notification on cloudwatch alarms created in AWS regions that don't support SMS yet.