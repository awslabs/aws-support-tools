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

region = 'us-west-2'
alert_threshold = 80
sns_topic_arn = 'arn:aws:sns:us-west-2:1111122222:MyTopic'


def publish_notification(topic_arn, message, subject):
    sns_client = boto3.client('sns', region_name=region)
    sns_response = sns_client.publish(TopicArn=topic_arn, Message=message, Subject=subject, MessageStructure='string')
    if sns_response:
        return 'Notification published successfully. Message id %s' % (sns_response['MessageId'])
    else:
        return 'Failed to publish notification.'


def check_quota():
    ses_client = boto3.client('ses', region_name=region)
    response = ses_client.get_send_quota()
    if response:
        daily_quota = response['Max24HourSend']
        total_sent = response['SentLast24Hours']
        threshold = total_sent / daily_quota * 100
        if threshold > alert_threshold:
            # Quota over threshold. Alert using SNS
            message = 'Daily sending limit threshold of %d%% has been reached.' % threshold
            publish_result = publish_notification(sns_topic_arn, message, 'SES daily quota warning')
            return message + ' ' + publish_result
        else:
            return 'Sending quota within threshold.'
    else:
        return 'Error occurred while getting daily send quota.'


def lambda_handler(event, context):
    return check_quota()


if __name__ == "__main__":
    result = check_quota()
    print(result)
