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
import socket
import time
import re
import sys
import os
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError, ProfileNotFound
from boto3.session import Session
import os
ENV_NAME = ""
REGION = ""

class ReportWriter:
    def __init__(self):
        self.full_report_file = None
        self.key_findings_file = None

        self.full_report_path = self._generate_unique_filepath("MWAA_DIAGNOSTICS_FULL_REPORT", ".md")
        self.key_findings_path = self._generate_unique_filepath("MWAA_DIAGNOSTICS_KEY_FINDINGS", ".md")
        
        self.full_report_requested = False
        print("Do you allow the results to be written to the following file: " + self.full_report_path + "?")
        print("If you select no, the same information will be written to standard output.")
        if input("(Y/n):").lower().strip() in ["y", "yes", ""]:
            print()
            self.full_report_requested = True
            self.full_report_file = self._setup_report_file("MWAA Diagnostics Full Report", self.full_report_path)

        self.key_findings_requested = False
        print("Do you allow key findings to be written to the following file: " + self.key_findings_path + "?")
        print("If you select no, the same information will be written to standard output.")
        if input("(Y/n):").lower().strip() in ["y", "yes", ""]:
            print()
            self.key_findings_requested = True
            self.key_findings_file = self._setup_report_file("MWAA Diagnostics Key Findings", self.key_findings_path)

    @staticmethod
    def _generate_unique_filepath(base_name, ext):
        counter = 0
        while counter < 1000:
            name = base_name + "_" + datetime.now(timezone.utc).strftime("%d%b%Y_%H%M") + "UTC"
            if counter > 0:
                name = name + "_" + str(counter)
            name += ext
            path = os.path.join(os.getcwd(), name)
            if not os.path.exists(path):
                return path
            counter += 1
        print("Could not generate unique filepath. Exiting...")
        exit(1)

    @staticmethod
    def _setup_report_file(name, path):
        file = open(path, "w")
        file.write("# " + name + "\n\n")
        file.write("Date: " + datetime.now(timezone.utc).strftime("%d %b %Y %H:%M") + " UTC\n\n")
        return file

    def write_full_report(self, *args, sep=' ', end='\n\n'):
        text = sep.join(str(arg) for arg in args) + end
        if self.full_report_requested:
            self.full_report_file.write(text)
        else:
            print(*args, sep=sep, end=end)

    def write_key_findings(self, *args, sep=' ', end='\n\n'):
        text = sep.join(str(arg) for arg in args) + end
        if self.key_findings_requested:
            self.key_findings_file.write(text)
        else:
            print(*args, sep=sep, end=end)

    def write_all_locations(self, *args, sep=' ', end='\n\n'):
        text = sep.join(str(arg) for arg in args) + end
        if self.key_findings_requested:
            self.key_findings_file.write(text)
        if self.full_report_requested:
            self.full_report_file.write(text)
        print(*args, sep=sep, end=end)


    def close(self):
        if self.full_report_requested:
            self.full_report_file.close()
            print("📝 Full report is written to", self.full_report_path)
        if self.key_findings_requested:
            self.key_findings_file.close()
            print("📝 Key findings are written to", self.key_findings_path)

def verify_boto3(boto3_current_version):
    '''
    check if boto3 version is valid, must be 1.16.25 and up
    return true if all dependenceis are valid, false otherwise
    '''
    valid_starting_version = '1.16.25'
    if boto3_current_version == valid_starting_version:
        return True
    ver1 = boto3_current_version.split('.')
    ver2 = valid_starting_version.split('.')
    for i in range(max(len(ver1), len(ver2))):
        num1 = int(ver1[i]) if i < len(ver1) else 0
        num2 = int(ver2[i]) if i < len(ver2) else 0
        if num1 > num2:
            return True
        elif num1 < num2:
            return False
    return False


def get_account_id(env_info):
    '''
    Given the environment metadata, fetch the account id from the
    environment ARN
    '''
    return env_info['Arn'].split(":")[4]


def validate_envname(env_name):
    '''
    verify environment name doesn't have path to files or unexpected input
    '''
    if re.match(r"^[a-zA-Z][0-9a-zA-Z-_]*$", env_name):
        return env_name
    raise argparse.ArgumentTypeError("%s is an invalid environment name value" % env_name)


def validation_region(input_region):
    '''
    verify environment name doesn't have path to files or unexpected input
    REGION: example is us-east-1
    '''
    session = Session()
    partition = session.get_partition_for_region(input_region)
    mwaa_regions = session.get_available_regions('mwaa', partition)
    if input_region in mwaa_regions:
        return input_region
    raise argparse.ArgumentTypeError("%s is an invalid REGION value" % input_region)


def validation_profile(profile_name):
    '''
    verify profile name doesn't have path to files or unexpected input
    '''
    if re.match(r"^[a-zA-Z0-9]*$", profile_name):
        return profile_name
    raise argparse.ArgumentTypeError("%s is an invalid profile name value" % profile_name)


def get_ip_address(hostname, vpc):
    '''
    method to get the hostname's IP address. This will first check to see if there is a VPC endpoint.
    If so, it will use that VPC endpoint's private IP. Sometimes hostnames don't resolve for various DNS reasons.
    This method retries 10 times and sleeps 1 second in between
    '''
    ec2 = boto3.client('ec2', region_name=REGION)
    endpoint = ec2.describe_vpc_endpoints(Filters=[
        {
            'Name': 'service-name',
            'Values': [
                '.'.join(hostname.split('.')[::-1])
            ]
        },
        {
            'Name': 'vpc-id',
            'Values': [
                vpc
            ]
        },
        {
            'Name': 'vpc-endpoint-type',
            'Values': [
                'Interface'
            ]
        }
    ])['VpcEndpoints']
    if endpoint:
        hostname = endpoint[0]['DnsEntries'][0]['DnsName']
    for i in range(0, 10):
        try:
            return socket.gethostbyname(hostname)
        except socket.error:
            print("attempt", i, "failed to resolve hostname: ", hostname, " retrying...")
            time.sleep(1)


def get_enis(input_subnet_ids, vpc, security_groups):
    '''
    method which returns the ENIs used by MWAA based on security groups assigned to the environment
    '''
    enis = {}
    for subnet_id in input_subnet_ids:
        interfaces = ec2.describe_network_interfaces(
            Filters=[
                {
                    'Name': 'subnet-id',
                    'Values': [subnet_id]
                },
                {
                    'Name': 'vpc-id',
                    'Values': [vpc]
                },
                {
                    'Name': 'group-id',
                    'Values': security_groups
                }
            ]
        )['NetworkInterfaces']
        for interface in interfaces:
            enis[subnet_id] = interface['NetworkInterfaceId']
    return enis


def get_inline_policies(iam_client, role_arn):
    """
    Get inline policies in for a role
    """
    inline_policies = iam_client.list_role_policies(RoleName=role_arn)
    return [
            json.dumps(iam_client.get_role_policy(RoleName=role_arn, PolicyName=policy).get("PolicyDocument", ))
            for policy in inline_policies.get("PolicyNames", [])
    ]


