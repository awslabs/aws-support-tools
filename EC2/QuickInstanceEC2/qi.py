#!/usr/bin/env python

# Copyright 2015-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

__version__ = '1.0'
__date__ = '01 August 2015'
__author__ = 'Said Ali Samed'

import getopt
import sys
import json
from os.path import expanduser
from time import sleep
import datetime

try:
    import boto3
    from botocore.exceptions import NoCredentialsError
except:
    print('Python module \'boto3\' missing. Install by running \'sudo pip install boto3\'')
    print('If pip is not installed, please install from https://pip.pypa.io/en/latest/installing.html')
    exit(2)

conf_file = expanduser('~') + '/.qi.conf'
script_name = 'qi.py'
os_list = tuple('amazon-linux nat-instance ubuntu redhat-linux windows-2012 windows-2008'.split())
redhat_account = '309956199498'
ubuntu_account = '099720109477'


def main():
    option_list = 'region= type= role= key= volume= ami= bootstrap='.split()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], '', option_list)
    except:
        usage()
        sys.exit(2)
    if len(args) > 0:
        if args[0] == 'configure':
            configure()
        elif args[0] in os_list:
            try:
                launch(opts, args[0])
            except NoCredentialsError:
                advise_credentials()
            except:
                troubleshoot()
        elif args[0] == 'help':
            usage()
        else:
            usage()
    else:
        usage()


def usage():
    print("""
Description: Launches, deploys application and terminates AWS ec2 instances quickly using CloudFormation.

Usage: ./%s [os|help|configure] [--region|--type|--role|--key|--volume|--ami|--bootstrap]

  os          : amazon-linux | nat-instance | redhat-linux | ubuntu | windows-2012 | windows-2008
  help        : prints this help
  configure   : configures quick instance.

  --region    : name of AWS region
  --type      : ec2 instance type
  --role      : ec2 instance role name
  --key       : ssh key name
  --volume    : ec2 instance root volume size in GB
  --ami       : ec2 instance ami id for the specified AWS region
  --bootstrap : any shell command to configure instance at boot

Examples:
  ./%s amazon-linux                              : Launch an Amazon Linux ec2 instance
  ./%s configure                                 : Configure qi
  ./%s ubuntu --bootstrap "<shell commands>"     : Bootstrap instance with shell commands

""" % (script_name, script_name, script_name, script_name))


