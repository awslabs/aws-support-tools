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
from datetime import timedelta
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, ProfileNotFound
from boto3.session import Session
ENV_NAME = ""
REGION = ""

S3_CHECK_SUCCESS_MSG = 's3 bucket, {bucket_arn}, or account blocks public access ✅'
S3_CHECK_FAILURE_MSG = 's3 bucket, {bucket_arn}, or account does NOT block public access 🚫'


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
    mwaa_regions = session.get_available_regions('mwaa')
    new_regions = ['sa-east-1', 'ap-northeast-2', 'ap-south-1', 'ca-central-1', 'eu-west-2', 'eu-west-3']
    mwaa_regions.extend(new_regions)
    if input_region in mwaa_regions:
        return input_region
    raise argparse.ArgumentTypeError("%s is an invalid REGION value" % input_region)


def validation_profile(profile_name):
    '''
    verify profile name doesn't have path to files or unexpected input
    '''
    if re.match(r"^[a-zA-Z0-9\-]*$", profile_name):
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


def check_iam_permissions(input_env, iam_client):
    '''uses iam simulation to check permissions of the role assigned to the environment'''
    print('### Checking the IAM execution role', input_env['ExecutionRoleArn'], 'using iam policy simulation')
    account_id = get_account_id(input_env)
    # Define actions and resources to be simulated
    actions_resources = [
        {'actions': ['airflow:PublishMetrics'], 'resources': [input_env['Arn']]},
        {'actions': ['s3:GetBucket*', 's3:List*'], 'resources': [input_env['SourceBucketArn']]},
        {'actions': ['s3:GetObject*'], 'resources': [input_env['SourceBucketArn'] +'/*']},
        {'actions': ['logs:CreateLogStream', 'logs:CreateLogGroup', 'logs:PutLogEvents', 'logs:GetLogEvents', 'logs:GetLogGroupFields'], 'resources': ['arn:aws:logs:'+REGION+':'+account_id+':log-group:airflow-'+input_env['Name'] +'-*']},
        {'actions': ['logs:DescribeLogGroups'], 'resources': ['*']},
        {'actions': ['cloudwatch:PutMetricData'], 'resources': ['*']},
        {'actions': ['sqs:ChangeMessageVisibility', 'sqs:DeleteMessage', 'sqs:GetQueueAttributes', 'sqs:GetQueueUrl', 'sqs:ReceiveMessage', 'sqs:SendMessage'], 'resources': ['arn:aws:sqs:'+REGION+':*:airflow-celery-*']}
    ]
    key_resource = input_env['KmsKey'] if "KmsKey" in input_env else 'arn:aws:kms:*:111122223333:key/*'

    # Append KMS actions to the simulation actions list
    for kms_action in [['kms:GenerateDataKey*'], ['kms:Decrypt', 'kms:Encrypt', 'kms:DescribeKey']]:
        src_services = ['sqs', 's3'] if "KmsKey" in input_env else ['sqs']
        for src_service in src_services:
            actions_resources.append({
                'actions': kms_action,
                'resources': [key_resource], 
                'contextEntries': [
                    {
                        'ContextKeyName': 'kms:ViaService',
                        'ContextKeyValues': [
                            src_service + '.' + REGION + '.amazonaws.com'
                        ],
                        'ContextKeyType': 'string'
                    }
                ]
            })
    for simulation in actions_resources:
        eval_results = iam_client.simulate_principal_policy(
            PolicySourceArn=input_env['ExecutionRoleArn'],
            ActionNames=simulation['actions'],
            ResourceArns=simulation['resources'],
            ContextEntries=simulation.get('contextEntries'),
        )['EvaluationResults'] if simulation.get('contextEntries') else iam_client.simulate_principal_policy(
                PolicySourceArn=input_env['ExecutionRoleArn'],
                ActionNames=simulation['actions'],
                ResourceArns=simulation['resources']
            )['EvaluationResults']
        for eval_result in eval_results:
            if eval_result['EvalDecision'] != 'allowed':
                print('Action: {} is not allowed on resource {}. Failed with {} 🚫'.format(eval_result['EvalActionName'], eval_result['EvalResourceName'], eval_result['EvalDecision']))
            else:
                print('Action: {} is allowed on resource {} ✅'.format(eval_result['EvalActionName'], eval_result['EvalResourceName']))

    print('If the policy is denied you can investigate more at ')
    print("https://policysim.aws.amazon.com/home/index.jsp?#roles/" + input_env['ExecutionRoleArn'].split("/")[-1])
    print("")
    print('These simulations are based off of the sample policies here ')
    print('https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json\n')