def check_iam_permissions(input_env, iam_client, reprot: ReportWriter):
    '''uses iam simulation to check permissions of the role assigned to the environment'''
    report.write_all_locations("### IAM Permissions")
    report.write_all_locations('Checking the IAM execution role', input_env['ExecutionRoleArn'], 'using iam policy simulation')
    account_id = get_account_id(input_env)
    policies = iam_client.list_attached_role_policies(
        RoleName=input_env['ExecutionRoleArn'].split("/")[-1]
    )['AttachedPolicies']
    policy_list = []
    for policy in policies:
        policy_arn = policy['PolicyArn']
        policy_version = iam_client.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
        policy_doc = iam_client.get_policy_version(PolicyArn=policy_arn,
                                                   VersionId=policy_version)['PolicyVersion']['Document']
        policy_list.append(json.dumps(policy_doc))
    eval_results = []
    # Add inline policies
    policy_list.extend(get_inline_policies(iam_client, input_env['ExecutionRoleArn'].split("/")[-1]))
    if "KmsKey" in input_env:
        report.write_full_report('Found Customer managed CMK')
        if PARTITION != 'aws-cn':
            eval_results = eval_results + iam_client.simulate_custom_policy(
                PolicyInputList=policy_list,
                ActionNames=[
                    "airflow:PublishMetrics"
                ],
                ResourceArns=[
                    input_env['Arn']
                ]
            )['EvaluationResults']
        # this next test should be denied
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "s3:ListAllMyBuckets"
            ],
            ResourceArns=[
                input_env['SourceBucketArn'],
                input_env['SourceBucketArn'] + '/'
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "s3:GetObject*",
                "s3:GetBucket*",
                "s3:List*"
            ],
            ResourceArns=[
                input_env['SourceBucketArn'],
                input_env['SourceBucketArn'] + '/'
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "logs:CreateLogStream",
                "logs:CreateLogGroup",
                "logs:PutLogEvents",
                "logs:GetLogEvents",
                "logs:GetLogRecord",
                "logs:GetLogGroupFields",
                "logs:GetQueryResults"
            ],
            ResourceArns=[
                "arn:" + PARTITION + ":logs:" + REGION + ":" + account_id + ":log-group:airflow-" + ENV_NAME + "-*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "logs:DescribeLogGroups"
            ],
            ResourceArns=[
                "*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "cloudwatch:PutMetricData"
            ],
            ResourceArns=[
                "*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "sqs:ChangeMessageVisibility",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage",
                "sqs:SendMessage"
            ],
            ResourceArns=[
                "arn:" + PARTITION + ":sqs:" + REGION + ":*:airflow-celery-*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "kms:GenerateDataKey*"
            ],
            ResourceArns=[
                input_env['KmsKey']
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'kms:viaservice',
                    'ContextKeyValues': [
                        's3.' + REGION + TOP_LEVEL_DOMAIN
                    ],
                    'ContextKeyType': 'string'
                }
            ],
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "kms:GenerateDataKey*"
            ],
            ResourceArns=[
                input_env['KmsKey']
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'kms:viaservice',
                    'ContextKeyValues': [
                        'sqs.' + REGION + '.amazonaws.com',
                    ],
                    'ContextKeyType': 'string'
                }
            ],
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:Encrypt"
            ],
            ResourceArns=[
                input_env['KmsKey']
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'kms:viaservice',
                    'ContextKeyValues': [
                        's3.' + REGION + '.amazonaws.com'
                    ],
                    'ContextKeyType': 'string'
                }
            ],
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:Encrypt"
            ],
            ResourceArns=[
                input_env['KmsKey']
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'kms:viaservice',
                    'ContextKeyValues': [
                        'sqs.' + REGION + '.amazonaws.com'
                    ],
                    'ContextKeyType': 'string'
                }
            ],
        )['EvaluationResults']
    else:
        report.write_full_report('Using AWS CMK')
        if PARTITION != 'aws-cn':
            eval_results = eval_results + iam_client.simulate_custom_policy(
                PolicyInputList=policy_list,
                ActionNames=[
                    "airflow:PublishMetrics"
                ],
                ResourceArns=[
                    input_env['Arn']
                ]
            )['EvaluationResults']
        # this action should be denied
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "s3:ListAllMyBuckets"
            ],
            ResourceArns=[
                input_env['SourceBucketArn'],
                input_env['SourceBucketArn'] + '/'
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "s3:GetObject*",
                "s3:GetBucket*",
                "s3:List*"
            ],
            ResourceArns=[
                input_env['SourceBucketArn'],
                input_env['SourceBucketArn'] + '/'
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "logs:CreateLogStream",
                "logs:CreateLogGroup",
                "logs:PutLogEvents",
                "logs:GetLogEvents",
                "logs:GetLogRecord",
                "logs:GetLogGroupFields",
                "logs:GetQueryResults"
            ],
            ResourceArns=[
                "arn:" + PARTITION + ":logs:" + REGION + ":" + account_id + ":log-group:airflow-" + ENV_NAME + "-*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "logs:DescribeLogGroups"
            ],
            ResourceArns=[
                "*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "cloudwatch:PutMetricData"
            ],
            ResourceArns=[
                "*"
            ]
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "sqs:ChangeMessageVisibility",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage",
                "sqs:SendMessage"
            ],
            ResourceArns=[
                "arn:" + PARTITION + ":sqs:" + REGION + ":*:airflow-celery-*"
            ]
        )['EvaluationResults']
        # tests role to allow any kms all for resources not in this account and that are from the sqs service
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:Encrypt"
            ],
            ResourceArns=[
                "arn:" + PARTITION + ":kms:*:111122223333:key/*"
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'kms:viaservice',
                    'ContextKeyValues': [
                        'sqs.' + REGION + '.amazonaws.com',
                    ],
                    'ContextKeyType': 'string'
                }
            ],
        )['EvaluationResults']
        eval_results = eval_results + iam_client.simulate_custom_policy(
            PolicyInputList=policy_list,
            ActionNames=[
                "kms:GenerateDataKey*"
            ],
            ResourceArns=[
                "arn:" + PARTITION + ":kms:*:111122223333:key/*"
            ],
            ContextEntries=[
                {
                    'ContextKeyName': 'kms:viaservice',
                    'ContextKeyValues': [
                        'sqs.' + REGION + '.amazonaws.com',
                    ],
                    'ContextKeyType': 'string'
                }
            ],
        )['EvaluationResults']

    iam_issue_detected = False
    for eval_result in eval_results:
        # s3:ListAllMyBuckets should be denied. Raise an issue if it is not.
        if eval_result['EvalActionName'] == "s3:ListAllMyBuckets":
            if eval_result['EvalDecision'] != 'allowed':
                report.write_full_report('✅', "Action", eval_result['EvalActionName'], "is blocked successfully on resource", eval_result['EvalResourceName'])
            else:
                report.write_all_locations('🚫', "MWAA expects action", eval_result['EvalActionName'], "to be blocked on resource", eval_result['EvalResourceName'], "but it is not blocked.")
                iam_issue_detected = True
        # Other policies should be allowed.
        elif eval_result['EvalDecision'] != 'allowed':
            report.write_all_locations("🚫", "MWAA expects action", eval_result['EvalActionName'], "to be allowed on resource", eval_result['EvalResourceName'], "but it is not allowed.")
            report.write_all_locations("Failed with the following eval decision:", eval_result['EvalDecision'])
            iam_issue_detected = True
        elif eval_result['EvalDecision'] == 'allowed':
            report.write_full_report('✅', "Action", eval_result['EvalActionName'], "is allowed on resource", eval_result['EvalResourceName'])
        else:
            report.write_all_locations("There is a result with unknown fields:", eval_result)
    
    if iam_issue_detected:
        report.write_all_locations('⚠️ You can investigate the detected policy issue more at')
        report.write_all_locations("https://policysim.aws.amazon.com/home/index.jsp?#roles/" + input_env['ExecutionRoleArn'].split("/")[-1])
    else:
        report.write_all_locations('✅ All IAM policies are as expected.')
    report.write_full_report('These simulations are based off of the sample policies here:')
    report.write_full_report('https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json\n')