def configure():
    prompts = [
        {'question': 'Enter AWS region name or number: ', 'id': 'region', 'fetch': True},
        {'question': 'Default instance type [t2.micro]: ', 'id': 'type', 'fetch': False},
        {'question': 'Instance profile name or number: ', 'id': 'role', 'fetch': True},
        {'question': 'SSH key pair name  or number for Linux instances: ', 'id': 'key', 'fetch': True},
        {'question': 'SSH key pair name or number for Windows instances: ', 'id': 'key-windows', 'fetch': True},
        {'question': 'Default root volume size in GB [30]: ', 'id': 'volume', 'fetch': False},
        {'question': 'AMI ID or number for Amazon Linux: ', 'id': 'ami-amazon-linux', 'fetch': True},
        {'question': 'AMI ID or number for NAT instance: ', 'id': 'ami-nat-instance', 'fetch': True},
        {'question': 'AMI ID or number for Ubuntu: ', 'id': 'ami-ubuntu', 'fetch': True},
        {'question': 'AMI ID or number for Redhat Linux: ', 'id': 'ami-redhat-linux', 'fetch': True},
        {'question': 'AMI ID or number for Windows 2012: ', 'id': 'ami-windows-2012', 'fetch': True},
        {'question': 'AMI ID or number for Windows 2008: ', 'id': 'ami-windows-2008', 'fetch': True}
    ]
    config = {}
    for prompt in prompts:
        prompt_index = prompts.index(prompt)
        resource_list = []
        if prompt_index == 0:
            resource_list = get_regions()
            display_list(resource_list, 'RegionName')
        elif prompt_index == 2:
            resource_list = get_roles()
            display_list(resource_list, 'RoleName')
        elif prompt_index in [3, 4]:
            resource_list = get_key_pairs(config['region'])
            display_list(resource_list, 'KeyName')
        elif prompt_index in [6, 7]:
            resource_list = get_images(config['region'], ['amazon'], False)
            display_list(resource_list, 'ImageId', 'CreationDate', 'Description')
        elif prompt_index in [8]:
            resource_list = get_images(config['region'], [ubuntu_account], False)
            display_list(resource_list, 'ImageId', 'CreationDate', 'Name')
        elif prompt_index in [9]:
            resource_list = get_images(config['region'], [redhat_account], False)
            display_list(resource_list, 'ImageId', 'CreationDate', 'Name')
        elif prompt_index in [10, 11]:
            resource_list = get_images(config['region'], ['amazon'], True)
            display_list(resource_list, 'ImageId', 'CreationDate', 'Description')
        else:
            resource_list = []
        while True:
            if sys.version_info[0] < 3:
                response = raw_input(prompt['question'])
            else:
                response = input(prompt['question'])
            if prompt_index in [1, 5]:  # allow blank entry for instance type and volume size
                break
            if response.strip():
                if is_number(response) and prompt['fetch']:
                    if int(response)-1 >= 0 and int(response)-1 < len(resource_list):
                        break
                else:
                    break
        if is_number(response):
            if prompt_index == 0:
                config[prompt['id']] = resource_list[int(response)-1]['RegionName']
            elif prompt_index == 2:
                config[prompt['id']] = resource_list[int(response)-1]['RoleName']
            elif prompt_index in [3, 4]:
                config[prompt['id']] = resource_list[int(response)-1]['KeyName']
            elif prompt_index == 5:
                config[prompt['id']] = response.strip()
            elif prompt_index in [6, 7]:
                config[prompt['id']] = resource_list[int(response)-1]['ImageId']
            elif prompt_index in [8]:
                config[prompt['id']] = resource_list[int(response)-1]['ImageId']
            elif prompt_index in [9]:
                config[prompt['id']] = resource_list[int(response)-1]['ImageId']
            elif prompt_index in [10, 11]:
                config[prompt['id']] = resource_list[int(response)-1]['ImageId']
        else:
            if prompt_index == 1 and not response.rstrip():
                config[prompt['id']] = 't2.micro'  # default to t2.micro if blank entry
            elif prompt_index == 5 and not response.rstrip():
                config[prompt['id']] = 30  # default to 30GB for volume if left blank
            else:
                config[prompt['id']] = response.strip()
    json.dump(config, open(conf_file, 'w'))


def load_conf():
    try:
        saved_conf = json.load(open(conf_file))
    except:
        print('Quick instance not configured. Please run \'./%s configure\'.' % script_name)
        sys.exit(2)
    return saved_conf


def get_instance_properties(opts, stack_name):
    saved_conf = load_conf()
    for opt in opts:
        # Add/replace saved conf with user supplied options
        if opt[0][2:] == 'bootstrap':
            saved_conf[opt[0][2:]] = opt[1]
        if opt[0][2:] == 'ami':
            saved_conf['ami-' + stack_name] = opt[1]
        if opt[0][2:] in saved_conf:
            saved_conf[opt[0][2:]] = opt[1]
            if opt[0][2:] == 'key': saved_conf['key-windows'] = opt[1]
    # Configure dictionary based on stack type
    if stack_name in ['amazon-linux', 'nat-instance']:
        saved_conf['device'] = '/dev/xvda'
    else:
        saved_conf['device'] = '/dev/sda1'
    if 'windows' in stack_name:
        saved_conf['user'] = 'Administrator'
        saved_conf['key'] = saved_conf['key-windows']
    elif 'ubuntu' in stack_name:
        saved_conf['user'] = 'ubuntu'
    else:
        saved_conf['user'] = 'ec2-user'
    saved_conf['ami'] = saved_conf['ami-' + stack_name]
    if not 'bootstrap' in saved_conf:
        saved_conf['bootstrap'] = ''
    return saved_conf


