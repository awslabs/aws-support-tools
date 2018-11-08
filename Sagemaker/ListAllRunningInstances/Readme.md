# List all running SageMaker instances in your account #

This is a Python script that can be used to find all running sagemaker instances accross all regions at any point in time.

What does this script do:

- Takes in a IAM users credentials 
- It then makes use of the AWS Boto3 python SDK to find all running instances. 
- It cycles through all regions currently supported by sagemaker.
- Returns the instances type as we as per region total and finally the grand total.