def prompt_user_and_print_info(input_env_name, ec2_client, mwaa, report: ReportWriter):
    '''method to get environment, print that information to stdout, and prompt the use to send it to support'''
    # get mwaa environment
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mwaa.html#MWAA.Client.get_environment
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


def check_kms_key_policy(input_env, kms_client):
    '''
    check kms key and if its customer managed if it has a policy like this
    https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json
    '''
    report.write_all_locations("### KMS Key Policy")
    if "KmsKey" in input_env:
        report.write_all_locations("Checking the kms key policy and if it includes reference to airflow")
        policy = kms_client.get_key_policy(
            KeyId=env['KmsKey'],
            PolicyName='default'
        )['Policy']
        if "airflow" not in policy and "aws:logs:arn" not in policy:
            report.write_all_locations("🚫", "MWAA expects texts 'airflow' and 'logs' to appear in KMS key policy but diagnostics cannot find them. Please check KMS key: ",
                  input_env['KmsKey'])
            report.write_all_locations("For an example resource policy, please see this doc: ")
            report.write_all_locations("https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json \n")
        else:
            report.write_all_locations("✅", "KMS key policy includes text 'airflow' and 'logs' as expected.")
    else:
        report.write_all_locations("No KMS key is found in environment configuration. KMS Key is not always required, so this finding does not indicate an issue by itself.")

def check_log_groups(input_env, env_name, logs_client, cloudtrail_client, report: ReportWriter):
    '''check if cloudwatch log groups exists, if not check cloudtrail to see why they weren't created'''
    loggroups = logs_client.describe_log_groups(
        logGroupNamePrefix='airflow-'+env_name
    )['logGroups']
    num_of_enabled_log_groups = sum(
        input_env['LoggingConfiguration'][logConfig]['Enabled'] is True
        for logConfig in input_env['LoggingConfiguration']
    )
    num_of_found_log_groups = len(loggroups)
    report.write_all_locations('### Log groups')
    if num_of_found_log_groups < num_of_enabled_log_groups:
        report.write_all_locations('🚫 The number of log groups is less than the number of enabled suggesting an error.')
        report.write_all_locations('checking cloudtrail for CreateLogGroup/DeleteLogGroup requests...\n')
        events = cloudtrail_client.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventName',
                    'AttributeValue': 'CreateLogGroup'
                },
            ],
            StartTime=input_env['CreatedAt'] - timedelta(minutes=15),
            EndTime=input_env['CreatedAt']
        )['Events']
        events = events + cloudtrail_client.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventName',
                    'AttributeValue': 'DeleteLogGroup'
                },
            ],
            StartTime=input_env['CreatedAt'] - timedelta(minutes=15),
            EndTime=input_env['CreatedAt']
        )['Events']
        events = events + cloudtrail_client.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventName',
                    'AttributeValue': 'DeleteLogGroup'
                },
            ],
            StartTime=datetime.now() - timedelta(minutes=30),
            EndTime=datetime.now()
        )['Events']
        for event in events:
            report.write_all_locations('Found CloudTrail event: ', event)
        report.write_all_locations('if events are failing, try creating the log groups manually\n')
    else:
        report.write_all_locations("✅ Number of log groups match suggesting they've been created successfully.")
    return loggroups


def check_egress_acls(acls, dst_port):
    '''
    method to check egress rules and if they allow port 5432. We don't know the destination IP so we ignore cider group
    taken from
    https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-awssupport-connectivitytroubleshooter.html
    '''
    for acl in acls:
        # check ipv4 acl rule only
        if acl.get('CidrBlock'):
            # Check Port
            if ((acl.get('Protocol') == '-1') or
               (dst_port in range(acl['PortRange']['From'], acl['PortRange']['To'] + 1))):
                # Check Action
                return acl['RuleAction'] == 'allow'
    return ""


def check_ingress_acls(acls, src_port_from, src_port_to):
    '''
    same as check_egress_acls but for ingress
    '''
    for acl in acls:
        # check ipv4 acl rule only
        if acl.get('CidrBlock'):
            # Check Port
            test_range = range(src_port_from, src_port_to)
            set_test_range = set(test_range)
            if ((acl.get('Protocol') == '-1') or
               set_test_range.issubset(range(acl['PortRange']['From'], acl['PortRange']['To'] + 1))):
                # Check Action
                return acl['RuleAction'] == 'allow'
    return ""


def check_nacl(input_subnets, input_subnet_ids, ec2_client, report: ReportWriter):
    '''
    check to see if the nacls for the subnets have port 5432 if they're even listing any specific ports
    '''
    nacls = ec2_client.describe_network_acls(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [input_subnets[0]['VpcId']]
            },
            {
                'Name': 'association.subnet-id',
                'Values': input_subnet_ids
            }
        ]
    )['NetworkAcls']
    report.write_all_locations("### Verify nACLs on subnets")
    nacl_issue_detected = False
    for nacl in nacls:
        egress_acls = [acl for acl in nacl['Entries'] if acl['Egress']]
        ingress_acls = [acl for acl in nacl['Entries'] if not acl['Egress']]
        src_egress_check_pass = check_egress_acls(egress_acls, 5432)
        src_ingress_check_pass = check_ingress_acls(ingress_acls, 5432, 5432)
        if src_egress_check_pass:
            report.write_full_report("✅ nacl:", nacl['NetworkAclId'], "allows port 5432 on egress")
        else:
            report.write_all_locations("🚫 nacl:", nacl['NetworkAclId'], "denied port 5432 on egress")
        if src_ingress_check_pass:
            report.write_full_report("✅ nacl:", nacl['NetworkAclId'], "allows port 5432 on ingress")
        else:
            report.write_all_locations("🚫 nacl:", nacl['NetworkAclId'], "denied port 5432 on ingress")

    if nacl_issue_detected:
        report.write_all_locations("⚠️", "Please investigate the nacl issue.")
    else:
        report.write_all_locations("✅", "All nacls are as expected.")

def check_vpc_endpoint_private_dns_enabled(vpc_endpnts, report: ReportWriter):
    '''short method to check if the interface's private dns option is set to true'''
    for vpc_endpnt in vpc_endpnts:
        if not vpc_endpnt['PrivateDnsEnabled'] and vpc_endpnt['VpcEndpointType'] == 'Interface':
            report.write_all_locations('🚫 VPC endpoint', vpc_endpnt['VpcEndpointId'], "does not have private dns enabled.")
            report.write_all_locations('This means that the public dns name for the service will resolve to its public IP and not')
            report.write_all_locations('the vpc endpoint private ip. You should enable this for use with MWAA')
        else:
            report.write_full_report('✅ VPC endpoint', vpc_endpnt['VpcEndpointId'], "has private dns enabled.")

