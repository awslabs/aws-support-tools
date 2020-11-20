# Lambda - Build Layers Shell Script

Lambda Layers allow for updating of libraries/mobdules for Lambda quickly, without the efforts of creating a custom Lambda runtime.  These bash scripts help automate the download of libraries/modules and optionally, upload the layer and associate with a Lambda function.

This is particularily helpful when adding [AWS X-Ray SDK](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html), latest versions of the AWS SDK or older/newer versions of other libraries/modules needed when troubleshooting or deploying functions for A/B type testing.

For more information on managing [Lambda layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)

## Requirements
If you wish the script to upload the Lambda layer and deploy the layer to a Lambda function you will need [jq](https://stedolan.github.io/jq/) and zip.

[AWSCLI](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html) will need to be installed and configured if you wish to upload layers and/or associate layers with Lambda functions.

Each runtime will need to have the relevant package manager installed.  Details are in the relevant README.md of each runtime.

## Permissions

The following User/Role IAM permissions are required in your AWS Account to upload the layer and associate the layer with a Lambda function:
 * Layer Development and Use [https://docs.aws.amazon.com/lambda/latest/dg/access-control-identity-based.html#permissions-user-layer]
 * This script does NOT assign resource policy's to the Lambda, you may need to consider adding permissions in certain scenarios. [https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-permissions]

## Usage

Each runtime has variences in how it is used - please check the README:
 [python/README.md]()
 [nodejs/README.md]()

This script will use the credentials and region configured with the AWS CLI if available.  If not, AWSCLI it will ask for an AWS access key and secret key.

### NOTE: Please test these sample scripts thoroughly to see if they suit your use case.



Work Hard, Have Fun, Make History