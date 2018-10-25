#!/bin/bash
# Install Sysstat package.
yum install sysstat -y 
#Validate that First argument is a number
if [ $1 -ge 0 2>/dev/null ] ; then

#Fetch the instance-id to use it as a dimension while pushing the CloudWatch metrics
Instanceid=`curl http://169.254.169.254/latest/meta-data/instance-id/`
EC2_AVAIL_ZONE=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
EC2_REGION="`echo \"$EC2_AVAIL_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
Time=$1
while read line; do  
  ARRAY[$c]="$line"
  c=$((c+1))  
done < <(curl http://169.254.169.254/latest/meta-data/block-device-mapping/)
#printf '%s\n' "${ARRAY[@]}"
#echo ${ARRAY[*]}
#for i in `curl http://169.254.169.254/latest/meta-data/block-device-mapping/`;do
function contains() {
    local n=$#
    local value=${!n}
    for ((i=1;i < $#;i++)) {
        if [[ "${!i}" == ${value}* ]]; then
            echo "y"
            return 0
        fi
    }
    echo "n"
    return 1
}

if [ $(contains "${ARRAY[@]}" "ephemeral") == "y" ]; then
    echo "The instance has Instance Store Volumes, Please consider DiskReadBytes, DiskWriteBytes instance metrics"
while true; 
do 
 Sum=`sar -b 1 1 | awk '(NR==4){print $5+$6}'`
# echo $Sum
 sleep $1
SumKB=$(( ( ${Sum%.*} * 512) / 1024 ))
aws cloudwatch put-metric-data --metric-name EBSThroughputKB --namespace EBS  --dimensions InstanceId=$Instanceid --value $SumKB --unit Kilobytes/Second --region $EC2_REGION 
SumMB=$(( SumKB / 1024 ))
aws cloudwatch put-metric-data --metric-name EBSThroughputMB --namespace EBS  --dimensions InstanceId=$Instanceid --value $SumMB --unit Megabytes/Second  --region $EC2_REGION
echo At $(date) Total EBS Throughput = $SumKB    KBytes/sec = $SumMB MBytes/sec
done
 
else 
    echo "The instance has EBS volumes only, The provided metrices is 100% accurate"
fi
#Start a loop to gather the SAR output & sum breads/s , bwrite/s, please bear in mind $
while true; 
do 
 Sum=`sar -b 1 1 | awk '(NR==4){print $5+$6}'`
# echo $Sum
 sleep $1
SumKB=$(( ( ${Sum%.*} * 512) / 1024 ))
aws cloudwatch put-metric-data --metric-name EBSThroughputKB --namespace EBS  --dimensions InstanceId=$Instanceid --value $SumKB --unit Kilobytes/Second --region $EC2_REGION 
SumMB=$(( SumKB / 1024 ))
aws cloudwatch put-metric-data --metric-name EBSThroughputMB --namespace EBS  --dimensions InstanceId=$Instanceid --value $SumMB --unit Megabytes/Second  --region $EC2_REGION
echo At $(date) Total EBS Throughput = $SumKB    KBytes/sec = $SumMB MBytes/sec
done

else 
echo Please enter a valid positive number as an argument
fi
