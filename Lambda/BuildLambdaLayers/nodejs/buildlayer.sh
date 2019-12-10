#!/bin/bash
set -o pipefail
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
# Note: This script can be used for any NodeJS version you choose to by specifying the version in the 
#       bash script agrguments
#
# Example requirements.txt file:
# 
# aws-sdk
# aws-xray-sdk
#
# Example of requirements file specifying versions:
#
# aws-xray-sdk@2.4.2
# aws-sdk@1.9.243
# 
# Requirements to allow this script to upload layer and/or update lambda are AWSCLI & jq.
# --------------------

# Check if required args are passed on cmd line
if ([ -f "$1" ] && [ "$2" != "" ]); then
    echo "Starting to build package:"
else
    echo "ERR: Please provide the requirements file as a minimum."
    echo ""
    echo "Usage: buildlayer.sh requirements.txt node-version [lambda-version-name] [function-name]"
    echo ""
    echo " - requirements.txt is the list of python packages you wish to add to the layer. "
    echo " - node-version is the version of runtime the modules are downloaded for, eg 10.16.3 "
    echo "   * https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html for the runtime currently supported."    
    echo " - lambda-version-name (optional) if you want to upload the zip as a new version of an existing layer or as a new layer if no layer yet exists."
    echo " - function-name (optional) if you want to add the layer to the \$latest of a lambda function."
    echo ""
    echo "Example: buildlayer.sh requirements.txt 10.16.3 mylambda-version-name some-function-name"
    echo ""
    echo "Exiting."
    exit 1
fi

# Clean out virt env 
if [ -d "nodejs" ]; then
  echo "Removing old nodejs folder."
  rm -r nodejs
fi
if [ -d "v-env" ]; then
  echo "Removing old v-env folder."
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

echo "NodeJS virtual environment start:"
# Build for a particular version
# Check versions in our documentation: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
# and node's past versions: https://nodejs.org/en/download/releases/
nodeenv v-env --node="$2" --requirements="$1"

# Activate virtual environment
echo "Activate virtual environment:"
. v-env/bin/activate

# Start check Node version
echo "Node Version:"
node --version

# Install modules per the provided requirements file and create folder structure needed for layer
mkdir -p nodejs/node_modules
cp -R v-env/lib/node_modules/ nodejs/node_modules/

echo "Deactivate virtual enviroment:"
deactivate_node

echo "Zip packages to layer.zip:"
zip -r9qdgds256k layer.zip nodejs/
ls -l layer.zip

# Publish layer if asked to
if  [ "$3" != "" ]; then
	echo "Adding new layer/version:" $3
	arn=$(aws lambda publish-layer-version --layer-name $3 --zip-file fileb://layer.zip | jq '.LayerVersionArn' -r)
	echo "Layer pubished: " $arn
	# Update function if asked to
	if [ "$3" != "" ]; then
		echo "Updating Lambda function:" $4
		aws lambda update-function-configuration --function-name $4 --layers $arn | jq
	else
		exit 0
	fi
else
	exit 0
fi