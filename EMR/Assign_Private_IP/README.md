# Assign Static Private IP to Master node #

This is a Python script that can be used as a bootstrap action or as an EMR step to attach a static private IP from the CIDR range of your subnet to the master node of the cluster.

What does this script do:

- takes the private IP address as its argument 
- associate that IP to the eth0 interface of the master node
- setup the necessary network configuration to ensure that all the traffic is redirected from the secondary to the primary IP address
