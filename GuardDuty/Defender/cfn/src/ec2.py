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

# AWS_DEFAULT_REGION is available during lambda execution to get current region
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

client = boto3.client('ec2', region_name=AWS_DEFAULT_REGION)


def set_network_interface_security_group(interface_id, security_group):
    response = client.modify_network_interface_attribute(
        Groups=[
            security_group,
        ],
        NetworkInterfaceId=interface_id
    )


def describe_ec2_instance(instance_id):
    response = client.describe_instances(
        InstanceIds=[
            instance_id,
        ]
    )
    return response['Reservations'][0]['Instances'][0]


def get_instance_vpc(instance_id):
    instance = describe_ec2_instance(instance_id)
    return instance['VpcId']


def lock_down_ec2_instance(instance_id, lock_down_security_group):
    instance = describe_ec2_instance(instance_id)

    for interface in instance['NetworkInterfaces']:
        interface_id = interface['NetworkInterfaceId']
        set_network_interface_security_group(interface_id, lock_down_security_group)
        print('Setting inteface {} security group to {}'.format(interface_id, lock_down_security_group))
