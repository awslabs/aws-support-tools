The script lets you automatically attach a second elastic network interface (ENI) in a difference subnet than an instance's primary ENI when Amazon EC2 Auto Scaling launches a new instance. 
You can optionally have one of the ENI's in a public subnet and the other in a private subnet. The scripts also deletes ENIs attached to the instance when instances are being terminated to avoid exhausting private IP addresses in the subnet and reaching the ENI limit in your account.

**This solution supports Warm pools and scale into Warm pools**.

**Note:** The following resolution is for an Auto Scaling Group enabled in single or multiple Availability Zones, with two or more subnets in each enabled Availability Zone.  Amazon EC2 does not allow multiple ENIs in different Availability Zones to be attached to the same instance simultaneously 

This script is for a lambda function which uses Python 3.8 for the Runtime. This script is triggered by a lifecycle hook in the auto scaling group
