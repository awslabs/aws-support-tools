# This Python file uses the following encoding: utf-8
'''
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
from __future__ import print_function
import argparse
import json
import sys
import boto3
from botocore.exceptions import ClientError, ProfileNotFound

from report_writer import ReportWriter
from aws_clients import AWSClients
from cloudwatch_verifier import CloudWatchVerifier
from networking_verifier import NetworkingVerifier
from airflow_verifier import AirflowVerifier
from iam_verifier import IAMVerifier
from secrets_verifier import SecretsVerifier
from logs_verifier import LogsVerifier
from utils import *

def prompt_user_and_print_info(input_env_name, ec2_client, mwaa, report: ReportWriter):
    '''method to get environment, report environment information'''
    environment = mwaa.get_environment(
        Name=input_env_name
    )['Environment']
    network_subnet_ids = environment['NetworkConfiguration']['SubnetIds']
    network_subnets = ec2_client.describe_subnets(SubnetIds=network_subnet_ids)['Subnets']

    report.write_all_locations("### Environment Info:")

    for key in environment.keys():
        if key in ['Name', 'Status', 'Arn']:
            print(key, ":", environment[key])
            report.write_key_findings(key, ":", environment[key])
        report.write_full_report(key, ':\n```json\n', json.dumps(environment[key], default=str, indent=2), '\n```')
    report.write_full_report('VPC: ', network_subnets[0]['VpcId'], "\n")
    print()
    return environment, network_subnets, network_subnet_ids

def hello_message():
    print("This is the start of the MWAA verify environment script.")

def goodbye_message():
    print('please send support the collected information including the full report and key findings.')
    print('If you selected not to generate the files, the same information is written to standard output. Copy the output to the support ticket.')
    print('If a case is not opened, you may open one here: https://console.aws.amazon.com/support/home#/case/create')
    print('Please make sure to NOT include any personally identifiable information in the case\n')


if __name__ == '__main__':
    if sys.version_info[0] < 3:
        print("python2 detected, please use python3. Will try to run anyway")
    if not verify_boto3(boto3.__version__):
        print("boto3 version ", boto3.__version__, "is not valid for this script. Need 1.16.25 or higher")
        print("please run pip install boto3 --upgrade --user")
        sys.exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument('--envname', type=validate_envname, required=True, help="name of the MWAA environment")
    parser.add_argument('--region', type=validation_region, default=boto3.session.Session().region_name,
                        required=True, help="region, Ex: us-east-1")
    parser.add_argument('--profile', type=validation_profile, default=None,
                        required=False, help="AWS CLI profile name (optional). If omitted, uses the default credential chain (env vars, instance profile, etc.)")
    args, _ = parser.parse_known_args()
    ENV_NAME = args.envname
    REGION = args.region
    PARTITION = boto3.session.Session().get_partition_for_region(args.region)
    TOP_LEVEL_DOMAIN = '.amazonaws.com.cn' if PARTITION == 'aws-cn' else '.amazonaws.com'
    PROFILE = args.profile
    try:
        hello_message()

        clients = AWSClients(REGION, PROFILE)
        report = ReportWriter()

        env, subnets, subnet_ids = prompt_user_and_print_info(ENV_NAME, clients.ec2, clients.mwaa, report)

        iam_verifier = IAMVerifier(clients, report, env, PARTITION, REGION, ENV_NAME, TOP_LEVEL_DOMAIN)
        cw_verifier = CloudWatchVerifier(clients, report, env)
        net_verifier = NetworkingVerifier(clients, report, env, REGION, PARTITION, TOP_LEVEL_DOMAIN)
        af_verifier = AirflowVerifier(clients, report, env, REGION, ENV_NAME)
        secrets_verifier = SecretsVerifier(clients, report, env)
        logs_verifier = LogsVerifier(clients, report, env, ENV_NAME)

        iam_verifier.check_iam_permissions()

        secrets_verifier.check_kms_key_policy()
        secrets_verifier.check_secrets_manager()

        net_verifier.check_nacl(subnets, subnet_ids)
        net_verifier.check_routes(subnets, subnet_ids)
        net_verifier.check_security_groups()
        net_verifier.check_s3_block_public_access()
        net_verifier.check_connectivity_to_dep_services(subnets, subnet_ids)

        cw_verifier.check_celery_sqs_health()
        cw_verifier.check_environment_class_utilization()
        cw_verifier.check_environment_class_dag_count()

        af_verifier.check_airflow_rest_api()
        af_verifier.check_airflowignore()
        af_verifier.check_full_dag_run()
        af_verifier.check_airflow_config()

        logs_verifier.check_log_groups()
        logs_verifier.check_for_failing_logs()

        report.close()
        goodbye_message()
    except ClientError as client_error:
        if client_error.response['Error']['Code'] == 'LimitExceededException':
            print_err_msg(client_error)
            print('please retry the script')
        elif client_error.response['Error']['Code'] in ['AccessDeniedException', 'NotAuthorized']:
            print_err_msg(client_error)
            print('please verify permissions used have permissions documented in readme')
        elif client_error.response['Error']['Code'] == 'InternalFailure':
            print_err_msg(client_error)
            print('please retry the script')
        else:
            print_err_msg(client_error)
        report.close()
        goodbye_message()
    except ProfileNotFound as profile_not_found:
        print('profile', PROFILE, 'does not exist, please doublecheck the profile name')
    except IndexError as error:
        print("Found index error suggesting there are no ENIs for MWAA")
        print("Error:", error)
        report.close()
        goodbye_message()
