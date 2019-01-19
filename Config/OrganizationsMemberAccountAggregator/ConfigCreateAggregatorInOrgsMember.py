#!/usr/bin/env python3

# The purpose of this script is to create a Config Aggregator
# in an Organizations Member Account that Aggregates all of your
# Organization's Member Accounts across all supported Regions.
# Note: you must run this in an Organizations Master Account

# Each Member Account must have an OrganizationAccountAccessRole
# that matches the string provided to the variable orgs_access_role_name
# the OrganizationAccountAccessRole must have the proper IAM permissions
orgs_access_role_name='OrganizationAccountAccessRole'

import boto3

configuration_aggregator_name='ConfigAggregator1'

# disabled getting regions automatically for now as
# get_available_regions() returns unsupported regions for Config Aggregator
#config_regions=boto3.session.Session().get_available_regions('config')
regions='ap-south-1 ap-northeast-2 ap-southeast-1 ap-southeast-2 ap-northeast-1 ca-central-1 eu-central-1 eu-west-1 eu-west-2 eu-west-3 sa-east-1 us-east-1 us-east-2 us-west-1 us-west-2'
config_regions=regions.split()

answer=None

orgs=boto3.client('organizations')

try:
    organization=orgs.describe_organization()['Organization']
except Exception as e:
    print(e)
    exit(1)

master_account_id=organization['MasterAccountId']

try:
    account_ids=[]
    paginator=orgs.get_paginator('list_accounts')
    for page in paginator.paginate():
        for account in page['Accounts']:
            account_ids.append(account['Id'])
            print(account['Id'])
    AggregatorAccount=input('Please choose the Account where you want the Aggregator to reside in: ')
    if AggregatorAccount not in account_ids:
        print('The Account Id that you entered is not within the Organization!')
        exit(1)
    if (AggregatorAccount == master_account_id):
        print('This script is meant to create a Config Aggregator in a Member Account')
        print('Please choose an Account that is not the Master Account')
        exit(1)
except Exception as e:
    print(e)

sts=boto3.client('sts')

member_orgs_role_arn='arn:aws:iam::' + AggregatorAccount + ':role/' + orgs_access_role_name

try:
    member_credentials=sts.assume_role(
        RoleArn=member_orgs_role_arn,
        RoleSessionName='ConfigAggregatorScript',
    )['Credentials']
except Exception as e:
    print(e)
    exit(1)

config=boto3.client('config',
    aws_access_key_id=member_credentials['AccessKeyId'],
    aws_secret_access_key=member_credentials['SecretAccessKey'],
    aws_session_token=member_credentials['SessionToken'],
)

try:
    config.put_configuration_aggregator(
        ConfigurationAggregatorName=configuration_aggregator_name,
        AccountAggregationSources=[
            {
                'AllAwsRegions':True,
                 'AccountIds':account_ids
            }
        ],
    )
except Exception as e:
    print(e)
    exit(1)

for account in account_ids:
    print('Accepting Authorizations in Account: ' + account)
    account_orgs_role_arn='arn:aws:iam::' + account + ':role/' + orgs_access_role_name
    try:
        if account not in [AggregatorAccount, master_account_id]:
            credentials=sts.assume_role(
                RoleArn=account_orgs_role_arn,
                RoleSessionName='ConfigAggregatorScript',
            )['Credentials']
            member_config=boto3.client('config',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
            )
            for region in config_regions:
                print('Authorizing Region: ' + region)
                member_config.put_aggregation_authorization(
                    AuthorizedAccountId=AggregatorAccount,
                    AuthorizedAwsRegion=region
                )
            authorizations=member_config.describe_aggregation_authorizations()
            print('Sucessfully Authorized Regions in ' + account + ': ')
            for authorization in authorizations['AggregationAuthorizations']:
                print(authorization['AuthorizedAwsRegion'])
        if account == master_account_id:
            master_config=boto3.client('config')
            for region in config_regions:
                print('Authorizing Region: ' + region)
                master_config.put_aggregation_authorization(
                    AuthorizedAccountId=AggregatorAccount,
                    AuthorizedAwsRegion=region
                )
            authorizations=master_config.describe_aggregation_authorizations()
            print('Sucessfully Authorized Regions in ' + account + ': ')
            for authorization in authorizations['AggregationAuthorizations']:
                print(authorization['AuthorizedAwsRegion'])

    except Exception as e:
        print(e)
        print('An error occoured in ' + account)
        while answer not in ['y', 'n', 'a']:
            answer = input('Do you want to continue? Y/A/N: ')
            if answer.lower().startswith('y'):
                print("Continuing")
                answer='unknown'
                break
            elif answer.lower().startswith('a'):
                print("Continuing")
                answer='a'
            elif answer.lower().startswith('n'):
                print("Exiting")
                exit(1)
