#!/bin/bash
#set -x -e -u
which aws >/dev/null 2>&1
xval=$?
if [ $xval -ne 0 ]; then
  echo "This script requires the AWS CLI"
  echo "http://aws.amazon.com/cli/"
  exit
fi

if [ $# -lt 1 ]; then
 echo "Usage: $0 [all|region]"
 echo "Please specify 'all' or a region name such as 'us-east-2'"
 exit 1
fi
export AWS_DEFAULT_REGION=$1

if [[ ! $AWS_DEFAULT_REGION =~ ^[a-z][a-z]-[a-z]{4,10}-[0-9]$ ]] ; then
  if [ $AWS_DEFAULT_REGION == 'all' ]; then
    export AWS_DEFAULT_REGION=us-east-2
    regions=$(aws ec2 describe-regions --query 'Regions[].RegionName' --output text)
  else
    echo $AWS_DEFAULT_REGION does not match expected format
    exit 2
  fi
else
  regions=$AWS_DEFAULT_REGION
fi

for region in $(echo $regions); do
  # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Filtering.html#Filtering_Resources_CLI
  AMINAME="amzn-ami-hvm-2017.03.1.20170812-x86_64-gp2"
  FILTERS="Name=owner-alias,Values=amazon Name=name,Values=$AMINAME"
  QUERY="Images[].[Name,\`$region\`,ImageId]"
  aws ec2 describe-images --output text \
       --filters $FILTERS \
       --region $region --query $QUERY &
done
xval=0
while [ $xval -ne 1 ]; do
  still_running=$( ps aux | grep '[d]escribe-images' >/dev/null )
  xval=$?
  sleep 5
  echo -n "still running queries "
  date --utc +'%Y-%m-%dT%H:%M:%S'
done
