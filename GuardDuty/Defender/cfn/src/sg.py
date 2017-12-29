"""Created by: David Pigliavento"""

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import boto3
import os

SECURITY_GROUP_NAME = 'guard-duty-lock-down'
SECURITY_GROUP_DESCRIPTION = 'restricts inbound/outbound access for compromised instance'

# AWS_DEFAULT_REGION is available during lambda execution to get current region
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

client = boto3.client('ec2', region_name=AWS_DEFAULT_REGION)


def describe_security_group(name, vpc_id):
    response = client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-name',
                'Values': [
                    name,
                ]
            },
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            }
        ]
    )

    if len(response['SecurityGroups'])  != 1:
        return None

    return response['SecurityGroups'][0]


def create_security_group(description, name, vpc_id):
    response = client.create_security_group(
        Description=description,
        GroupName=name,
        VpcId=vpc_id
    )
    group_id = response['GroupId']

    return group_id


def revoke_security_group_egress(security_group):
    group_id = security_group['GroupId']
    ip_permissions = security_group['IpPermissionsEgress']

    response = client.revoke_security_group_egress(
        GroupId=group_id,
        IpPermissions=ip_permissions
    )


def get_lockdown_security_group(vpc_id):
    lock_down_security_group = describe_security_group(SECURITY_GROUP_NAME, vpc_id)

    if lock_down_security_group == None:
        print('Creating security group {}'.format(SECURITY_GROUP_NAME))

        group_id = create_security_group(SECURITY_GROUP_DESCRIPTION, SECURITY_GROUP_NAME, vpc_id)
        lock_down_security_group = describe_security_group(SECURITY_GROUP_NAME, vpc_id)
        revoke_security_group_egress(lock_down_security_group)

        print('Created security group {}'.format(group_id))

    return lock_down_security_group['GroupId']
