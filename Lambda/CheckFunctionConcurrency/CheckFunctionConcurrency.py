#!/usr/bin/env python3

# This script will check if your AWS account makes use of per-function concurrency in the current region. If so, it will display concurrency used per function.
# IAM Permissions required:
# Lambda: GetAccountSettings, ListFunctions, GetFunctionConcurrency
# STS: getCallerIdentity

import os
import sys
import time
import boto3
import logging
logging.basicConfig(format='%(asctime)s - [%(levelname)s] %(message)s')
logger = logging.getLogger('simple_example')
# logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

# Get Credentials and Region
if os.path.exists(os.path.join(os.path.expanduser("~"), ".aws", "credentials")) or os.path.exists(
        os.path.join(os.path.expanduser("~"), ".aws", "config")):
    profile_name = input("Enter your AWS profile name [Default]: ") or "default"
    session = boto3.Session(profile_name=profile_name)
    default_region = session.region_name
    region = input(f"Enter the AWS Region to check [Default: {default_region}]: ") or default_region
    if region != default_region:
        session = boto3.Session(profile_name=profile_name, region_name=region)
    client = session.client('lambda')
    sts_client = session.client('sts')

else:
    access_key = input("Enter your AWS access key ID: ")
    secret_key = input("Enter your AWS secret key: ")
    region = input("Enter the AWS Region to check")
    client = boto3.client("lambda", aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key, region_name=region)
    sts_client = boto3.client("sts", aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key, region_name=region)

response = client.get_account_settings()
logger.debug(response)

ConcurrentExecutions = response.get('AccountLimit', {}).get('ConcurrentExecutions')
UnreservedConcurrentExecutions = response.get('AccountLimit', {}).get('UnreservedConcurrentExecutions')

accountid = sts_client.get_caller_identity().get('Account')

print(f"""
Account: {accountid}
Region: {region}
Concurrent Execution Limit: {ConcurrentExecutions}
Unreserved Concurrent Execution Limit: {UnreservedConcurrentExecutions}

For more information on managing Lambda concurrency, see https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html
    """)

diff = int(ConcurrentExecutions) - int(UnreservedConcurrentExecutions)

if diff == 0:
    print("Your account does not have any functions with reserved concurrency in this region")
    sys.exit(0)
else:
    print(f"A sum of {diff} concurrent executions are reserved by functions in this region.\nI will now gather which functions have function level concurrent execution limits set...\n\n")


# Get all functions using pagination (list_functions returns max 50 per page)
paginator = client.get_paginator('list_functions')

functionList = []

for page in paginator.paginate():
    logger.debug(f'list_functions page: {page}\n\n')
    for function in page['Functions']:
        logger.debug(f"Function Name: {function['FunctionName']}")
        functionList.append(function['FunctionName'])

print(f"Found {len(functionList)} functions\n")
logger.debug(f"Function List: {functionList}")

print("The Following functions have per-function concurrency reservations:")
print("{:<30} {:<30}".format("FunctionName:", "ReservedConcurrentExecutions:"))

for function in functionList:
    logger.debug(f"Function: {function}")
    retries = 0
    max_retries = 5
    while True:
        try:
            response = client.get_function_concurrency(FunctionName=function)
            reservationStatus = response.get('ReservedConcurrentExecutions')
            if reservationStatus is not None:
                logger.debug(f"reservationStatus: {reservationStatus}")
                print("{:<30} {:<30}".format(function, reservationStatus))
            break
        except client.exceptions.ResourceNotFoundException:
            logger.debug(f"Function {function} not found (may have been deleted)")
            break
        except client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'TooManyRequestsException' and retries < max_retries:
                retries += 1
                wait = min(2 ** retries, 32)
                print(f"Throttled on {function}, backing off {wait}s (retry {retries}/{max_retries})")
                time.sleep(wait)
            else:
                raise

print("Done.")
