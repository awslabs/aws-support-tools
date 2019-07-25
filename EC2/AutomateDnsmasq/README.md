Bash Script AutomateDnsmasq.sh	
=================================================
The Bash script AutomateDnsmasq.sh automates the installation and configuration of Dnsmasq on Amazon Linux 1 & 2. It could be used as a standalone script, injected as User data during the Launch of an AWS EC2 instance, or used with AWS Systems Manager Run Command to perform the actions on existing instances with SSM Agent configured.

Cloud-init Directives AutomateDnsmasq.cloudinit		
===============================================
The Cloud-init Directives AutomateDnsmasq.cloudinit	automates the installation and configuration of Dnsmasq on Amazon Linux 1 & 2 and should be injected as user-data during the instance launch.

Details of steps performed on both the Bash script and the Cloud-init Directives
=================================================================================
The following step will be automatically performed by the Bash script and the Cloud-init directives:

  - Install dnsmasq package (if not already installed)

  - Create the appropriate dnsmasq user and group
  
  - Set /etc/dnsmasq.conf configuration and start the dnsmasq service
  
  - Configure /etc/dhcp/dhclient.conf and /etc/resolv.dnsmasq with the right DNS IP Address ( Note that this DNS is set to 169.254.169.253 for VPC and to 172.16.0.23 for ec2-classic)
  
  - Configure /etc/dhcp/dhclient.conf and trigger dhclient
