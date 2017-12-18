'''
Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS"
BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under the License.
'''

from __future__ import print_function

print('Loading function')

import json, boto3, re

def lambda_handler(event, context):
    # print("Received event: \n" + json.dumps(event))

    # If CreateTags failed nothing to do
    if 'errorCode' in event['detail']:
        print('CreateTags failed with error code {} and error message "{}", nothing to do.'
            .format(event['detail']['errorCode'], event['detail']['errorMessage']))
        return

    region = event['detail']['awsRegion']
    ec2 = boto3.client('ec2', region_name=region)

    instance_ids = []
    is_instance = re.compile('i-[0-9a-f]+')
    # Run instances may create several instances, then the event will contain 
    # several instances
    for item in event['detail']['requestParameters']['resourcesSet']['items']:
        if is_instance.match(item['resourceId']):
            instance_ids.append(item['resourceId'])
    
    # check if we were tagging any instances
    if len(instance_ids) == 0:
        return

    tags = []
    for tag in event['detail']['requestParameters']['tagSet']['items']:
        tags.append({
            'Key': tag['key'],
            'Value': tag['value']
        })

    # If the number of created instances then describe instances may be paginated
    paginator = ec2.get_paginator('describe_instances')
    instances_iterator = paginator.paginate(
        DryRun=False,
        InstanceIds=instance_ids
    )

    for page in instances_iterator:
        resources = []
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                for eni in instance['NetworkInterfaces']:
                    resources.append(eni['NetworkInterfaceId'])

                for volume in instance['BlockDeviceMappings']:
                    if 'Ebs' in volume:
                        resources.append(volume['Ebs']['VolumeId'])

        print("Tagging resorces for instance ids:\n[{}]".format(', '.join(instance_ids)))
        print("Resources to be tagged:\n[{}]".format(', '.join(resources)))

        ec2.create_tags(
            DryRun=False,
            Resources=resources,
            Tags=tags
        )

    return
