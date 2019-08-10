#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
  
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  A copy of the License is located at
  
#      http://www.apache.org/licenses/LICENSE-2.0
  
#  or in the "license" file accompanying this file. This file is distributed 
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either 
#  express or implied. See the License for the specific language governing 
#  permissions and limitations under the License.

#!/usr/bin/python
# run > python get_emr_cli_export.py j-2ABCABCABC
import boto3
import json
import sys

cluster_id = sys.argv[1]
client = boto3.client('emr')
clst = client.describe_cluster(ClusterId=cluster_id)
clst_info = clst['Cluster']

# non-list type
opt_keys = {}
opt_keys['--release-label'] = 'ReleaseLabel'
opt_keys['--log-uri'] = 'LogUri'
opt_keys['--auto-terminate'] = 'AutoTerminate'
opt_keys['--auto-scaling-role'] = 'AutoScalingRole'
opt_keys['--ebs-root-volume-size'] = 'EbsRootVolumeSize'
opt_keys['--service-role'] = 'ServiceRole'
opt_keys['--name'] = 'Name'

awscli = "aws emr create-cluster "
for i in opt_keys.keys():
    if clst_info[opt_keys[i]] is True:
        awscli += " " + i
    else:
        awscli += " " + i + " " + str(clst_info[opt_keys[i]])

InstanceAtt = clst_info['Ec2InstanceAttributes']
cli_InstanceAtt = {}
cli_InstanceAtt['InstanceProfile'] = InstanceAtt.pop('IamInstanceProfile')
cli_InstanceAtt['KeyName'] = InstanceAtt.pop('Ec2KeyName')
cli_InstanceAtt['SubnetId'] = InstanceAtt.pop('Ec2SubnetId')
cli_InstanceAtt['EmrManagedSlaveSecurityGroup'] = InstanceAtt.pop('EmrManagedSlaveSecurityGroup')
cli_InstanceAtt['EmrManagedMasterSecurityGroup'] = InstanceAtt.pop('EmrManagedMasterSecurityGroup')
awscli += ' --ec2-attributes ' + '\'' + str(json.dumps(cli_InstanceAtt)) + '\''


# list type
l_opt_keys = {}
l_opt_keys['--applications'] = 'Applications'
l_opt_keys['--tags'] = 'Tags'
awscli += ' --applications ' + " ".join(list(map(lambda a: 'Name=%s' % a['Name'], clst_info[l_opt_keys['--applications']])))
awscli += ' --tags ' + " ".join(list(map(lambda a: '\'%s=%s\'' % (a['Key'], a['Value']), clst_info[l_opt_keys['--tags']])))


# steps
cli_steps = []
steps = client.list_steps(ClusterId=cluster_id)
for item in steps['Steps']:
    cli_step = {}
    cli_step['Name'] = item['Name']
    cli_step['ActionOnFailure'] = item['ActionOnFailure']
    cli_step['Args'] = item['Config']['Args']
    cli_step['Jar'] = item['Config']['Jar']
    cli_steps.append(cli_step)

awscli += ' --steps ' + '\'' + json.dumps(cli_steps) + '\''

# instance groups
cli_igroups = []
igroups = client.list_instance_groups(ClusterId=cluster_id)
for item in igroups['InstanceGroups']:
    cli_igroup = {}
    cli_igroup['InstanceCount'] = item['RequestedInstanceCount']
    cli_igroup['InstanceGroupType'] = item['InstanceGroupType']
    cli_igroup['InstanceType'] = item['InstanceType']
    cli_igroup['Name'] = item['Name']
    if 'BidPrice' in item:
        cli_igroup['BidPrice'] = item['BidPrice']
    if len(item['EbsBlockDevices']) > 0:
        cli_igroup['EbsConfiguration'] = {}
        cli_igroup['EbsConfiguration']['EbsBlockDeviceConfigs'] = {}
        cli_igroup['EbsConfiguration']['EbsBlockDeviceConfigs']['VolumeSpecification'] = \
            list(map(lambda a: a['VolumeSpecification'], item['EbsBlockDevices']))
    cli_igroups.append(cli_igroup)

awscli += ' --instance-groups ' + '\'' + json.dumps(cli_igroups) + '\''
print(awscli)
