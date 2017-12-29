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
import sys
import sg
import ec2
import sns


def lambda_handler(event, context):
    gd_severity = event['detail']['severity']
    gd_type = event['detail']['type']
    gd_resource = event['detail']['resource']
    gd_resource_type = gd_resource['resourceType']
    gd_resource_role = event['detail']['service']['resourceRole']

    print('gd_severity = {}'.format(gd_severity))
    print('gd_type = {}'.format(gd_type))
    print('gd_resource = {}'.format(gd_resource))
    print('gd_resource_role = {}'.format(gd_resource_role))

    if gd_resource_type == 'Instance' and gd_resource_role == 'ACTOR':
        instance_id = gd_resource['instanceDetails']['instanceId']
        print('instance_id = {}'.format(instance_id))

        if instance_id == 'i-99999999':
            print('No action for sample finding')
            sys.exit(0)

        if gd_severity >= 8.0:
            # Get instance vpc_id
            vpc_id = ec2.get_instance_vpc(instance_id)

            # Get lock down security group for vpc_id
            # If lock down security group does not exist it will be created
            # Lock down group has no ingress or egress rules
            lock_down_security_group = sg.get_lockdown_security_group(vpc_id)

            # Change security group for all instance interfaces
            ec2.lock_down_ec2_instance(instance_id, lock_down_security_group)

            print('instance {} was locked down with security group {}'.format(instance_id, lock_down_security_group))

            message_body = 'instance {} was locked down based on guardduty finding: \n\n {}'.format(instance_id, event)

            sns.publish_sns_email_message(message_body, gd_severity)
