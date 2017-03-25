# Enable IPv6 #


This is a shell script built to search the user's AWS account for VPCs in each region, and enable IPv6 capabilities on each. This tool goes as far as associating an Amazon-provided IPv6 CIDR block for each VPC found, updating all Route Tables in each VPC to include a default route for IPv6 traffic to the IGW, and update Security Groups to include rules to allow IPv6 traffic. The results (successes and failures alike) are saved in the resulting log file, stored in the same directory the script is launched from.

What this script does not do is add subnets with new IPv6 address space (you must do that on your own or modify the code to do so, since I didn't get that far just yet). It does not launch new resources, just modifies existing ones.

- - - -
# How To Use It #

1. Configure the ```aws-cli``` on your workstation. Ensure you have a Bash shell available in /usr/bin/env. (You likely do.)
2. Modify the script's REGIONLIST array if you want to enable IPv6 in certain regions only. If you're looking to enable all regions' VPCs for IPv6, skip to the next step.
3. Run the enableIPv6.sh script: ```$ ./enableIPv6.sh``` This will begin filling your terminal window with what resources it finds and modifies. Note that a copy of this output will be in the ```log-enableIPv6.log``` file for later review as well.
4. When it's done, allocate IPv6 address space for your subnets in those VPCs, so your EC2 instances will get IPv6 addresses. 

- - - -

# Relevant Documentation #

Assigning an IPv6 Address to Your EC2 Instances: [http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#assign-ipv6-address](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#assign-ipv6-address)