def prompt_user_and_print_info(input_env_name, ec2_client):
    '''method to get environment, print that information to stdout, and prompt the use to send it to support'''
    print('please send support the following information')
    print('If a case is not opened you may open one here https://console.aws.amazon.com/support/home#/case/create')
    print('Please make sure to NOT include any personally identifiable information in the case\n')
    # get mwaa environment
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mwaa.html#MWAA.Client.get_environment
    mwaa = boto3.client('mwaa', region_name=REGION)
    environment = mwaa.get_environment(
        Name=input_env_name
    )['Environment']
    network_subnet_ids = environment['NetworkConfiguration']['SubnetIds']
    network_subnets = ec2_client.describe_subnets(SubnetIds=network_subnet_ids)['Subnets']
    for key in environment.keys():
        print(key, ': ', environment[key])
    print('VPC: ', network_subnets[0]['VpcId'], "\n")
    return environment, network_subnets, network_subnet_ids


def check_kms_key_policy(input_env, kms_client):
    '''
    check kms key and if its customer managed if it has a policy like this
    https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json
    '''
    if "KmsKey" in input_env:
        print("### Checking the kms key policy and if it includes reference to airflow")
        policy = kms_client.get_key_policy(
            KeyId=env['KmsKey'],
            PolicyName='default'
        )['Policy']
        if "airflow" not in policy and "aws:logs:arn" not in policy:
            print("text 'airflow' and 'logs' do not appear in KMS key policy. Please check KMS key: ",
                  input_env['KmsKey'], "🚫")
            print("for an example resource policy please see this doc: ")
            print("https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html#mwaa-create-role-json \n")
        else:
            print("KMS includes text 'airflow' and 'logs'", "✅")


def check_log_groups(input_env, env_name, logs_client, cloudtrail_client):
    '''check if cloudwatch log groups exists, if not check cloudtrail to see why they weren't created'''
    loggroups = logs_client.describe_log_groups(
        logGroupNamePrefix='airflow-'+env_name
    )['logGroups']
    num_of_enabled_log_groups = sum(
        input_env['LoggingConfiguration'][logConfig]['Enabled'] is True
        for logConfig in input_env['LoggingConfiguration']
    )
    num_of_found_log_groups = len(loggroups)
    print('### Checking if log groups were created successfully...\n')
    if num_of_found_log_groups < num_of_enabled_log_groups:
        print('The number of log groups is less than the number of enabled suggesting an error creating', "🚫")
        print('checking cloudtrail for CreateLogGroup/DeleteLogGroup requests...\n')
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
            print('Found CloudTrail event: ', event)
        print('if events are failing, try creating the log groups manually\n')
    else:
        print("number of log groups match suggesting they've been created successfully", "✅")
    return loggroups

# New functions
# Function to check Network ACLs
def check_network_acls(ec2_client, vpc_id, input_subnet_ids):
    nacls = ec2_client.describe_network_acls(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [vpc_id]
            },
            {
                'Name': 'association.subnet-id',
                'Values': input_subnet_ids
            }
        ]
    )['NetworkAcls']

    result = {
        'ingress': {'final': False, '-1': 'deny', '6': 'deny', '17': 'deny'},
        'egress': {'final': False, '-1': 'deny', '6': 'deny', '17': 'deny'}
    }
    # NACL rules with lowest number take precedence. So, keeping track of last rule number to correctly identify the final result.
    result['ingress']['previousRule'] = {'-1': 32768, '6': 32768, '17': 32768};
    result['egress']['previousRule'] = {'-1': 32768, '6': 32768, '17': 32768};
    for nacl_entry in nacls:
        for nacl in nacl_entry['Entries']:
            traffic_type = "egress" if nacl['Egress'] else "ingress"
            if nacl.get('PortRange'):
                if nacl['PortRange']['From'] and nacl['PortRange']['To']:
                    nacl['PortRange'] = nacl['PortRange']['To'] if nacl['PortRange']['From'] == nacl['PortRange']['To'] else nacl['PortRange']['From'] + '-' + nacl['PortRange']['To']
                else:
                    nacl['PortRange'] = 'ALL'
            else:
                nacl['PortRange'] = 'ALL'

            if nacl['CidrBlock'] == '0.0.0.0/0' and nacl['RuleNumber'] < result[traffic_type]['previousRule'][nacl['Protocol']] and type(nacl['PortRange'] is str):
                result[traffic_type][nacl['Protocol']] = nacl['RuleAction']
                result[traffic_type]['previousRule'][nacl['Protocol']] = nacl['RuleNumber']

    for rule_type in ['ingress', 'egress']:
        if result[rule_type]['-1'] == 'allow' or (result[rule_type]['6'] == 'allow' and result[rule_type['17'] == 'allow']):
            result[rule_type]['final'] = True

    return True if result['ingress'] and result['egress'] else False

