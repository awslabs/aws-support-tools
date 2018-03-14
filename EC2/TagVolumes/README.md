Tag EBS volumes on instances in AutoScaling Groups
==================
Problem: 
When tags are specified in an AutoScaling Group, they are applied to the instances created in that group, but not the EBS volumes attached to those instances.  

------------------

Short Description:
This script acts as a workaround to tag EBS volumes on Linux instances

------------------

Usage:
Put one of these scripts in the userdata section of the AutoScaling Groups Launch Configuration so that the script is run at startup each time an instance is launched

------------------

Method of tagging:
* The script titled TagAutoScalingVolumesGetTags will take the tags on an AutoScaling Group and apply them to the EBS volumes on each instance launched
* The script titled TagAutoScalingVolumesSetTags will take the tags defined in the script and apply them to the EBS volumes on each instance launched

------------------

Configuration:
* The instances need to have a role attached to them which allows these commands to be run
* The region needs to be changed to the correct region
* The AWS CLI must be installed on the instance