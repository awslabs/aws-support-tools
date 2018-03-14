#!bin/bash
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

#Get the instance ID from the local metadata
id=$(curl http://169.254.169.254/latest/meta-data/instance-id)

#Get the volume ID's attached to the instance
volumes=$(aws ec2 describe-instances --instance-ids $id --region=us-east-2 --query 'Reservations[*].Instances[*].BlockDeviceMappings[*].Ebs.VolumeId' --output text)

#Get the name of the AutoScaling Group this instance is a part of
asg=$(aws autoscaling describe-auto-scaling-instances --instance-ids $id --region=us-east-2 --query 'AutoScalingInstances[*].AutoScalingGroupName' --output text)

#Get the tags attached to the AutoScaling Group
tags=$(aws autoscaling describe-tags --filters Name=auto-scaling-group,Values="$asg" --region=us-east-2 --query 'Tags[*].{Key:Key,Value:Value}')

#Tag the volume(s) on the instance
aws ec2 create-tags --resources $volumes --tags "$tags" --region=us-east-2


#Please note that:
#* the instances need to have a role attached to them which allows these commands to be run
#* the region needs to be changed to the correct region