# Function to map subnets and route tables
def map_subnets_route_tables(route_tables):
    sub_routes = {}
    for route_table in route_tables:
        sub_routes[route_table['RouteTableId']] = route_table['Routes']
        for association in route_table['Associations']:
            if association['Main'] == True:
                sub_routes['main'] = route_table['RouteTableId']
            else:
                sub_routes[association['SubnetId']] = route_table['RouteTableId']
    return sub_routes

# Function to return route entries for requested subnet ID
def get_subnet_routes(subnet_id, sub_routes):
    if subnet_id in sub_routes:
        return sub_routes[sub_routes[subnet_id]]
    else:
        return sub_routes[sub_routes['main']]

# Function to check and return default route entry from the specified route table
def get_default_route(routes):
    result = {}
    for route in routes:
        if route.get('DestinationCidrBlock') == "0.0.0.0/0":
            result = {
                "defaultRoute": True,
                "natGatewayId": route.get('NatGatewayId'),
                "gatewayId": route.get('GatewayId'),
                "transitGatewayId": route.get('TransitGatewayId')
            }
    return result

# Function to validate if NAT GW has path to Internet
def validate_nat_gw_path(ec2_client, nat_gw_id, requested_subnet, vpc_routes):
    # Get the subnet associated with this NAT GW and check its routes
    nat_subnet_request = ec2_client.describe_nat_gateways(NatGatewayIds=[nat_gw_id])['NatGateways']
    nat_subnet_id = nat_subnet_request[0]['SubnetId']
    if nat_subnet_id == requested_subnet:
        print('NAT Gateway is attached to same subnet. Instead, it should be attached to different i.e. public subnet. 🚫')
    else:
        # Different subnet
        public_route = get_default_route(get_subnet_routes(nat_subnet_id, vpc_routes))
        if public_route['defaultRoute'] and public_route['gatewayId']:
            print('NAT GW ({}) has Internet route: {} -> {} -> {} -> {} ✅'.format(nat_gw_id, requested_subnet, nat_gw_id, nat_subnet_id, public_route['gatewayId']))
        else:
            print('NAT GW ({}) doesn\'t have Internet route 🚫'.format(nat_gw_id))

# Function to analyze routes via Transit Gateway
def check_tgw_route(ec2_client, tgw_id, subnet_az):
    tgw_route_tables = ec2_client.describe_transit_gateway_route_tables(
        Filters=[
                    {
                        'Name': 'transit-gateway-id',
                        'Values': [tgw_id]
                    },
                    {
                        'Name': 'state',
                        'Values': ['available']
                    }
    ])['TransitGatewayRouteTables']
    tgw_routes = ec2_client.search_transit_gateway_routes(
        TransitGatewayRouteTableId=tgw_route_tables[0]['TransitGatewayRouteTableId'],
        Filters=[
                {
                    'Name': 'state',
                    'Values': ['active']
                }
    ])['Routes']
    for route in tgw_routes:
        if route['DestinationCidrBlock'] == '0.0.0.0/0':
            print('{} has default route via {} ({})'.format(tgw_id, route['TransitGatewayAttachments'][0]['ResourceType'], route['TransitGatewayAttachments'][0]['ResourceId']))
            tgw_attachments = ec2_client.describe_transit_gateway_vpc_attachments(
                TransitGatewayAttachmentIds=[route['TransitGatewayAttachments'][0]['TransitGatewayAttachmentId']]
            )['TransitGatewayVpcAttachments']
            tgw_path_subnets = ec2_client.describe_subnets(SubnetIds=tgw_attachments[0]['SubnetIds'])['Subnets']
            tgw_az_subnet = [subnet['SubnetId'] for subnet in tgw_path_subnets if subnet['AvailabilityZone'] == subnet_az][0]
            tgw_egress_vpc_routes = ec2_client.describe_route_tables(Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [route['TransitGatewayAttachments'][0]['ResourceId']]
                }
            ])['RouteTables']
            tgw_sub_routes = map_subnets_route_tables(tgw_egress_vpc_routes)
            tgw_subnet_route = get_default_route(get_subnet_routes(tgw_az_subnet, tgw_sub_routes))
            if tgw_subnet_route['defaultRoute'] and tgw_subnet_route['natGatewayId']:
                print('TGW has default route to NAT GW ({})'.format(tgw_subnet_route['natGatewayId']))
                validate_nat_gw_path(ec2_client, tgw_subnet_route['natGatewayId'], tgw_az_subnet, tgw_sub_routes)
            else:
                print('TGW doesn\'t have default route to Internet')
            