def check_service_vpc_endpoints(ec2_client, subnets, report: ReportWriter):
    '''
    should be used if the environment does not have internet access through NAT Gateway
    '''
    top_level_domain = ".".join(reversed(TOP_LEVEL_DOMAIN.split(".")))
    service_endpoints = [
        top_level_domain + REGION + '.airflow.api',
        top_level_domain + REGION + '.airflow.env',
        top_level_domain + REGION + '.sqs',
        top_level_domain + REGION + '.ecr.api',
        top_level_domain + REGION + '.ecr.dkr',
        top_level_domain + REGION + '.kms',
        top_level_domain + REGION + '.s3',
        top_level_domain + REGION + '.monitoring',
        top_level_domain + REGION + '.logs'
    ]
    if PARTITION == "aws":
        service_endpoints.append(
           top_level_domain + REGION + '.airflow.ops', 
        )
    vpc_endpoints = ec2_client.describe_vpc_endpoints(Filters=[
        {
            'Name': 'service-name',
            'Values': service_endpoints
        },
        {
            'Name': 'vpc-id',
            'Values': [
                subnets[0]['VpcId']
            ]
        }
    ])['VpcEndpoints']
    # filter by subnet ids here, if the vpc endpoints include the env's subnet ids then check those
    s_ids = [subnet['SubnetId'] for subnet in subnets]
    vpc_endpoints = [endpoint for endpoint in vpc_endpoints if all(subnet in s_ids for subnet in
                     endpoint['SubnetIds'])]
    if len(vpc_endpoints) != 9:
        report.write_full_report("The route for the subnets do not have a NAT gateway." +
                                 "This suggests vpc endpoints are needed to connect to:")
        report.write_full_report('s3, ecr, kms, sqs, monitoring, airflow.api, airflow.env.')
        report.write_full_report("The environment's subnets currently have these endpoints: ")
        for endpoint in vpc_endpoints:
            report.write_full_report(endpoint['ServiceName'])
        report.write_all_locations("🚫 The environment's subnets do not have these required endpoints: ")
        vpc_service_endpoints = [e['ServiceName'] for e in vpc_endpoints]
        for i, service_endpoint in enumerate(service_endpoints):
            if service_endpoint not in vpc_service_endpoints:
                report.write_all_locations(service_endpoint)
        check_vpc_endpoint_private_dns_enabled(vpc_endpoints)
        return True
    else:
        report.write_full_report("✅ The route for the subnets do not have a NAT Gateway. However, there are sufficient VPC endpoints")
        return False


def check_routes(input_env, input_subnets, input_subnet_ids, ec2_client, report: ReportWriter):
    '''
    method to check and make sure routes have access to the internet if public and subnets are private
    '''
    # vpc should be the same so I just took the first one
    routes = ec2_client.describe_route_tables(Filters=[
            {
                'Name': 'vpc-id',
                'Values': [input_subnets[0]['VpcId']]
            },
            {
                'Name': 'association.subnet-id',
                'Values': input_subnet_ids
            }
    ])
    # check subnets are private
    report.write_all_locations("### Verify route table validity")
    route_issue_detected = False
    for route_table in routes['RouteTables']:
        has_nat = False
        for route in route_table['Routes']:
            if route['State'] == "blackhole":
                report.write_all_locations("🚫 Route:", route_table['RouteTableId'], 'has a state of blackhole.')
                route_issue_detected = True
            if 'GatewayId' in route and route['GatewayId'].startswith('igw'):
                report.write_all_locations('🚫 Route:', route_table['RouteTableId'],
                      'has a route to IGW making the subnet public. Needs to be private.')
                report.write_all_locations('please review ',
                      'https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html#vpc-create-required')
                route_issue_detected = True
            if 'NatGatewayId' in route:
                has_nat = True
        if has_nat:
            report.write_full_report('✅ Route Table', route_table['RouteTableId'], 'does have a route to a NAT Gateway.')
        if not has_nat:
            report.write_full_report('Route Table:', route_table['RouteTableId'], 'does not have a route to a NAT Gateway')
            report.write_full_report('Checking for VPC endpoints to airflow, s3, sqs, kms, ecr, and monitoring...')
            endpoint_issue_detected = check_service_vpc_endpoints(ec2_client, input_subnets, report)
            if endpoint_issue_detected:
                route_issue_detected = True
    if route_issue_detected:
        report.write_all_locations("⚠️", "Please investigate the route issue.")
    else:
        report.write_all_locations("✅", "All routes are as expected.")

def _check_access_blocked(block_config_type, client, report: ReportWriter, **request_kwargs):
    '''
    Checks whether public access is blocked for <block_config_type> (either
    bucket or account) using the client and args passed in.
    '''
    report.write_all_locations('Checking if public access is blocked at the {config_type} level'.format(config_type=block_config_type))
    try:
        public_access_block = client.get_public_access_block(**request_kwargs)
    except ClientError as client_error:
        # The same client error is thrown for both account level and bucket level configs
        report.write_all_locations('The {config_type} level access block config is not set'.format(config_type=block_config_type))
        if client_error.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
            # If the config isn't set then act as if it's public
            return False
        # if it's any other exception scenario raise so that the user is notified
        raise

    # If we successfully got a config, check if public access is blocked or not
    return public_access_block['PublicAccessBlockConfiguration']['BlockPublicAcls']

def check_s3_block_public_access(input_env, s3_client, s3_control_client, report: ReportWriter):
    '''check s3 bucket or account and make sure "block public access" is enabled'''
    report.write_all_locations("### Verifying 'block public access' is enabled on the s3 bucket or account")
    account_id = get_account_id(input_env)
    bucket_arn = input_env['SourceBucketArn']
    bucket_name = bucket_arn.split(':')[-1]
    public_access_block = None

    if any([_check_access_blocked('bucket', s3_client, report, Bucket=bucket_name),
            _check_access_blocked('account', s3_control_client, report, AccountId=account_id)]):
        report.write_all_locations(f'✅ s3 bucket, {bucket_arn}, or account blocks public access.')
    else:
        report.write_all_locations(f'🚫 s3 bucket, {bucket_arn}, or account does NOT block public access.')


def check_security_groups(input_env, ec2_client, report: ReportWriter):
    '''
    check MWAA environment's security groups for:
        - have at least 1 rule
        - checks ingress to see if sg allows itself
        - egress is checked by SSM document for 443 and 5432
    '''
    security_groups = input_env['NetworkConfiguration']['SecurityGroupIds']
    groups = ec2_client.describe_security_groups(
        GroupIds=security_groups
    )['SecurityGroups']
    # have a sanity check on ingress and egress to make sure it allows something
    report.write_all_locations('### Trying to verify ingress on security groups...')
    ingress_self_allowed = True
    for security_group in groups:
        ingress = security_group['IpPermissions']
        egress = security_group['IpPermissionsEgress']
        if not ingress:
            report.write_all_locations('🚫 Ingress for security group: ', security_group['GroupId'], ' requires at least one rule')
            ingress_self_allowed = False
            break
        if not egress:
            report.write_all_locations('🚫 Egress for security group: ', security_group['GroupId'], ' requires at least one rule')
            break
        # check security groups to ensure port at least the same security group or everything is allowed ingress
        for rule in ingress:
            if rule['IpProtocol'] == "-1":
                if rule['UserIdGroupPairs'] and not (
                    any(x['GroupId'] == security_group['GroupId'] for x in rule['UserIdGroupPairs'])
                ):
                    ingress_self_allowed = False
                    break
    if ingress_self_allowed:
        report.write_all_locations("✅ Ingress for security groups have at least 1 rule to allow itself.")
    else:
        report.write_all_locations("🚫 Ingress for security groups do not have at least 1 rule to allow itself.")


def wait_for_ssm_step_one_to_finish(ssm_execution_id, ssm_client):
    '''
    check if the first step finished because that will do the test on the IP to get the eni.
    The eni changes to quickly that sometimes this fails so I retry till it works
    '''
    execution = ssm_client.get_automation_execution(
        AutomationExecutionId=ssm_execution_id
    )['AutomationExecution']['StepExecutions'][0]['StepStatus']
    while True:
        if execution in ['Success', 'TimedOut', 'Cancelled', 'Failed']:
            break
        time.sleep(5)
        execution = ssm_client.get_automation_execution(
            AutomationExecutionId=ssm_execution_id
        )['AutomationExecution']['StepExecutions'][0]['StepStatus']


