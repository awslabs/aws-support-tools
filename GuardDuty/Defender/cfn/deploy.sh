#!/bin/bash

# Created by: David Pigliavento

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

# Wrapper script to simplify deployment

USAGE="Usage: $0 [-role role_arn] [-bucket s3_bucket_name]"

check_input()
    if [ -z ${ROLE} ] || [ -z ${S3_BUCKET} ]; then
        echo "$USAGE"
        exit 1
    fi

while (( "$#" )); do

    if [[ ${1} == "-role" ]]; then
      	shift
        ROLE=${1}
    fi

    if [[ ${1} == "-bucket" ]]; then
      	shift
        S3_BUCKET="${1}"
    fi

    shift
done

check_input

aws cloudformation package \
    --template-file stack.yaml \
    --s3-bucket ${S3_BUCKET} \
    --output-template-file deploy.yaml

aws cloudformation deploy \
    --template-file deploy.yaml \
    --stack-name guardduty-defender \
    --parameter-overrides \
    Role=$ROLE
