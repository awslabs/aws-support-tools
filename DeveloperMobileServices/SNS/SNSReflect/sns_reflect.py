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

from __future__ import print_function

import json
import os

import boto3
import botocore

__author__ = 'Said Ali Samed'

# Get Lambda environment variables
region = os.environ['REGION']
topic = os.environ['TOPIC']

# Global variables
sns = boto3.client('sns', region_name=region)


# Publishes to a specified SNS topic
def sns_publish(topic_arn, subject, message):
    try:
        response = sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        if not isinstance(response, dict):  # log failed requests only
            print('%s, %s' % (topic_arn, response))
        else:
            print(response['ResponseMetadata'])
    except botocore.exceptions.ClientError as e:
        print('%s, %s, %s' % (
            topic_arn,
            ', '.join("%s=%r" % (k, v) for (k, v) in e.response['ResponseMetadata'].iteritems()),
            e.message))


# Entry point for lambda execution
def lambda_handler(event, context):
    try:
        for record in event['Records']:
            type = record['Sns']['Type']
            subject = record['Sns']['Subject']
            message = record['Sns']['Message']
            if type == 'Notification':
                sns_publish(topic, subject, message)
    except Exception as e:
        print(e.message + ' Aborting...')
        raise e


# Default entry point outside lambda
if __name__ == "__main__":
    # Test load a sample json event during development testing
    json_content = json.loads(open('sns_event.json', 'r').read())
    lambda_handler(json_content, None)