# Function to analyze VPC Endpoints            
def check_vpc_endpoints(ec2_client, vpc_id, input_subnet_ids, input_security_groups):
    tld = "com.amazonaws."
    REGION = 'eu-west-1'
    service_endpoints = [tld + REGION + '.' + srv for srv in ['airflow.api', 'airflow.env', 'airflow.ops', 'sqs', 'ecr.dkr', 'ecr.api', 'kms', 's3', 'monitoring', 'logs']]
    vpc_endpoints = ec2_client.describe_vpc_endpoints(Filters=[
        {
            'Name': 'service-name',
            'Values': service_endpoints
        },
        {
            'Name': 'vpc-id',
            'Values': [vpc_id]
        }
    ])['VpcEndpoints']

    for vpce in vpc_endpoints:
        if vpce['VpcEndpointType'] == 'Interface':
            service = '.'.join(vpce['ServiceName'].split('.')[3:]).upper()
            subnet_match = [subnet_id for subnet_id in vpce['SubnetIds'] if subnet_id in input_subnet_ids]
            security_group_match = [sg_id['GroupId'] for sg_id in vpce['Groups'] if sg_id['GroupId'] in input_security_groups]
            # print('{}: {} : {}'.format(service, subnet_match, security_group_match))

            if len(subnet_match) == 0:
                print('{} VPCE ({}) isn\'t associated with MWAA\'s subnets 🚫'.format(service, vpce['VpcEndpointId']))
            elif len(subnet_match) == 1:
                print('{} VPCE ({}) is only associated with one subnet {} 🚫'.format(service, vpce['VpcEndpointId'], subnet_match[0]))
            
            if len(subnet_match) >= 1 and len(security_group_match) > 0:
                print('{} VPCE ({}) has common subnets and security group(s) as MWAA ✅'.format(service, vpce['VpcEndpointId']))
            elif len(subnet_match) >= 1 and len(security_group_match) == 0:
                if check_vpce_sg_with_env(ec2_client, input_security_groups, vpce['Groups']):
                    print('{} VPCE ({}) SG is allowing MWAA environment\'s SG ✅'.format(service, vpce['VpcEndpointId']))
                else:
                    print('{} VPCE ({}) doesn\'t share MWAA SG nor allows it. 🚫'.format(service, vpce['VpcEndpointId']))
            if not vpce['PrivateDnsEnabled']:
                print('{} VPCE ({}) doesn\'t have Private DNS Enabled. 🚫'.format(service, vpce['VpcEndpointId']))

# Function to check if specified SG allows MWAA
def check_vpce_sg_with_env(ec2_client, env_sg_ids, vpce_sgs):
    result = False
    vcpe_sg_ids = [sg_id['GroupId'] for sg_id in vpce_sgs]
    groups = ec2_client.describe_security_groups(
        GroupIds=vcpe_sg_ids
    )['SecurityGroups']
    for security_group in groups:
        for ip_permission in security_group['IpPermissions']:
            # If allows all traffic or HTTPS from env's SG
            if ip_permission['IpProtocol'] == '-1' or (ip_permission['IpProtocol'] == 'tcp' and (ip_permission['ToPort'] and (ip_permission['ToPort'] == '443' or (ip_permission['FromPort'] == 0 and ip_permission['ToPort'] == 65535)))):
                for group_pair in ip_permission['UserIdGroupPairs']:
                    if group_pair['GroupId'] in env_sg_ids:
                        result = True
    return result
# End of new functions

