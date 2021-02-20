
"""Created by: Rahul Baisla"""

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at

#     http://aws.amazon.com/apache2.0/

# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import boto3

client = boto3.client('apigateway')

def look_for_resource_methods(apiid, resource):
    """Loop through HTTP methods in API resources"""
    if 'resourceMethods' in resource:
        for method in resource["resourceMethods"]:
            #print(method)
            methodintegration = client.get_method(restApiId=apiid,
            resourceId=resource["id"],
            httpMethod=method)

            if "methodIntegration" in methodintegration:
                #print(methodIntegration)
                if ("connectionType" in methodintegration["methodIntegration"] and
                methodintegration["methodIntegration"]["connectionType"] == 'VPC_LINK'):
                    print("        API ID='{0}'   Resource ID='{1}'   Resource Path='{2}'   "
                    "HttpMethod='{3}' ConnectionType='{4}' ConnectionId='{5}'".format(
                        apiid, resource["id"], resource["path"], methodintegration["httpMethod"],
                        methodintegration["methodIntegration"]["connectionType"],
                        methodintegration["methodIntegration"]["connectionId"]))

def look_for_resources(apiid, resources):
    """Loop through API resources"""
    #print(resources)
    for resource in resources["items"]:
        #Describe Resource
        resource = client.get_resource(restApiId=apiid,resourceId=resource["id"])
        #print(resource)
        look_for_resource_methods(apiid, resource)

def look_for_vpc_links():
    """Loop through Vpc Links"""
    vpclinks = client.get_vpc_links()

    for vpclink in vpclinks["items"]:
        print("LISTING Resources attached to VPClINK ID {0}".format(vpclink["id"]))
        print("Associated NLB is {0}".format(vpclink["targetArns"]))

        response = client.get_rest_apis()

        # Loop through APIs
        for api in response["items"]:
            print("    LISTING FOR API = %s" % api["id"])
            apiid = api["id"]
            resources = client.get_resources(restApiId=apiid)

            look_for_resources(apiid, resources)

def lambda_handler(event, context):
    """Return the function"""
    return look_for_vpc_links()
