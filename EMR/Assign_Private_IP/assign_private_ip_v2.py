#!/usr/bin/python
#
#Copyright 2017-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file 
#except in compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/apache2.0/
#
#or in the "license" file accompanying this file. This file is distributed on an "AS IS" 
#BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the 
#License for the specific language governing permissions and limitations under the License.

import sys, subprocess

is_master = subprocess.check_output(['cat /emr/instance-controller/lib/info/instance.json | jq .isMaster'], shell=True).strip()

if is_master == "true":
    private_ip = str(sys.argv[1])
    region = str(sys.argv[2])
    instance_id = subprocess.check_output(['TOKEN=`/usr/bin/curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` &&  /usr/bin/curl -H "X-aws-ec2-metadata-token: $TOKEN" -v http://169.254.169.254/latest/meta-data/instance-id'], shell=True)
    print(instance_id)
    interface_id = subprocess.check_output(['aws ec2 describe-instances --region %s --instance-ids %s | jq .Reservations[].Instances[].NetworkInterfaces[].NetworkInterfaceId' % (region, instance_id)], shell=True).strip().strip('"')
    print(interface_id)

    #Assign private IP to the master instance:
    subprocess.check_call(['aws ec2 assign-private-ip-addresses --region %s --network-interface-id %s --private-ip-addresses %s' % (region, interface_id, private_ip)], shell=True)

    subnet_id = subprocess.check_output(['aws ec2 describe-instances --region %s --instance-ids %s | jq .Reservations[].Instances[].NetworkInterfaces[].SubnetId' % (region, instance_id)], shell=True).strip().strip('"').strip().strip('"')
        
    subnet_cidr = subprocess.check_output(['aws ec2 describe-subnets --region %s --subnet-ids %s | jq .Subnets[].CidrBlock' % (region, subnet_id)], shell=True).strip().strip('"')
    cidr_prefix = subnet_cidr.split("/")[1]

    #Add the private IP address to the default network interface:
    subprocess.check_call(['sudo ip addr add dev eth0 %s/%s' % (private_ip, cidr_prefix)], shell=True)

    #Configure iptablles rules such that traffic is redirected from the secondary to the primary IP address:
    primary_ip = subprocess.check_output(['TOKEN=`/usr/bin/curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` && /usr/bin/curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4'], shell=True, universal_newlines=True).strip()
    subprocess.check_call(['sudo iptables -t nat -A PREROUTING -d %s -j DNAT --to-destination %s' % (private_ip, primary_ip)], shell=True)
else:
    print "Not the master node"
