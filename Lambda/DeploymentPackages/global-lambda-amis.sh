#!/bin/bash

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

#set -x -e -u
which aws >/dev/null 2>&1
xval=$?
if [ $xval -ne 0 ]; then
  echo "This script requires the AWS CLI"
  echo "http://aws.amazon.com/cli/"
  exit
fi

if [ $# -lt 1 ]; then
 echo "Usage: $0 [all|region]"
 echo "Please specify 'all' or a region name such as 'us-east-2'"
 exit 1
fi
export AWS_DEFAULT_REGION=$1

if [[ ! "$AWS_DEFAULT_REGION" =~ ^[a-z][a-z]-[a-z]{4,10}-[0-9]$ ]] ; then
  if [ "$AWS_DEFAULT_REGION" == 'all' ]; then
    export AWS_DEFAULT_REGION=us-east-2
    regions=$(aws ec2 describe-regions --query 'Regions[].RegionName' --output text)
  else
    echo "$AWS_DEFAULT_REGION does not match expected format"
    exit 2
  fi
else
  regions="$AWS_DEFAULT_REGION"
fi

for region in $regions; do
  # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Filtering.html#Filtering_Resources_CLI
  AMINAME="amzn-ami-hvm-2017.03.1.20170812-x86_64-gp2"
  QUERY="Images[].[Name,\`$region\`,ImageId]"
  aws ec2 describe-images --output text \
       --filters "Name=owner-alias,Values=amazon" "Name=name,Values=$AMINAME" \
       --region "$region" --query "$QUERY" &
done

sleep 1
pgrep -f '[d]escribe-images' >/dev/null && xval=1
while [ $xval -ne 0 ]; do
  echo -n "describe-images still running "
  date --utc +'%Y-%m-%dT%H:%M:%S'
  pgrep -f '[d]escribe-images' >/dev/null 
  xval=$?
  sleep 5
done
