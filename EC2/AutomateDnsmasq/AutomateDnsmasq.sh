#!/bin/bash

########################################################################

# Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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


# The aim of this script is to automate the installation and configuration of dnsmasq services on Amazon Linux 1, 2 and 2023.
# The script needs no argument and could be use either stand-alone, injected as user-data or use with AWS Systems Manager Run Command AWS-RunShellScript

# Function to determine OS version
get_os_version() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "$VERSION_ID"
  fi
}

# Function to configure DNS based on OS version
configure_dns() {
  local os_version=$(get_os_version)
    
  if [[ "$os_version" == "2023" ]]; then
    # AL2023 configuration using systemd-resolved
    echo "DNS=127.0.0.1" >> /etc/systemd/resolved.conf
    echo "DNS=${NAMESERVER}" >> /etc/systemd/resolved.conf
    systemctl restart systemd-resolved.service
  else
    # AL1 or AL2 configuration using dhclient
    echo "supersede domain-name-servers 127.0.0.1, ${NAMESERVER};" >> /etc/dhcp/dhclient.conf
    dhclient
  fi
}

# set NAMESERVER
NAMESERVER="169.254.169.253"

# Install dnsmasq package
yum install -y dnsmasq bind-utils

# Create dnsmasq user/group only for Amazon Linux 1 or 2
if [[ $(get_os_version) != "2023" ]]; then
  getent group dnsmasq || groupadd -r dnsmasq
  getent passwd dnsmasq || useradd -r -g dnsmasq dnsmasq
fi

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

# Configure /etc/resolv.dnsmasq
echo "nameserver ${NAMESERVER}" > /etc/resolv.dnsmasq

# Enable and Start dnsmasq service
pidof systemd && systemctl restart dnsmasq.service || service dnsmasq restart
pidof systemd && systemctl enable  dnsmasq.service || chkconfig dnsmasq on

# Test the service
dig aws.amazon.com @127.0.0.1 

# Configure DNS based on OS version
configure_dns
