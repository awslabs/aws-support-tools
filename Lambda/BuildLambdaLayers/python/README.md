# Lambda - Build Layers Shell Script - Python

This bash script will help with downloading modules and libraries using a python virtual environment, zip and optionally upload the layer as a new version and associate with a Lambda Function if desired.

## Usage

'''bash
./buildlayer.sh requirements.txt [lambda-version-name] [function-name]
'''

- requirements.txt is the list of python packages you wish to add to the layer.
- lambda-version-name (optional) if you want to upload the zip as a new version of an existing layer or as a new layer if no layer yet exists.
- function-name (optional) if you want to add the layer to the $lastest of a lambda function. This updates the Lambda immediately!

This script will use the credentials and region configured with the AWS CLI if available.  If not, AWSCLI it will ask for an AWS access key and secret key.

## Requirements
* If you wish the script to upload the Lambda layer and deploy the layer to a Lambda function you will need [jq](https://stedolan.github.io/jq/) and zip.
* python 2.7 will need [virtualenv](https://pip.pypa.io/en/stable/installing/)
* python 3.x will need [venv](https://docs.python.org/3/library/venv.html) 
* [pip](https://virtualenv.pypa.io/en/latest/)
* [AWSCLI](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html) will need to be installed and configured if you wish to upload layers and/or associate layers with Lambda functions.

## Permissions
The following User/Role IAM permissions are required in your AWS Account to upload the layer and associate the layer with a Lambda function:
* Layer Development and Use [https://docs.aws.amazon.com/lambda/latest/dg/access-control-identity-based.html#permissions-user-layer]
* This script does NOT assign resource policy's to the Lambda layer, you may need to consider adding permissions in certain scenarios. [https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-permissions]

### NOTE: Please test these sample scripts thoroughly to see if they suit your use case.



Work Hard, Have Fun, Make History