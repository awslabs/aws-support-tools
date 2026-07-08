Bash Script AutomateDnsmasq.sh	
=================================================
The Bash script `AutomateDnsmasq.sh` automates the installation and configuration of **Dnsmasq** on Amazon Linux 1, 2 and 2023. It could be used as a standalone script, injected as [user-data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) during the launch of an AWS EC2 instance, or used with [AWS Systems Manager Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html) to perform the actions on existing instances with SSM Agent configured.

Cloud-init Directives AutomateDnsmasq.cloudinit		
===============================================
The cloud-init directives `AutomateDnsmasq.cloudinit`	automates the installation and configuration of **Dnsmasq** on Amazon Linux 1, 2 and 2023 and should be injected as user-data during the instance launch.

Details of steps performed on both the bash script and the cloud-init directives
=================================================================================
The following step will be automatically performed by the bash script and the cloud-init directives:

  - Install dnsmasq package (if not already installed)

  - Create the appropriate dnsmasq user and group (if not already created)
  
  - Set /etc/dnsmasq.conf configuration and start the dnsmasq service
  
  - Configure /etc/dhcp/dhclient.conf and /etc/resolv.dnsmasq with the right DNS IP Address (_Note that this DNS is set to `169.254.169.253` for VPC_)
  
  - Configure /etc/dhcp/dhclient.conf and trigger `dhclient` or `systemctl restart systemd-resolved.service`.
