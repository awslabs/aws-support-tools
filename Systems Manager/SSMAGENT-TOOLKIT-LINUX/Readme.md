
### **Owner**

Amazon

### **Platforms**

Linux

### **Description**

The SSMAgent-Toolkit-Linux is a bash script developed to run multiple checks to determined why an Linux EC2 instance does not come up as SSM Managed Instances.


### **Usage**

Simply download the ssmagent-toolkit-Linux.sh and execute the script.
This script must run with sudo privileges.


- For Redhat Variants

```
[root@dub901nex901 ec2-user]# bash ssmagent-toolkit-Linux.sh

```
   
- For Debian Variants ( Note: Use of sh on ubuntu may fail)

```
[root@dub901nex901 ec2-user]# bash ssmagent-toolkit-Linux.sh

```

### **Options Available**

- Run -h to see the available options.

```

[root@dub901nex901 ~]# bash ssmagent-toolkit-Linux.sh -h
Description of the script options here.

Syntax: ssmagent-toolkit-Linux.sh [-h|r|l]
options:
-h     Print this Help.
-r     Enter Region. Useful with On-Premise/Hybrid Instances.
-l     Collect Logs.

Examples:
1) To run the Test:
         ssmagent-toolkit-Linux.sh

2) To run the Test with us-east-1 region:
         ssmagent-toolkit-Linux.sh -r us-east-1

3) To Collect SSM Agent Logs
         ssmagent-toolkit-Linux.sh -l

```

- Run -r to specify the region

- Run -l to collect SSM agent or Run Command Logs.