def check_routes(input_env, input_subnets, input_subnet_ids, ec2_client):
    '''
    method to check and make sure routes have access to the internet if public and subnets are private
    '''
    print('='*15 + ' Network Analysis ' + '='*15)
    vpc_id = input_subnets[0]['VpcId']
    # vpc should be the same so I just took the first one
    routes = ec2_client.describe_route_tables(Filters=[
            {
                'Name': 'vpc-id',
                'Values': [vpc_id]
            }
    ])

    subnet_routes = map_subnets_route_tables(routes['RouteTables'])
    for subnet_id in input_subnet_ids:
        subnet_az = [subnet['AvailabilityZone'] for subnet in input_subnets if subnet['SubnetId'] == subnet_id][0]
        print('Subnet: {} (AZ: {})'.format(subnet_id, subnet_az))
        if check_network_acls(ec2_client, vpc_id, input_subnet_ids):
            print('NACL is allowing both ingress and egress. Manually review full NACLs for confirmation.')
        else:
            print('NACL isn\'t allowing both ingress and egress. Manually review full NACLs for confirmation.')
        
        default_route = get_default_route(get_subnet_routes(subnet_id, subnet_routes))
        if default_route['defaultRoute'] and default_route['natGatewayId']:
            validate_nat_gw_path(ec2_client, default_route['natGatewayId'], subnet_id, subnet_routes)
        elif default_route['defaultRoute'] and default_route['gatewayId']:
            print('Subnet has default route to {}, so cannot reach Internet 🚫'.format(default_route['gatewayId']))
        elif default_route['defaultRoute'] and default_route['transitGatewayId']:
            print('Subnet has default route to {}'.format(default_route['transitGatewayId']))
            check_tgw_route(ec2_client, default_route['transitGatewayId'], subnet_az)
        else:
            print('Subnet has no default route.')
        print('-'*40)

    # For VPCE Analysis
    check_vpc_endpoints(ec2_client, vpc_id, input_subnet_ids, input_env['NetworkConfiguration']['SecurityGroupIds'])
    print('='*15 + ' End of Network Analysis ' + '='*15)
    print('')

def _check_access_blocked(block_config_type, client, **request_kwargs):
    '''
    Checks whether public access is blocked for <block_config_type> (either
    bucket or account) using the client and args passed in.
    '''
    print('Checking if public access is blocked at the {config_type} level'.format(config_type=block_config_type))
    try:
        public_access_block = client.get_public_access_block(**request_kwargs)
    except ClientError as client_error:
        # The same client error is thrown for both account level and bucket level configs
        print('The {config_type} level access block config is not set'.format(config_type=block_config_type))
        if client_error.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
            # If the config isn't set then act as if it's public
            return False
        # if it's any other exception scenario raise so that the user is notified
        raise

    # If we successfully got a config, check if public access is blocked or not
    return public_access_block['PublicAccessBlockConfiguration']['BlockPublicAcls']

def check_s3_block_public_access(input_env, s3_client, s3_control_client):
    '''check s3 bucket or account and make sure "block public access" is enabled'''
    print("### Verifying 'block public access' is enabled on the s3 bucket or account...")
    account_id = get_account_id(input_env)
    bucket_arn = input_env['SourceBucketArn']
    bucket_name = bucket_arn.split(':')[-1]
    public_access_block = None

    if any([_check_access_blocked('bucket', s3_client, Bucket=bucket_name),
            _check_access_blocked('account', s3_control_client, AccountId=account_id)]):
        print(S3_CHECK_SUCCESS_MSG.format(bucket_arn=bucket_arn))
    else:
        print(S3_CHECK_FAILURE_MSG.format(bucket_arn=bucket_arn))


def check_security_groups(input_env, ec2_client):
    '''
    check MWAA environment's security groups for:
        - have at least 1 rule
        - checks ingress to see if sg allows itself
        - egress is checked by SSM document for 443 and 5432
    '''
    print("")
    security_groups = input_env['NetworkConfiguration']['SecurityGroupIds']
    groups = ec2_client.describe_security_groups(
        GroupIds=security_groups
    )['SecurityGroups']
    # have a sanity check on ingress and egress to make sure it allows something
    print('### Trying to verifying ingress on security groups...')
    valid = True
    for security_group in groups:
        ingress = security_group['IpPermissions']
        egress = security_group['IpPermissionsEgress']
        if not ingress and not egress:
            print('ingress and egress for security group: ', security_group['GroupId'], ' requires at least one rule',
                  "🚫")
            valid = False
            break
        elif not ingress:
            print('ingress for security group: ', security_group['GroupId'], ' requires at least one rule', "🚫")
            valid = False
            break
        elif not egress:
            print('egress for security group: ', security_group['GroupId'], ' requires at least one rule', "🚫")
            break
        # check security groups to ensure port at least the same security group or everything is allowed ingress
        for rule in ingress:
            if rule['IpProtocol'] == "-1":
                if rule['UserIdGroupPairs'] and not (
                    any(x['GroupId'] == security_group['GroupId'] for x in rule['UserIdGroupPairs'])
                ):
                    valid = False
                    break
    if valid:
        print("ingress for security groups have at least 1 rule to allow itself", "✅", "\n")
    else:
        print("ingress for security groups do not have at least 1 rule to allow itself", "🚫", "\n")


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


