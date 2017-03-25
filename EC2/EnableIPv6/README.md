# enableIPv6 #


This is a shell script built to search the user's AWS account for VPCs in each region, and enable IPv6 capabilities on each. This tool goes as far as associating an Amazon-provided IPv6 CIDR block for each VPC found, updating all Route Tables in each VPC to include a default route for IPv6 traffic to the IGW, and update Security Groups to include rules to allow IPv6 traffic. The results (successes and failures alike) are saved in the resulting log file, stored in the same directory the script is launched from.

What this script does not do is add subnets with new IPv6 address space (you must do that on your own or modify the code to do so, since I didn't get that far just yet). It does not launch new resources, just modifies existing ones.

- - - -
# How To Use It #

1. Configure the awscli on your workstation. Ensure you have a Bash shell available in /usr/bin/env. (You likely do.)
2. Modify the script's REGIONLIST array if you want to enable IPv6 in certain regions only. If you're enabling all of them, skip to the next step.
3. Run the enableIPv6.sh script. 
4. When it's done, allocate IPv6 address space for your subnets in those VPCs.

- - - -