def launch(opts, stack_name):
    prop = get_instance_properties(opts, stack_name)
    region = prop['region']
    print('Launching instance %s... ' % stack_name)
    output = create_stack(stack_name, get_template(prop, stack_name), region)
    if output == 'STACK_ALREADY_EXISTS':
        status = get_stack_state(stack_name, region).stack_status
        if status == 'CREATE_COMPLETE':
            get_instance_detail(get_instance_id(stack_name, region), stack_name, prop['key'], prop['user'], region)
        if sys.version_info[0] < 3:
            prompt = raw_input('Instance \'%s\' already exists. Would you like to terminate it? ' % stack_name)
        else:
            prompt = input('Instance \'%s\' already exists. Would you like to terminate it? ' % stack_name)
        if prompt in ['Y', 'y']:
            delete_stack(stack_name, region)
    elif 'arn:aws:cloudformation' in output:
        while True:
            status = get_stack_state(stack_name, region).stack_status
            if status == 'CREATE_COMPLETE':
                print('\nInstance created successfully.')
                get_instance_detail(get_instance_id(stack_name, region), stack_name, prop['key'], prop['user'], region)
                break
            elif status == 'CREATE_FAILED' or 'ROLLBACK' in status:
                print('\nFailed to create instance \'%s\'.' % stack_name)
                get_stack_events(stack_name, region)
                break
            sys.stdout.write('.')
            sys.stdout.flush()
            sleep(5)


def create_stack(stack_name, template, region):
    try:
        cf = boto3.client('cloudformation', region_name=region)
        response = cf.create_stack(StackName=stack_name, TemplateBody=template)
    except:
        return 'STACK_ALREADY_EXISTS'
    if 'StackId' in response:
        return response['StackId']
    else:
        return


def delete_stack(stack_name, region):
    try:
        cf = boto3.client('cloudformation', region_name=region)
        print('Terminating %s...' % stack_name)
        response = cf.delete_stack(StackName=stack_name)
    except:
        print('Failed to terminate %s.' % stack_name)
        get_stack_events(stack_name, region)
        return response
    return response


def get_stack_state(stack_name, region):
    try:
        cf = boto3.resource('cloudformation', region_name=region)
        stack = cf.Stack(stack_name)
    except:
        print('Failed to get stack state.')
        return
    return stack


def get_stack_events(stack_name, region):
    try:
        cf = boto3.resource('cloudformation', region_name=region)
        stack = cf.Stack(stack_name)
        for event in stack.events.all():
            if event.resource_status in ['CREATE_FAILED', 'ROLLBACK_IN_PROGRESS'] and event.resource_status_reason:
                print(event.resource_status_reason)
        print('For more detail please review error in CloudFormation console.')
    except:
        print('Failed to get stack events.')


def get_instance_id(stack_name, region):
    state = get_stack_state(stack_name, region)
    stack_outputs = state.outputs
    if stack_outputs and len(stack_outputs) > 0 and stack_outputs[0]['OutputKey'] == 'InstanceId':
        return stack_outputs[0]['OutputValue']
    else:
        return


def get_instance_ip(instance_id, region):
    try:
        ec2 = boto3.resource('ec2', region_name=region)
        instance = ec2.Instance(instance_id)
    except:
        print("Failed to get instance ip address.")
        return
    return instance.public_ip_address


def get_instance_detail(instance_id, stack_name, key, username, region):
    print('Getting instance details... ')
    instance_ip = get_instance_ip(instance_id, region)
    print('%s -> %s\n' % (instance_id, instance_ip))
    if 'windows' in stack_name:
        print('RDP to the instance by decrypting Administrator password in management console.\n')
        print('Paste the following command in Start -> Run:')
        print('mstsc /v:%s\n' % instance_ip)
    else:
        print('SSH into the instance using command:')
        print('ssh -i ~/.ssh/%s.pem %s@%s\n' % (key, username, instance_ip))


