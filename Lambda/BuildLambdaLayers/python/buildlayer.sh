#!/bin/bash
set -euo pipefail
# Copyright [2019]-[2019] Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# 
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
# 
#    http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#
# --------------------
# Purpose: Build layers to allow for module testing the latest libraries rapidly or for diagnostics such as
#          X-Ray.  Please test thoroughly if this suits your use-case, and if you have any issues report via git issues
# 
# Note: This script can be used for boto and boto3 / py2/3 as needed by changing #'s out as needed below.
#
# Example requirements.txt file:
# 
# boto3
# aws-xray-sdk
#
# Example of requirements file specifying versions:
#
# aws-xray-sdk==2.4.2
# boto3==1.9.243
# 
# Requirements to allow this script to upload layer and/or update lambda are AWSCLI & jq.
# --------------------

# Check if arg passed on cmd line
if [ -f "$1" ]; then
    echo "Starting to build package:"
else
    echo "ERR: Please provide the requirements file as a minimum."
    echo ""
    echo "Usage: buildlayer.sh requirements.txt [lambda-version-name] [function-name]"
    echo ""
    echo " - requirements.txt is the list of python packages you wish to add to the layer. "
    echo " - lambda-version-name (optional) if you want to upload the zip as a new version of an existing layer or as a new layer if no layer yet exists."
    echo " - function-name (optional) if you want to add the layer to the \$latest of a lambda function."
    echo ""
    exit 1
fi

# Clean out virt env 
echo "Removing old virtual env/python folder"
if [ -d "python" ]; then
  rm -r python
fi
if [ -d "v-env" ]; then
  rm -r v-env
fi

dateofbackup=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Backup previous layer built
if [ -f layer.zip ]; then
    echo "Copy layer.zip to layer-"$dateofbackup".zip"
    cp layer.zip layer-backup-$dateofbackup.zip
    rm layer.zip
else 
    echo "No previous layer file, no local backup occurred."
fi

echo "Python virtual environment start:"
# Python3.x
# Alternative is to use virtualenv -p /usr/bin/python3 v-env
python3 -m venv v-env
# Can comment out the line above and remove the # below to allow Python2.7 virtual environments if you have python 2.7 installed
#python2 -m virtualenv v-env

# Activate virtual environment
source v-env/bin/activate

# Install modules per the provided requirements file
echo "Download Python Packages..."
pip install -q --no-cache-dir -r $1 -t python/

echo "End virtual env..."
# Deactive virtual environment
deactivate

echo "Zip packages..."
# Zip the packages up
zip -r9qdgds256k layer.zip python/
ls -l layer.zip

# Publish layer if asked to
if  [ "$2" != "" ]; then
	echo "Adding new layer or new layer version: "$2
	arn=$(aws lambda publish-layer-version --layer-name $2 --zip-file fileb://layer.zip | jq '.LayerVersionArn' -r)
	echo "Layer pubished: "$arn
	# Update function if asked to
	if [ "$3" != "" ]; then
		echo "Updating Lambda function: "$3
		aws lambda update-function-configuration --function-name $3 --layers $arn | jq
	else
		exit 0
	fi
else
	exit 0
fi