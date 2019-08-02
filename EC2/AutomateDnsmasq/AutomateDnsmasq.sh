#!/bin/bash

########################################################################

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License


########################################################################


# The aim of this script is to automate the installation and configuration of DNSMasq services on Amazon Linux 1 & 2
# The script needs no argument and could be use either stand-alone, injected as user-data or use with AWS Systems Manager Run Command AWS-RunShellScript

# Check whether this is to run on VPC (default) or EC2 classic and set NAMESERVER accordingly
INTERFACE=$(curl --silent http://169.254.169.254/latest/meta-data/network/interfaces/macs/ | head -n1)
IS_IT_CLASSIC=$(curl --write-out %{http_code} --silent --output /dev/null http://169.254.169.254/latest/meta-data/network/interfaces/macs/${INTERFACE}/vpc-id)

if [[ $IS_IT_CLASSIC == '404' ]]
then
  NAMESERVER="172.16.0.23"
else
  NAMESERVER="169.254.169.253"
fi

# Install dnsmasq package
yum install -y dnsmasq

# Create the required User and Group
groupadd -r dnsmasq
useradd -r -g dnsmasq dnsmasq

# Set dnsmasq.conf configuration
cat << EOF > /etc/dnsmasq.conf
# Server Configuration
listen-address=127.0.0.1
port=53
bind-interfaces
user=dnsmasq
group=dnsmasq
pid-file=/var/run/dnsmasq.pid
# Name resolution options
resolv-file=/etc/resolv.dnsmasq
cache-size=500
neg-ttl=60
domain-needed
bogus-priv
EOF

# Populate /etc/resolv.dnsmasq
echo "nameserver ${NAMESERVER}" > /etc/resolv.dnsmasq

# Enable and Start dnsmasq service
pidof systemd && systemctl restart dnsmasq.service || service dnsmasq restart
pidof systemd && systemctl enable  dnsmasq.service || chkconfig dnsmasq on

# Test the service and configure dhclient accordingly
dig aws.amazon.com @127.0.0.1 && echo "supersede domain-name-servers 127.0.0.1, ${NAMESERVER};" >> /etc/dhcp/dhclient.conf && dhclient
