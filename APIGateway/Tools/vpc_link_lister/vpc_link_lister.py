
"""Created by: Rahul Baisla"""

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at

#     http://aws.amazon.com/apache2.0/

# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import json
import boto3

client = boto3.client('apigateway')

def look_for_vpc_links():
    vpclinks = client.get_vpc_links()
    
    for vpclink in vpclinks["items"]:
        print("LISTING Resources attached to VPClINK ID {0}".format(vpclink["id"]))
        print("Associated NLB is {0}".format(vpclink["targetArns"]))
        
        response = client.get_rest_apis()
        
        # Loop through APIs
        for api in response["items"]:
            print("    LISTING FOR API = %s" % api["id"])
            resources = client.get_resources(restApiId=api["id"])
        
            # Loop through Resources
            #print(resources)
            for resource in resources["items"]:
                #Describe Resource
                resource = client.get_resource(restApiId=api["id"],resourceId=resource["id"])
                #print(resource)
        
                if 'resourceMethods' in resource:
                    for method in resource["resourceMethods"]:
                        #print(method)
                        methodIntegration = client.get_method(restApiId=api["id"],resourceId=resource["id"],httpMethod=method)
        
                        if "methodIntegration" in methodIntegration:
                            #print(methodIntegration)
                            if "connectionType" in methodIntegration["methodIntegration"] and methodIntegration["methodIntegration"]["connectionType"] == 'VPC_LINK':
                                print("        API ID='{0}'   Resource ID='{1}'   Resource Path='{2}'   HttpMethod='{3}' ConnectionType='{4}' ConnectionId='{5}'".format(api["id"], resource["id"], resource["path"], methodIntegration["httpMethod"], methodIntegration["methodIntegration"]["connectionType"], methodIntegration["methodIntegration"]["connectionId"]))
                                
def lambda_handler(event, context):
    return look_for_vpc_links()