def check_connectivity_to_dep_services(input_env, input_subnets, ec2_client, ssm_client, mwaa_utilized_services, report: ReportWriter):
    '''
    uses ssm document AWSSupport-ConnectivityTroubleshooter to check connectivity between MWAA's enis
    and a list of services. More information on this document can be found here
    https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-awssupport-connectivitytroubleshooter.html
    '''
    report.write_all_locations("### Connectivity Check via ENIs\nPlease see the full report for results if no error in output.")
    report.write_full_report("Testing connectivity to the following service endpoints from MWAA enis...")
    vpc = subnets[0]['VpcId']
    security_groups = input_env['NetworkConfiguration']['SecurityGroupIds']
    for service in mwaa_utilized_services:
        # retry 5 times for just one of the enis the service uses
        for i in range(0, 5):
            try:
                # get ENIs used by MWAA
                enis = get_enis(subnet_ids, vpc, security_groups)
                if not enis:
                    report.write_all_locations("🚫 no enis found for MWAA, exiting test for ", service['service'])
                    report.write_all_locations("please try accessing the airflow UI and then try running this script again")
                    break
                eni = list(enis.values())[0]
                interface_ip = ec2_client.describe_network_interfaces(
                    NetworkInterfaceIds=[eni]
                )['NetworkInterfaces'][0]['PrivateIpAddress']
                ssm_execution_id = ''
                ssm_execution_id = ssm_client.start_automation_execution(
                    DocumentName='AWSSupport-ConnectivityTroubleshooter',
                    DocumentVersion='$DEFAULT',
                    Parameters={
                        'SourceIP': [interface_ip],
                        'DestinationIP': [get_ip_address(service['service'], input_subnets[0]['VpcId'])],
                        'DestinationPort': [service['port']],
                        'SourceVpc': [vpc],
                        'DestinationVpc': [vpc],
                        'SourcePortRange': ["0-65535"]
                    }
                )['AutomationExecutionId']
                wait_for_ssm_step_one_to_finish(ssm_execution_id, ssm_client)
                execution = ssm_client.get_automation_execution(
                    AutomationExecutionId=ssm_execution_id
                )['AutomationExecution']
                # check if the failure is due to not finding the eni. If it is, retry testing the service again
                if execution['StepExecutions'][0]['StepStatus'] != 'Failed':
                    report.write_full_report('Testing connectivity between eni', eni, "with private ip of",
                          interface_ip, "and", service['service'], "on port", service['port'])
                    report.write_full_report("Please follow this link to view the results of the test:")
                    report.write_full_report("https://console.aws.amazon.com/systems-manager/automation/execution/" + ssm_execution_id +
                          "?REGION=" + REGION + "\n")
                    break
            except ClientError as client_error:
                report.write_all_locations('🚫 Attempt', i, 'encountered error', client_error.response['Error']['Message'], ' retrying...')


def check_for_failing_logs(loggroups, logs_client, report: ReportWriter):
    '''look for any failing logs from CloudWatch in the past hour'''
    report.write_all_locations("### Failing Cloudwatch Logs\nChecking CloudWatch logs for any errors less than 1 hour old")
    now = int(time.time() * 1000)
    past_day = now - 3600000
    for log in loggroups:
        events = logs_client.filter_log_events(
            logGroupName=log['logGroupName'],
            startTime=past_day,
            endTime=now,
            filterPattern='?ERROR ?Error ?error ?traceback ?Traceback ?exception ?Exception ?fail ?Fail'
        )['events']
        events = sorted(events, key=lambda i: i['timestamp'])
        report.write_all_locations('Log group: ', log['logGroupName'])
        if len(events) == 0:
            report.write_all_locations('✅ No error logs found in the past hour')
            continue
        report.write_all_locations('⚠️ Please see the full report for logs.')
        for event in events:
            report.write_full_report(str(event['timestamp']) + " " + event['message'], end='')


def print_err_msg(c_err):
    '''short method to handle printing an error message if there is one'''
    print('Error Message: {}'.format(c_err.response['Error']['Message']))
    print('Request ID: {}'.format(c_err.response['ResponseMetadata']['RequestId']))
    print('Http code: {}'.format(c_err.response['ResponseMetadata']['HTTPStatusCode']))


