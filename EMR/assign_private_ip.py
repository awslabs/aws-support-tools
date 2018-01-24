#!/usr/bin/python

import sys, subprocess

is_master = subprocess.check_output(['cat /emr/instance-controller/lib/info/instance.json | jq .isMaster'], shell=True).strip()

if is_master == "true":
    private_ip = str(sys.argv[1])
    instance_id = subprocess.check_output(['/usr/bin/curl -s http://169.254.169.254/latest/meta-data/instance-id'], shell=True)
    interface_id = subprocess.check_output(['aws ec2 describe-instances --instance-ids %s | jq .Reservations[].Instances[].NetworkInterfaces[].NetworkInterfaceId' % instance_id], shell=True).strip().strip('"')

    #Assign private IP to the master instance:
    subprocess.check_call(['aws ec2 assign-private-ip-addresses --network-interface-id %s --private-ip-addresses %s' % (interface_id, private_ip)], shell=True)

    subnet_id = subprocess.check_output(['aws ec2 describe-instances --instance-ids %s | jq .Reservations[].Instances[].NetworkInterfaces[].SubnetId' % instance_id], shell=True).strip().strip('"').strip().strip('"')
        
    subnet_cidr = subprocess.check_output(['aws ec2 describe-subnets --subnet-ids %s | jq .Subnets[].CidrBlock' % subnet_id], shell=True).strip().strip('"')
    cidr_prefix = subnet_cidr.split("/")[1]

    #Add the private IP address to the default network interface:
    subprocess.check_call(['sudo ip addr add dev eth0 %s/%s' % (private_ip, cidr_prefix)], shell=True)

    #Configure iptablles rules such that traffic is redirected from the secondary to the primary IP address:
    primary_ip = subprocess.check_output(['/sbin/ifconfig eth0 | grep \'inet addr:\' | cut -d: -f2 | awk \'{ print $1}\''], shell=True).strip()
    subprocess.check_call(['sudo iptables -t nat -A PREROUTING -d %s -j DNAT --to-destination %s' % (private_ip, primary_ip)], shell=True)
else:
    print "Not the master node"
