#!/usr/bin/env python

# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

__author__ = 'Said Ali Samed'

no_shut_keyword = 'noshut'


def get_regions():
    client = boto3.client('ec2')
    regions = client.describe_regions()
    return regions['Regions']


def get_instances(ec2_client):
    response = ec2_client.describe_instances()
    instance_list = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_list.append(instance)
    return instance_list


def shutdown_instance(region, instance_id):
    ec2 = boto3.resource('ec2', region_name=region)
    instance = ec2.Instance(instance_id)
    response = instance.stop()
    if response:
        return "Successfully shutdown instance {}\n".format(instance_id)
    else:
        return "Failed to shutdown instance {}\n".format(instance_id)


def look_for_instances():
    output = ''
    for region in get_regions():
        region_name = region['RegionName']
        ec2_client = boto3.client('ec2', region_name=region_name)
        output += 'Looking for running instances in {}\n'.format(region_name)
        for instance in get_instances(ec2_client):
            instance_id = instance['InstanceId']
            if instance['State']['Name'] == 'running':
                shutdown = False
                for tag in instance['Tags']:
                    if any(no_shut_keyword in value for value in tag.itervalues()):
                        shutdown = False
                        break
                    else:
                        shutdown = True
                if shutdown:
                    output += 'Shutting down running instance {}\n'.format(instance_id)
                    output += shutdown_instance(region_name, instance_id)
    return output


def lambda_handler(event, context):
    return look_for_instances()


if __name__ == "__main__":
    result = look_for_instances()
    print(result)