def get_mwaa_utilized_services(ec2_client, vpc):
    '''return an array objects for the services checking for ecr.dks and if it exists add it to the array'''
    mwaa_utilized_services = [{"service": 'sqs.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 'api.ecr.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 'monitoring.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 'kms.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 's3.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 'env.airflow.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 'env.airflow.' + REGION + TOP_LEVEL_DOMAIN, "port": "5432"},
                              {"service": 'api.airflow.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"},
                              {"service": 'logs.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"}]
    if PARTITION == 'aws':
        mwaa_utilized_services.append(
                              {"service": 'ops.airflow.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"}
        )
    ecr_dks_endpoint = ec2_client.describe_vpc_endpoints(Filters=[
        {
            'Name': 'service-name',
            'Values': ['com.amazonaws.us-east-1.ecr.dkr']
        },
        {
            'Name': 'vpc-id',
            'Values': [vpc]
        },
        {
            'Name': 'vpc-endpoint-type',
            'Values': ['Interface']
        }
    ])['VpcEndpoints']
    if ecr_dks_endpoint:
        mwaa_utilized_services.append({"service": 'dkr.ecr.' + REGION + TOP_LEVEL_DOMAIN, "port": "443"})
    return mwaa_utilized_services


def check_airflow_rest_api_iam(input_env, iam_client, report: ReportWriter):
    ''' Check which airflow roles the user gave access for REST API using IAM simulation to check policy permissions'''
    account_id = get_account_id(input_env)
    airflow_roles = {"Admin":"", "Op":"", "User":"", "Viewer":"", "Public":""}
    policies = iam_client.list_attached_role_policies(
        RoleName=input_env["ExecutionRoleArn"].split("/")[-1]
    )["AttachedPolicies"]
    policy_list = []
    for policy in policies:
        policy_arn = policy["PolicyArn"]
        policy_version = iam_client.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
        policy_doc = iam_client.get_policy_version(PolicyArn=policy_arn,
                                                   VersionId=policy_version)['PolicyVersion']['Document']
        policy_list.append(json.dumps(policy_doc))
    policy_list.extend(get_inline_policies(iam_client, input_env['ExecutionRoleArn'].split("/")[-1]))
    for role in airflow_roles.keys():
        results = iam_client.simulate_custom_policy(
                PolicyInputList=policy_list,
                ActionNames=[
                    "airflow:InvokeRestApi"
                ],
                ResourceArns=[
                    "arn:aws:airflow:" + REGION + ":" + account_id + ":role/" + ENV_NAME + "/" + role
                ]
            )["EvaluationResults"]
    
        for result in results:
            airflow_roles[result["EvalResourceName"].split("/")[-1]] = result["EvalDecision"]

    if "allowed" in airflow_roles.values():
        report.write_all_locations("🔐 The following Airflow roles have IAM permissions to access the Airflow REST API: ")
        for role in airflow_roles.keys():
            if airflow_roles[role] == "allowed":
                report.write_all_locations(role, end=" ")
        report.write_all_locations("\n")

    if list(airflow_roles.values()).count("allowed") < len(airflow_roles.values()):
        report.write_all_locations("🔒 The following Airflow roles do not have IAM permissions to access the Airflow REST API: ")
        for role in airflow_roles.keys():
            if airflow_roles[role] != "allowed":
                report.write_all_locations(role, end=" ")
        report.write_all_locations("\n")
    return airflow_roles


def check_airflow_rest_api_health(input_env, mwaa_client):
    request_params = {
        "Name": input_env["Name"],
        "Path": "/monitor/health" if int(input_env["AirflowVersion"].split(".")[0]) >= 3 else "/health",
        "Method": "GET"
        }

    report.write_all_locations("Airflow REST API /health endpoint is invoked.")

    try:
        response = mwaa_client.invoke_rest_api(
            **request_params
        )
    except ClientError as client_error:
        report.write_all_locations("🚫 Airflow REST API invocation failed with the following error:\n", client_error)
        return

    report.write_all_locations("✅ Airflow REST API invocation succeeded.")

    for component, info in response['RestApiResponse'].items():
        status = info['status']
        emoji = '✅' if status == 'healthy' else '🚫'
        report.write_all_locations(f"{emoji} {component.replace('_', ' ').title()}: {status}")
        
        # Find heartbeat key
        heartbeat_key = next((k for k in info.keys() if 'heartbeat' in k), None)
        if heartbeat_key:
            heartbeat = info[heartbeat_key].split('T')[0] + ' ' + info[heartbeat_key].split('T')[1][:8]
            report.write_full_report(f"   Last heartbeat: {heartbeat}")
        else:
            report.write_full_report(f"   This resource does not publish a heartbeat")

def check_airflow_rest_api(env, mwaa, iam, report: ReportWriter):
    report.write_all_locations("### Airflow REST API")

    roles_rest_api_allowed_status = check_airflow_rest_api_iam(env, iam, report)

    if "allowed" in roles_rest_api_allowed_status.values():
        print("Do you allow the following tests to trigger Airflow REST API and access inside your Airflow environment?\n" +
            "The gathered information will be saved on your device. It will not be shared with AWS.")
        if input("(Y/n):").lower().strip() in ["y", "yes", ""]:
            print()
            check_airflow_rest_api_health(env, mwaa)
        else:
            report.write_all_locations("Skipping Airflow REST API test because user did not allow test to access REST API")
    else:
        report.write_all_locations("Skipping Airflow REST API test because no role have IAM permissions to access REST API.")
        report.write_all_locations("If you would like to allow REST API access: https://docs.aws.amazon.com/mwaa/latest/userguide/access-mwaa-apache-airflow-rest-api.html#granting-access-MWAA-Enhanced-REST-API")

def upload_file_to_dags_folder(env, file_path, s3_client):
    """
    Upload a file to the environment's DAGs folder in S3
    
    Args:
        env: MWAA environment dict containing SourceBucketArn and DagS3Path
        file_path: Local path to file to upload
        s3_client: Boto3 S3 client
    """
    # Get bucket name from ARN
    bucket_name = env['SourceBucketArn'].split(':')[-1]
    # Get file name from path
    file_name = file_path.split('/')[-1]
    s3_key = env['DagS3Path'] + file_name
    
    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        return True
        
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return False

def delete_file_from_dags_folder(env, file_path, s3_client):
    """
    Delete a file from the environment's DAGs folder in S3
    
    Args:
        env: MWAA environment dict containing SourceBucketArn and DagS3Path 
        file_path: Local path to file to delete
        s3_client: Boto3 S3 client
    """
    # Get bucket name from ARN
    bucket_name = env['SourceBucketArn'].split(':')[-1]
    # Get file name from path 
    file_name = file_path.split('/')[-1]
    s3_key = env['DagS3Path'] + file_name
    
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        return True
        
    except ClientError as e:
        print(f"Error deleting file from S3: {e}")
        return False

def perform_dag_run(input_env, dag_id, mwaa_client, report: ReportWriter):
    # Unpause and trigger the DAG run
    try:
        unpause_request_params = {
            "Name": input_env["Name"],
            "Path": f"/dags/{dag_id}",
            "Method": "PATCH",
            "Body": {"is_paused": False}
        }
        unpause_response = mwaa_client.invoke_rest_api(**unpause_request_params)
        
        if unpause_response.get('RestApiStatusCode') not in [200, 201]:
            report.write_all_locations("🚫 Failed to unpause DAG:", unpause_response.get('RestApiResponse', {}))
            return
            
    except ClientError as client_error:
        report.write_all_locations("🚫 Failed to unpause DAG:", client_error.response)
        return
    
    report.write_all_locations(f"✅ DAG '{dag_id}' unpaused successfully")

    try:
        dag_run_id = f"test_run_{int(time.time())}"
        trigger_request_params = {
            "Name": input_env["Name"],
            "Path": f"/dags/{dag_id}/dagRuns",
            "Method": "POST",
            "Body": {
                "dag_run_id": dag_run_id,
                "logical_date": datetime.now(timezone.utc).isoformat(),
                "conf": {}
            }
        }
        trigger_response = mwaa_client.invoke_rest_api(**trigger_request_params)
        
        if trigger_response.get('RestApiStatusCode') not in [200, 201]:
            report.write_all_locations("🚫 Failed to trigger DAG run:", trigger_response.get('RestApiResponse', {}))
            return
            
    except ClientError as client_error:
        report.write_all_locations("🚫 Failed to trigger DAG run:", client_error.response)
        return
    
    report.write_all_locations(f"✅ Successfully triggered DAG run with ID: {dag_run_id}")

    # Monitor the DAG run status
    print("Monitoring DAG run progress...")
    
    max_wait_time = 300  # 5 minutes
    check_interval = 10  # 10 seconds
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        try:
            status_request_params = {
                "Name": input_env["Name"],
                "Path": f"/dags/{dag_id}/dagRuns/{dag_run_id}",
                "Method": "GET"
            }
            
            status_response = mwaa_client.invoke_rest_api(**status_request_params)
            dag_run_info = status_response.get('RestApiResponse', {})
            
            state = dag_run_info.get('state', 'unknown')
            
            if state == 'success':
                report.write_all_locations(f"✅ DAG run completed successfully!")
                report.write_all_locations(f"   Start time: {dag_run_info.get('start_date', 'N/A')}")
                report.write_all_locations(f"   End time: {dag_run_info.get('end_date', 'N/A')}")
                
                # Get task instances to show detailed results
                try:
                    tasks_request_params = {
                        "Name": input_env["Name"],
                        "Path": f"/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances",
                        "Method": "GET"
                    }
                    
                    tasks_response = mwaa_client.invoke_rest_api(**tasks_request_params)
                    task_instances = tasks_response.get('RestApiResponse', {}).get('task_instances', [])
                    
                    report.write_all_locations("Task execution results:")
                    for task in task_instances:
                        task_state = task.get('state', 'unknown')
                        task_emoji = '✅' if task_state == 'success' else '🚫'
                        report.write_all_locations(f"   {task_emoji} {task.get('task_id', 'unknown')}: {task_state}")
                        
                except ClientError:
                    report.write_full_report("Could not retrieve detailed task information")
                
                return
                
            elif state == 'failed':
                report.write_all_locations(f"🚫 DAG run failed!")
                report.write_all_locations(f"   Start time: {dag_run_info.get('start_date', 'N/A')}")
                report.write_all_locations(f"   End time: {dag_run_info.get('end_date', 'N/A')}")
                return
                
            elif state in ['running', 'queued']:
                print(f"DAG run status: {state} (elapsed: {elapsed_time}s)")
                time.sleep(check_interval)
                elapsed_time += check_interval
                
            else:
                report.write_all_locations(f"⚠️ DAG run in unexpected state: {state}")
                return
                
        except ClientError as client_error:
            report.write_all_locations("🚫 Failed to check DAG run status:", client_error.response['Error']['Message'])
            return
    
    # If we reach here, the DAG run timed out
    report.write_all_locations(f"⚠️ DAG run monitoring timed out after {max_wait_time} seconds.")
    report.write_all_locations("The DAG may still be running. Check the Airflow UI for current status.")


def check_full_dag_run(input_env, mwaa_client, s3, report: ReportWriter):
    """
    Test a full DAG run using the MWAA REST API to trigger and monitor a simple test DAG
    """
    report.write_all_locations("### Full DAG Run Test")
    
    print("Do you allow the following test to:")
    print("    1. Use Airflow REST API to check if MWAA_OWNED_TEST_DAG.py is already uploaded.")
    print("    2. Upload MWAA_OWNED_TEST_DAG.py if not found.")
    print("    3. Use Airflow REST API to invoke the dag run")
    print("The gathered information will be saved on your device. It will not be shared with AWS.")
    if input("(Y/n):").lower().strip() not in ["y", "yes", ""]:
        report.write_all_locations("Skipping full DAG run test because user did not give permission.")
        return
    print()
    
    dag_id = "mwaa_owned_test_dag"
    
    # First, check if the DAG exists
    dag_request_params = {
        "Name": input_env["Name"],
        "Path": f"/dags/{dag_id}",
        "Method": "GET"
    }
    
    status_code = 400
    dag_response = None
    try:
        dag_response = mwaa_client.invoke_rest_api(**dag_request_params)
    except ClientError as client_error:
        dag_response = client_error.response
    status_code = dag_response.get('RestApiStatusCode')

    if status_code == 200:
        report.write_all_locations(f"✅ Test DAG '{dag_id}' is found in the environment.") 
    elif status_code == 404:
        report.write_all_locations(f"Test DAG '{dag_id}' not found in the environment. Uploading...")
        upload_file_to_dags_folder(input_env, os.path.join(os.path.dirname(os.path.realpath(__file__)), "MWAA_OWNED_TEST_DAG.py"), s3)

        print("Waiting for DAG to be uploaded and recognized by Airflow. This can take up to 10 minutes.")

        dag_found = False
        for i in range(30):
            try:
                dag_response = mwaa_client.invoke_rest_api(**dag_request_params)
            except ClientError as client_error:
                dag_response = client_error.response
            status_code = dag_response.get('RestApiStatusCode')
            if status_code == 200:
                dag_found = True
                break
            elif status_code != 404:
                report.write_all_locations(f"🚫 Error checking if upload is successful:", dag_response.get('RestApiResponse', {}))
                return
            print(f"DAG is not recognized by Airflow yet. Waiting... (elapsed {(i+1)*20}s)")
            time.sleep(20)

        if not dag_found:
            report.write_all_locations("🚫 Automatic upload failed.")
            report.write_all_locations("Please upload MWAA_OWNED_TEST_DAG.py to your DAGs folder.")
            return
        
        report.write_all_locations(f"✅ Test DAG '{dag_id}' is uploaded.")
    else:
        report.write_all_locations(f"🚫 Failed to check if test DAG '{dag_id}' exists:", dag_response.get('RestApiResponse', {}))
        return
    
    perform_dag_run(input_env, dag_id, mwaa_client, report)

    print("Do you want to delete the dag used for the test?")
    if input("(y/N):").lower().strip() in ["y", "yes"]:
        delete_file_from_dags_folder(input_env, os.path.join(os.path.dirname(os.path.realpath(__file__)), "MWAA_OWNED_TEST_DAG.py"), s3)
        report.write_all_locations(f"✅ Test DAG '{dag_id}' is deleted.")
    else:
        report.write_all_locations(f"✅ The user selected to keep the test DAG '{dag_id}'.")


def check_celery_sqs_health(env, cw, report: ReportWriter):
    report.write_all_locations("### Checking Celery executor SQS queue health...")
    metrics = ["TaskQueued", "TaskPulled", "TaskExecuted"]
    dimensions = [
            {
                "Name": "Environment",
                "Value": env["Name"]
            },
            {
                "Name": "Function",
                "Value": "Celery"
            }
        ]
    
    for metric in metrics:
        response = cw.get_metric_statistics(
            Namespace="AmazonMWAA",
            MetricName=metric,
            Dimensions=dimensions,
            StartTime=datetime.now(timezone.utc) - timedelta(hours=24),
            EndTime=datetime.now(timezone.utc),
            Period=300,  # 5 minutes
            Statistics=["Average"]
        )

        # Find the latest datapoint
        if response["Datapoints"]:
            latest = max(response["Datapoints"], key=lambda x: x["Timestamp"])
            delta = datetime.now(timezone.utc) - latest['Timestamp']
            hours = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            report.write_all_locations(f"{metric} Latest Datapoint - {hours}h {minutes}m ago - Time: {latest['Timestamp']}, Value: {latest['Average']}")
        else:
            report.write_all_locations(f"⚠️ {metric} did not have any datapoints in last 24 hours.")

    response = cw.get_metric_statistics(
        Namespace="AmazonMWAA",
        MetricName="CeleryWorkerHeartbeat",
        Dimensions=dimensions,
        StartTime=datetime.now(timezone.utc) - timedelta(minutes=20),
        EndTime=datetime.now(timezone.utc),
        Period=300,  # 5 minutes
        Statistics=["Average"]
    )

    if response["Datapoints"]:
        report.write_all_locations("✅ Celery worker heartbeat received in last 20 minutes.")
    else:
        report.write_all_locations("🚫 No Celery Worker heartbeat received in last 20 minutes")

def check_environment_class_utilization(env, cw, report: ReportWriter):
    '''https://docs.aws.amazon.com/mwaa/latest/userguide/environment-class.html
    
    For one of BaseWorker, Scheduler, or WebServer clusters,
    if the average CPU Utilization or Memory Utilization for 
    last 7 days is above a certain percentage, suggest upgrade.
    '''
    report.write_all_locations("### Environment Class - Cluster Utilization")
    THRESHOLD = 85

    clusters = ["BaseWorker", "Scheduler", "WebServer"]
    metrics = ["CPUUtilization", "MemoryUtilization"]
    env_classes = ["mw1.micro", "mw1.small", "mw1.medium", "mw1.large", "mw1.xlarge", "mw1.2xlarge"]

    suggest_upgrade = False
    for metric in metrics:
        for cluster in clusters:
            dimensions = [
                {
                    "Name": "Environment",
                    "Value": env["Name"]
                },
                {
                    "Name": "Cluster",
                    "Value": cluster
                }
            ]

            response = cw.get_metric_statistics(
                Namespace="AWS/MWAA",
                MetricName=metric,
                Dimensions=dimensions,
                StartTime=datetime.now(timezone.utc) - timedelta(days=7),
                EndTime=datetime.now(timezone.utc),
                Period=604800,  # 7 days
                Statistics=["Average"]
            )

            if response["Datapoints"][0]["Average"] > THRESHOLD:
                suggest_upgrade = True
                report.write_all_locations("⚠️ The", cluster, "cluster had an average", metric, "of",
                                           int(response["Datapoints"][0]["Average"]), response["Datapoints"][0]["Unit"].lower(),
                                           "over last 7 days. MWAA recommends this value to be less than", THRESHOLD, "percent.")
            else:
                report.write_full_report("✅ The", cluster, "cluster had an average", metric, "of",
                                           int(response["Datapoints"][0]["Average"]), response["Datapoints"][0]["Unit"].lower(),
                                           "over last 7 days. This is under the MWAA recommended threshold of", THRESHOLD, "percent.")

    if suggest_upgrade:
        if env["EnvironmentClass"] == env_classes[-1]:
            report.write_all_locations("⚠️ Your utilization is higher than the threshold although you use the largest environment class.")
            report.write_all_locations("Consider MWAA best practices for performance tuning: https://docs.aws.amazon.com/mwaa/latest/userguide/best-practices-tuning.html")
        else:
            report.write_all_locations("⚠️ MWAA recommends the environment class to be upgraded to " + env_classes[env_classes.index(env["EnvironmentClass"]) + 1])
            report.write_all_locations("You can also consider MWAA best practices for performance tuning: https://docs.aws.amazon.com/mwaa/latest/userguide/best-practices-tuning.html")
    else:
        report.write_all_locations("✅ The average CPU and memory utilizations of all clusters were under the threshold of", THRESHOLD, "percent for the last 7 days.")

def check_environment_class_dag_count(env, cw, report):
    report.write_all_locations("### Environment Class - DAG Count")
    env_class_dag_capacities = [
        ("mw1.micro", 25),
        ("mw1.small", 50),
        ("mw1.medium", 250),
        ("mw1.large", 1000),
        ("mw1.xlarge", 2000),
        ("mw1.2xlarge", 4000)
    ]

    dimensions = [
        {
            "Name": "Environment",
            "Value": env["Name"]
        },
        {
            "Name": "Function",
            "Value": "DAG Processing"
        }
    ]

    response = cw.get_metric_statistics(
        Namespace="AmazonMWAA",
        MetricName="DagBagSize",
        Dimensions=dimensions,
        StartTime=datetime.now(timezone.utc) - timedelta(minutes=6),
        EndTime=datetime.now(timezone.utc),
        Period=300,  # 5 minutes
        Statistics=["Average"]
    )

    dagcount = int(response["Datapoints"][0]["Average"])
    report.write_all_locations("Dag count:", dagcount)

    current_capacity = 0
    for env_class, capacity in env_class_dag_capacities:
        if env["EnvironmentClass"] == env_class:
            current_capacity = capacity
            break

    if dagcount > current_capacity:
        report.write_all_locations("⚠️ The DAG count exceeds the capacity of the environment class. Consider upgrading to a larger environment class.")
    else:
        report.write_all_locations("✅ The DAG count is within the capacity of the", env["EnvironmentClass"], "environment class.")

def check_airflowignore(env, s3, report: ReportWriter):

    common_ignores = [".ipynb_checkpoints", ".git", "__pycache__"]

    report.write_all_locations("### Check `.airflowignore`")
    
    print("Do you allow the following test to use the S3 API to read your dags folder structure including subfolders and filenames?")
    if input("(Y/n):").lower().strip() not in ["y", "yes", ""]:
        report.write_all_locations("Skipping Airflow ignore test because user did not allow test to read dags folder structure.")
        return
    
    print()
    
    bucket_name = env['SourceBucketArn'].split(':')[-1]
    dags_prefix = env['DagS3Path']
    
    files_and_folders = []

    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=dags_prefix)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    files_and_folders.append(obj['Key'])
    except Exception as e:
        report.write_all_locations(f"Error reading S3 folder structure: {e}")
    
    found_paths_in_dags = []
    found_names_in_dags = []
    for path in files_and_folders:
        for ignore in common_ignores:
            if ignore in path:
                found_paths_in_dags.append(path)
                found_names_in_dags.append(ignore)
    
    if not found_paths_in_dags:
        report.write_all_locations("✅ The dags folder does not include any folder names that are knwon to be commonly included by mistake.")
        return
    
    report.write_full_report("The dags folder includes the following folders / files that might be included by mistake:")
    for path in found_paths_in_dags:
        report.write_full_report("   ", path)

    if (dags_prefix + ".airflowignore") not in files_and_folders:
        report.write_all_locations("⚠️ The dags folder does not include a .airflowignore file but includes the following folders / files that might be included by mistake:")
        for path in found_paths_in_dags:
            report.write_all_locations("   ", path)
        report.write_all_locations("Consider adding a .airflowignore file to your dags folder to exclude these folders / files.")
        return

    report.write_all_locations("✅ The dags folder includes a .airflowignore file.")
    print("Do you allow the test to read the .airflowignore file?")
    if input("(Y/n):").lower().strip() not in ["y", "yes", ""]:
        report.write_all_locations("Skipping reading .airflowignore file because user did not allow read.")
        return

    airflowignore_content = None
    try:
        response = s3.get_object(Bucket=bucket_name, Key=dags_prefix + ".airflowignore")
        airflowignore_content = response['Body'].read().decode('utf-8')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            report.write_all_locations("⚠️ .airflowignore file not found at location:", dags_prefix + ".airflowignore")
        else:
            report.write_all_locations(f"Error reading .airflowignore file: {e}")

    all_ignores_found = True
    for ignore in found_names_in_dags:
        if ignore not in airflowignore_content:
            report.write_all_locations("⚠️ The .airflowignore file does not include", ignore, "but it is present in your dags folder. Please consider if this is intentional or by mistake.")
            all_ignores_found = False
        else:
            report.write_full_report("✅ Found", ignore, "in .airflowignore file on lines:\n\n```")
            report.write_full_report("\n".join([line for line in airflowignore_content.splitlines() if ignore in line]),"\n```")

    if all_ignores_found:
        report.write_all_locations("✅ No immediate issue found with .airflowignore. Note that this check does not cover all potential issues with .airflowignore")

def hello_message():
    print("Hello")

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
                        required=False, help="region, Ex: us-east-1")
    parser.add_argument('--profile', type=validation_profile, default='default',
                        required=False, help="AWS CLI profile, Ex: dev")
    args, _ = parser.parse_known_args()
    ENV_NAME = args.envname
    REGION = args.region
    PARTITION = boto3.session.Session().get_partition_for_region(args.region)
    TOP_LEVEL_DOMAIN = '.amazonaws.com.cn' if PARTITION == 'aws-cn' else '.amazonaws.com'
    PROFILE = args.profile
    try:
        boto3.setup_default_session(profile_name=PROFILE)
        ec2 = boto3.client('ec2', region_name=REGION)
        s3 = boto3.client('s3', region_name=REGION)
        s3control = boto3.client('s3control', region_name=REGION)
        logs = boto3.client('logs', region_name=REGION)
        kms = boto3.client('kms', region_name=REGION)
        cloudtrail = boto3.client('cloudtrail', region_name=REGION)
        ssm = boto3.client('ssm', region_name=REGION)
        iam = boto3.client('iam', region_name=REGION)
        mwaa = boto3.client('mwaa', region_name=REGION)
        sqs = boto3.client('sqs', region_name=REGION)
        cw = boto3.client('cloudwatch', region_name=REGION)

        hello_message()

        report = ReportWriter()

        env, subnets, subnet_ids = prompt_user_and_print_info(ENV_NAME, ec2, mwaa, report)
        check_iam_permissions(env, iam, report)
        check_kms_key_policy(env, kms)
        log_groups = check_log_groups(env, ENV_NAME, logs, cloudtrail, report)
        check_nacl(subnets, subnet_ids, ec2, report)
        check_routes(env, subnets, subnet_ids, ec2, report)
        check_s3_block_public_access(env, s3, s3control, report)
        check_security_groups(env, ec2, report)
        mwaa_services = get_mwaa_utilized_services(ec2, subnets[0]['VpcId'])
        check_connectivity_to_dep_services(env, subnets, ec2, ssm, mwaa_services, report)
        check_celery_sqs_health(env, cw, report)
        check_environment_class_utilization(env, cw, report)
        check_environment_class_dag_count(env, cw, report)
        check_airflow_rest_api(env, mwaa, iam, report)
        check_airflowignore(env, s3, report)
        check_full_dag_run(env, mwaa, s3, report)
        check_for_failing_logs(log_groups, logs, report)

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
