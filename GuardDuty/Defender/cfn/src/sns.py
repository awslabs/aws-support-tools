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

# SNS topic used to send notification
SNS_TOPIC = os.getenv("SNS_TOPIC")
# AWS_DEFAULT_REGION is available during lambda execution to get current region
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

client = boto3.client('sns', region_name=AWS_DEFAULT_REGION)


def publish_sns_email_message(message_body, severity):

    if severity >= 8.0:
        severity = 'High'

    response = client.publish(
        TopicArn=SNS_TOPIC,
        Message=message_body,
        Subject='GuardDuty Finding: {} Severity'.format(severity),
        MessageStructure='string'
    )