def get_template(prop, stack_name):
    security_group = {}
    security_group['Type'] = 'AWS::EC2::SecurityGroup'
    security_group['Properties'] = {}
    security_group['Properties']['GroupDescription'] = 'Enable required inbound ports.'
    ingress_rules = []
    login_port = '3389' if 'windows' in stack_name else '22'
    ingress_rules.append({"IpProtocol": "tcp", "FromPort": login_port, "ToPort": login_port, "CidrIp": "0.0.0.0/0"})
    ingress_rules.append({"IpProtocol": "tcp", "FromPort": "80", "ToPort": "80", "CidrIp": "0.0.0.0/0"})
    ingress_rules.append({"IpProtocol": "tcp", "FromPort": "443", "ToPort": "443", "CidrIp": "0.0.0.0/0"})
    security_group['Properties']['SecurityGroupIngress'] = ingress_rules
    ec2_instance = {}
    ec2_instance['Type'] = 'AWS::EC2::Instance'
    ec2_instance['Properties'] = {}
    ec2_instance['Properties']['BlockDeviceMappings'] = [
        {'DeviceName': prop['device'],'Ebs': {'VolumeSize': prop['volume'], 'VolumeType': 'gp2'}}
    ]
    ec2_instance['Properties']['ImageId'] = prop['ami']
    ec2_instance['Properties']['InstanceType'] = prop['type']
    ec2_instance['Properties']['KeyName'] = prop['key']
    ec2_instance['Properties']['IamInstanceProfile'] = prop['role']
    ec2_instance['Properties']['SecurityGroupIds'] = [{'Ref': 'InstanceSecurityGroup'}]
    ec2_instance['Properties']['Tags'] = [{'Key': 'Name', 'Value': stack_name}]
    ec2_instance['Properties']['UserData'] = {'Fn::Base64': '#!/bin/bash\n' + prop['bootstrap']}
    resources = {}
    resources['InstanceSecurityGroup'] = security_group
    resources['Ec2Instance'] = ec2_instance
    outputs = {}
    outputs['InstanceId'] = {}
    outputs['InstanceId']['Value'] = {'Ref': 'Ec2Instance'}
    outputs['InstanceId']['Description'] = 'Instance Id of newly created instance.'
    template = {}
    template['AWSTemplateFormatVersion'] = '2010-09-09'
    template['Description'] = 'Launched using quick instance script'
    template['Resources'] = resources
    template['Outputs'] = outputs
    return json.dumps(template)


def advise_credentials():
    print('AWS credentials not found. You can create the credential file in ~/.aws/credentials')
    print('Follow http://boto3.readthedocs.org/en/latest/guide/quickstart.html#configuration for details.')


def troubleshoot():
    print('\nAn error occurred while launching instance. ' +
          'Please ensure you have entered correct settings during configuration.')
    print('Run \'./%s configure\' to reconfigure or specify correct options as parameters.' % script_name)


def get_regions():
    try:
        client = boto3.client('ec2')
        regions = client.describe_regions()
        return regions['Regions']
    except:
        return


def get_roles():
    try:
        iam = boto3.client('iam')
        roles = iam.list_roles()
        return roles['Roles']
    except:
        return


def get_key_pairs(region):
    try:
        client = boto3.client('ec2', region_name=region)
        keys = client.describe_key_pairs()
        return keys['KeyPairs']
    except:
        return


def get_images(region, owners=[], windows=False):
    try:
        client = boto3.client('ec2', region_name=region)
        images = client.describe_images(Owners=owners, Filters=[
                {'Name': 'architecture', 'Values': ['x86_64']},
                {'Name': 'block-device-mapping.volume-type', 'Values': ['gp2']},
                {'Name': 'image-type', 'Values': ['machine']},
                {'Name': 'virtualization-type', 'Values': ['hvm']},
                {'Name': 'platform', 'Values': ['windows']} if windows else {},
                ])
        image_list = []
        filter_keyword = 'Microsoft Windows Server' if windows else 'Amazon Linux'
        for image in images['Images']:
            if 'amazon' in owners:
                if 'Description' in image and filter_keyword in image['Description']:
                    if windows and any(keyword not in image['Description'] for keyword in ['English', 'Base']):
                        continue
                    if windows: image['Description'] = image['Description'].replace('AMI provided by Amazon', '')
                    image_list.append(image)
            elif redhat_account in owners:
                image_list.append(image)
            elif ubuntu_account in owners:
                image_list.append(image)
        image_list.sort(key=lambda x: datetime.datetime.strptime(x['CreationDate'], '%Y-%m-%dT%H:%M:%S.000Z'))
        return image_list
    except:
        return


def display_list(items, key_one, key_two=None, key_three=None):
    if type(items) is not list: return
    for item in items:
        print('%i. %s  %s %s' % (items.index(item) + 1, item[key_one], item[key_two] if key_two else '',
                                 item[key_three] if key_three else ''))


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
