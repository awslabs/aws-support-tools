#!/usr/bin/env bash
#
#   List out all VPCs in all AWS regions, and enable IPv6 on each.
#   Also update Route Tables with ::/0 default route and Security Groups to allow IPv6 traffic.
#
#   This script can be expanded out as per one's specific need to take further actions, 
#   like associating IPv6 CIDR blocks with existing subnets. Running this script multiple 
#   times will not harm resources that have already been enabled for IPv6 - conflicting 
#   commands will simply error out.
#
#   Do note that this is built using the OS X install of grep and as such your version 
#   may use alternate flags. Overall it should be compatible with current Linux builds.
#

# Output to both stdout and log-enableIPv6.log, including errors.
exec > >(tee -ia log-enableIPv6.log)
exec 2> >(tee -ia log-enableIPv6.log >&2)

REGIONLIST=(`echo $(aws ec2 describe-regions --output text --query 'Regions[*].RegionName' | tr -s '\t' ' ')`)

# By default the REGIONLIST is populated with all current regions. If you wish to curate your own list of regions,
# uncomment the following line and edit the space-delimited list for your needs.
# REGIONLIST=( ap-south-1 eu-west-2 eu-west-1 ap-northeast-2 ap-northeast-1 sa-east-1 ca-central-1 ap-southeast-1 ap-southeast-2 eu-central-1 us-east-1 us-east-2 us-west-1 us-west-2 )

printf "%s\n" "Enabling IPv6 in:"
printf "%s\n" "${REGIONLIST[@]}"

for REGION in "${REGIONLIST[@]}"; do
  # Blank the VPC array for each new region
  VPCLIST=()

  printf "%s\n" "===="
  printf "%s\n" "Checking ${REGION} for VPC IDs."

  for VPCID in `aws ec2 describe-vpcs --output json --region ${REGION} | grep -ohE "\w*vpc-[a-zA-Z0-9]{8}"`; do
    VPCLIST+=("${VPCID}")
    printf "%s\n" "${REGION}: ${VPCID}"
  done

  printf "\n"

  for VPCID in "${VPCLIST[@]}"; do
    printf "%s\n" "[Enabling IPv6 on ${VPCID}]"

    printf "%s\n" "Associating IPv6 CIDR Block to ${VPCID}."
    aws ec2 associate-vpc-cidr-block --output json --region ${REGION} --vpc-id ${VPCID} --amazon-provided-ipv6-cidr-block

    TARGETIGW=$(aws ec2 describe-internet-gateways --output json --region ${REGION} | grep -B 10 "${VPCID}" | grep -oh "\w*igw-\w*")

    # One IGW per VPC, but many possible Route Tables per VPC.
    for ROUTETABLE in `aws ec2 describe-route-tables --output json --region ${REGION} | grep -B 1 "${VPCID}" | grep -oh "\w*rtb-\w*"`; do
      printf "%s\n" "Updating ${ROUTETABLE} with IPv6 default route to ${TARGETIGW}."
      aws ec2 create-route --output json --region ${REGION} --route-table-id ${ROUTETABLE} --gateway-id ${TARGETIGW} --destination-ipv6-cidr-block "::/0"
    done

    # The following updates all Security Groups in the VPC to allow IPv6 traffic outbound. This occurs on every Security Group, so it may not fit everyone's use case. 
    # Disable if you don't want some Security Groups to allow access to the Internet for IPv6 traffic. Generally we do, so it is enabled by default.
    for SECURITYGROUP in `aws ec2 describe-security-groups --output json --region ${REGION} | grep -A 3 "${VPCID}" | grep -oh "\w*sg-\w*"`; do
      printf "%s\n" "Updating ${SECURITYGROUP} to allow IPv6 traffic. $(aws ec2 describe-security-groups --output json --region ${REGION} --group-id "${SECURITYGROUP}" | grep GroupName)"
      aws ec2 authorize-security-group-ingress --output json --region ${REGION} --group-id ${SECURITYGROUP} --ip-permissions '[{"Ipv6Ranges":[{"CidrIpv6":"::/0"}], "IpProtocol":"-1"}]'
    done

    # Verify that the VPC got an IPv6 assignment.
    aws ec2 describe-vpcs --output json --region ${REGION} --vpc-id ${VPCID} | grep -A 8 "Ipv6CidrBlockAssociationSet"

    printf "%s\n" "Remember to allocate subnets for each VPC or you won't be using any of your assigned CIDR block."
    # aws ec2 associate-subnet-cidr-block --output json --region ${REGION} --subnet-id ${TARGETSUB} --ipv6-cidr-block <::/64>
    # aws ec2 modify-subnet-attribute --output json --region ${REGION} --subnet ${TARGETSUB} --assign-ipv6-address-on-creation
    # aws ec2 modify-subnet-attribute --output json --region ${REGION} --subnet ${TARGETSUB} --map-public-ip-on-launch

    printf "\n"
    printf "%s\n" "----"
    printf "%s\n" "${REGION}: ${VPCID} is now enabled for IPv6!"
    printf "%s\n" "----"

  done

  printf "%s\n" "${REGION} Completed."
  printf "%s\n" "===="
done
