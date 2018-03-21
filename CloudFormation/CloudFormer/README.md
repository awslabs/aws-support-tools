##CloudFormer Implementation for Existing VPCs

This version of the CloudFormer solution can be used to launch the solution into an existing VPC.

This version replaces the "VPCSelection" parameter with two new parameters "VpcId" and "SubnetId".

AWS specific parameter types "AWS::EC2::VPC::Id" and "AWS::EC2::Subnet::Id" have been used to populate selections based on resources available in the account. The subnet selected MUST be a public subnet with an Internet Gateway. Selecting a private subnet that uses a NAT Gateway will not work.
