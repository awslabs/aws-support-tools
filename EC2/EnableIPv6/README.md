# Enable IPv6 #


This is a shell script built to search the user's AWS account for VPCs in each region, and enable IPv6 capabilities on each. This tool goes as far as associating an Amazon-provided IPv6 CIDR block for each VPC found, updating all Route Tables in each VPC to include a default route for IPv6 traffic to the IGW, and update Security Groups to include rules to allow IPv6 traffic. The results (successes and failures alike) are saved in the resulting log file, stored in the same directory the script is launched from.

What this script **does** do:

- describes your VPCs, Security Groups, Route Tables, and Internet Gateways in each AWS region specified
- enable the Amazon-provided IPv6 CIDR block for every VPC
- create a Default Route for IPv6 traffic, pointing to the VPC's IGW, in each VPC's Route Tables
- add a Security Group Egress rule to allow all outbound IPv6 traffic

What this script **does not** do:
- add new subnets with new IPv6 address space - you must do this on your own or modify the code to do so.
- modify Security Group Ingress rules to allow IPv6 traffic - you must do this on your own or modify the code to so.
- launch new resources - this script only modifies existing resources.

Do note that if you wish to enable IPv6 for all your VPCs in all your account's regions, this script is for you. Otherwise, if you need to enable IPv6 for certain VPCs and not others, you will need to modify the code or do this manually, as this script goes through all of them.

- - - -
# How To Use It #

1. Configure the ```aws-cli``` on your workstation. Ensure you have a Bash shell available in /usr/bin/env. (You likely do.)
2. Modify the script's REGIONLIST array if you want to enable IPv6 in certain regions only. If you're looking to enable all regions' VPCs for IPv6, skip to the next step.
3. Run the enableIPv6.sh script: ```$ ./enableIPv6.sh``` This will begin filling your terminal window with what resources it finds and modifies. Note that a copy of this output will be in the ```log-enableIPv6.log``` file for later review as well.
4. When it's done, allocate IPv6 address space for your subnets in those VPCs, so your EC2 instances will get IPv6 addresses. Guidance on how to do this can be found [in the documentation here.](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#assign-ipv6-address)

- - - -

# Relevant Documentation #

- [Assigning an IPv6 Address to Your EC2 Instances](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#assign-ipv6-address)