# Lambda - Check Function Concurrency

This script will check the concurrency configuration for a given region in your AWS account. The Account Level Concurrent Execution Limit and Function Level Concurrent Execution Limits will be displayed. No changes to your account will be made.

Setting the per function concurrency can impact the concurrency pool available to other functions, and this script is helpful to quickly determine which functions are making use of per function concurrency. 

For more information on managing Lambda concurrency, see https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html

## Requirements
This script requires Python 3.6+

The following IAM permissions are required in your AWS Account:

Lambda
  * GetAccountSettings
  * ListFunctions
  * GetFunction

STS
   * getCallerIdentity

## Usage

`python3 CheckFunctionConcurrency.py`

This script will use the credentials configured with the AWS CLI if available. If not, it will ask for an AWS access key and secret key.







