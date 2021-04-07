# Assign Static Private IP to Master node #

This is a Python script that can be used as a bootstrap action or as an EMR step to attach a static private IP from the CIDR range of your subnet to the master node of the cluster.

What does this script do:

- takes the private IP address and region as its argument 
- associate that IP to the eth0 interface of the master node
- setup the necessary network configuration to ensure that all the traffic is redirected from the secondary to the primary IP address

Steps to execute this script:

- Please confirm that your AWS Identity and Access Management (IAM) policy allows permissions for EMR_EC2_DefaultRole and ec2:AssignPrivateIpAddresses.
- Download the assign_private_ip_region.py script from awslabs github repo.
- Save the script in an Amazon Simple Storage Service (Amazon S3) bucket.
- Specify the script as a [custom bootstrap action](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-bootstrap.html#bootstrapCustom) while launching an Amazon EMR cluster. You can also run the script as an [Amazon EMR step](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-work-with-steps.html#emr-add-steps). The script requires an argument, which is a private IP address from the CIDR range of your subnet and the region. The script attaches that private IP address to the network interface (eth0) of the master node. The script also configures the network settings to redirect all traffic from the secondary IP address to the primary IP address.
 eg 
  -  From bash shell (on master node)
     s3://<bucekt>/assign_private_ip.py 172.31.45.7 us-east-1
    
  -  Using BA
     Script location:- s3://<s3 bucekt>/assign_private_ip.py
     Optional arguments:-  172.31.45.13 us-east-1
    
- To find the new IP address, open the Amazon Elastic Compute Cloud (Amazon EC2) console. Then, select the EC2 instance that's acting as the master node of the EMR cluster. The new IP address appears on the Description tab, in the Secondary private IPs field.