def check_connectivity_to_dep_services(input_env, input_subnets, ec2_client, ssm_client):
    '''
    uses ssm document AWSSupport-ConnectivityTroubleshooter to check connectivity between MWAA's enis
    and a list of services. More information on this document can be found here
    https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-awssupport-connectivitytroubleshooter.html
    '''
    print("### Testing connectivity to the following service endpoints from MWAA enis...")
    vpc = subnets[0]['VpcId']
    security_groups = input_env['NetworkConfiguration']['SecurityGroupIds']
    tld = '.amazonaws.com'
    mwaa_srvs = ['api.airflow', 'env.airflow', 'ops.airflow', 'sqs', 'test.dkr.ecr', 'api.ecr', 'kms', 's3', 'monitoring', 'logs']
    mwaa_utilized_services = [{"service": srv + '.' + REGION + tld, "port": "443"} for srv in mwaa_srvs]
    for service in mwaa_utilized_services:
        # retry 5 times for just one of the enis the service uses
        for i in range(0, 5):
            try:
                # get ENIs used by MWAA
                enis = get_enis(subnet_ids, vpc, security_groups)
                if not enis:
                    print("no enis found for MWAA, exiting test for ", service['service'])
                    print("please try accessing the airflow UI and then try running this script again")
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
                    print('Testing connectivity between eni', eni, "with private ip of",
                          interface_ip, "and", service['service'], "on port", service['port'])
                    print("Please follow this link to view the results of the test:")
                    print("https://console.aws.amazon.com/systems-manager/automation/execution/" + ssm_execution_id +
                          "?REGION=" + REGION + "\n")
                    break
            except ClientError as client_error:
                print('Attempt', i, 'Encountered error', client_error.response['Error']['Message'], ' retrying...')
    print("")


def check_for_failing_logs(loggroups, logs_client):
    '''look for any failing logs from CloudWatch in the past hour'''
    print("### Checking CloudWatch logs for any errors less than 1 hour old")
    now = int(time.time() * 1000)
    past_day = now - 3600000
    print('Found the following failing logs in cloudwatch: ')
    for log in loggroups:
        events = logs_client.filter_log_events(
            logGroupName=log['logGroupName'],
            startTime=past_day,
            endTime=now,
            filterPattern='?ERROR ?Error ?error ?traceback ?Traceback ?exception ?Exception ?fail ?Fail'
        )['events']
        events = sorted(events, key=lambda i: i['timestamp'])
        print('Log group: ', log['logGroupName'])
        for event in events:
            print(str(event['timestamp']) + " " + event['message'], end='')


def print_err_msg(c_err):
    '''short method to handle printing an error message if there is one'''
    print('Error Message: {}'.format(c_err.response['Error']['Message']))
    print('Request ID: {}'.format(c_err.response['ResponseMetadata']['RequestId']))
    print('Http code: {}'.format(c_err.response['ResponseMetadata']['HTTPStatusCode']))


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
        env, subnets, subnet_ids = prompt_user_and_print_info(ENV_NAME, ec2)
        check_iam_permissions(env, iam)
        check_kms_key_policy(env, kms)
        log_groups = check_log_groups(env, ENV_NAME, logs, cloudtrail)
        # check_nacl(subnets, subnet_ids, ec2)
        check_routes(env, subnets, subnet_ids, ec2)
        check_s3_block_public_access(env, s3, s3control)
        # check_security_groups(env, ec2)
        # mwaa_services = get_mwaa_utilized_services(ec2, subnets[0]['VpcId'])
        check_connectivity_to_dep_services(env, subnets, ec2, ssm)
        check_for_failing_logs(log_groups, logs)
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
    except ProfileNotFound as profile_not_found:
        print('profile', PROFILE, 'does not exist, please doublecheck the profile name')
    except IndexError as error:
        print("Found index error suggesting there are no ENIs for MWAA")
        print("Error:", error)