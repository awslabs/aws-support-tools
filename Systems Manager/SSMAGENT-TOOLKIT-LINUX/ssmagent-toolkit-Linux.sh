#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  
#
#!/bin/bash


# Diagnostic Test Function

runtests()
{

echo "
    ___ _       _______    _____            __                         __  ___                                 
   /   | |     / / ___/   / ___/__  _______/ /____  ____ ___  _____   /  |/  /___ _____  ____ _____ ____  _____
  / /| | | /| / /\__ \    \__ \/ / / / ___/ __/ _ \/ __ '__ \/ ___/  / /|_/ / __ '/ __ \/ __ '/ __ '/ _ \/ ___/
 / ___ | |/ |/ /___/ /   ___/ / /_/ (__  ) /_/  __/ / / / / (__  )  / /  / / /_/ / / / / /_/ / /_/ /  __/ /    
/_/  |_|__/|__//____/   /____/\__, /____/\__/\___/_/ /_/ /_/____/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/     
                             /____/                                                         /____/             

"

    Region=$fetchregion
    METADATA_URL=169.254.169.254
    ec2end=ec2messages.$Region.amazonaws.com
    ssmend=ssm.$Region.amazonaws.com
    ssmmessagesend=ssmmessages.$Region.amazonaws.com
    HTTPSPORT=443
    HTTPPORT=80
    TIMEOUT=1

    printf "Check|Value|Note\n" >> /tmp/ssmtoolkitscript-output.txt
    echo "-----|-----|-----" >> /tmp/ssmtoolkitscript-output.txt
    echo "   |    |    |" >> /tmp/ssmtoolkitscript-output.txt

    #-------Test1-------

    Test1="Testing metadata endpoint"
    echo " "
    curl -s --connect-timeout 5 http://169.254.169.254/ > /dev/null
    exitcode=$?
    if [ $exitcode -ne 0 ]; then
        Result1="Fail"
        Note1="Couldn't connect to http://169.254.169.254. Possible issue could be proxy"
    else
    	Result1="Pass"
        Note1="Connected to http://169.254.169.254"    
    fi
    printf "$Test1|$Result1|$Note1\n" >> /tmp/ssmtoolkitscript-output.txt


    #-------Test2-------

    Test2="Getting IAM Role Attached"
    IAM_ROLE=$(curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    if [[ $IAM_ROLE == *"Not Found"* ]];then
     Result2="Not Found"
    else
     Result2="$IAM_ROLE"
    fi
    Note2="Ensure the Amazon Managed Policy,AmazonSSMManagedInstanceCore is attached to the Role."
    printf "$Test2|$Result2|$Note2\n"  >> /tmp/ssmtoolkitscript-output.txt


    #-------Test3-------

    Test3="Testing ec2messages endpoint Connectivity"
	timeout 3 bash -c "cat < /dev/null > /dev/tcp/$ec2end/443"
	exitcode=$?
    if [ $exitcode -eq 0 ]; then
		Result3="Pass"
        Note3="Connected to $ec2end."
    elif [ $exitcode -eq 124 ]; then
        Result3="Fail"
        Note3="Couldn't connect to $ec2end. Check the Security group and NACL configuration."
    else
        Result3="Fail"
        Note3="Check if DNS is working"         
    fi
    printf "$Test3|$Result3|$Note3\n" >> /tmp/ssmtoolkitscript-output.txt
    

    #-------Test4-------
    Test4="Testing SSM endpoint Connectivity"
	timeout 3 bash -c "cat < /dev/null > /dev/tcp/$ssmend/443"
	exitcode=$?
    if [ $exitcode -eq 0 ]; then
		Result4="Pass"
        Note4="Connected to $ssmend."
    elif [ $exitcode -eq 124 ]; then
        Result4="Fail"
        Note4="Couldn't connect to $ssmend. Check the Security group and NACL configuration."
    else
        Result4="Fail"
        Note4="Check if DNS is working"         
    fi
    printf "$Test4|$Result4|$Note4\n" >> /tmp/ssmtoolkitscript-output.txt

    #-------Test5-------

    Test5="Testing ssmmessages endpoint Connectivity"
	timeout 3 bash -c "cat < /dev/null > /dev/tcp/$ssmmessagesend/443"
	exitcode=$?
    if [ $exitcode -eq 0 ]; then
		Result5="Pass"
        Note5="Connected to $ssmmessagesend."
    elif [ $exitcode -eq 124 ]; then
        Result5="Fail"
        Note5="Couldn't connect to $ssmmessagesend. Check the Security group and NACL configuration."
    else
        Result5="Fail"
        Note5="Check if DNS is working"         
    fi
    printf "$Test5|$Result5|$Note5\n" >> /tmp/ssmtoolkitscript-output.txt
    
	#-------Test6-------

    Test6="SSM agent Service Running"
    SSMAGENTISSUE="https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-manual-agent-install.html"
    if [ -f /usr/bin/yum ] || [ -f /usr/bin/zypper ]; # For Redhat Variants
    then 
     Test6="SSM agent service status"
     rpm -qa | grep amazon-ssm-agent > /dev/null 2>/dev/null
     if [ $? -ne 0 ];then
      Result6="Not Installed"
      Note6="$SSMAGENTISSUE"
     else
      is_running=$(ps aux | grep -v grep | grep -w amazon-ssm-agent | wc -l | awk '{print $1}')
      if [ $is_running != "0" ]; then
       Result6="Active"
       Note6="N/A"
      else
       Result6="Inactive"
       Note6="$SSMAGENTISSUE"
      fi      
     fi
    elif [ -f /etc/debian_version ];then #For Ubuntu. Covering both snap and dpkg installation types.
     if [ -f /usr/bin/snap ];
     then
      snap info amazon-ssm-agent > /dev/null 2>/dev/null
      if [ $? -eq 0 ];then
       snap services amazon-ssm-agent.amazon-ssm-agent | grep -w "active" > /dev/null 2>/dev/null
       if [ $? -eq 0 ];then
        Result6="Active"
        Note6="N/A"
       else
        Result6="Inactive"
        Note6="$SSMAGENTISSUE"
       fi 
      else
       Result6="Not Installed."
       Note6="$SSMAGENTISSUE"
      fi
     else
      if [ $(dpkg-query -W -f='${Status}' amazon-ssm-agent 2>/dev/null | grep -c "ok installed") -eq 1 ];
      then
       Result6=`systemctl is-active  amazon-ssm-agent`
      else
       Result6="Not Installed"
       Note6="$SSMAGENTISSUE"
      fi
     fi
    else
     Results6="Unable to determine OS"
     Note6="$SSMAGENTISSUE"
    fi 
    printf "$Test6|$Result6|$Note6\n" >> /tmp/ssmtoolkitscript-output.txt

    #-------Test7-------
    Test7="SSM Agent Proxy Settings"
    Proxy_doc="No Proxy variables found for ssm agent. Refer : https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-proxy-with-ssm-agent.html"
    if [[ $Result6 = "Not Installed" ]] || [[ $Result6 = "Unable to determine OS" ]];then
        Results7="Skipped"
        Note7="SSM Agent not present. Skipping this test.."
        printf "$Test7|$Results7|$Note7\n" >> /tmp/ssmtoolkitscript-output.txt 
    else    
        sudo xargs --null --max-args=1 < /proc/$(pidof amazon-ssm-agent)/environ | grep -e "http_proxy" > /dev/null 2>/dev/null
        if [ $? -eq 0 ];then
            Results7a=`sudo xargs --null --max-args=1 < /proc/$(pidof amazon-ssm-agent)/environ | grep -e "http_proxy"`
            Note7=N/A
        else
            Results7a="http_proxy=NULL"
            Note7=$Proxy_doc
        fi
        sudo xargs --null --max-args=1 < /proc/$(pidof amazon-ssm-agent)/environ | grep -e "https_proxy" > /dev/null 2>/dev/null
        if [ $? -eq 0 ];then
            Results7b=`sudo xargs --null --max-args=1 < /proc/$(pidof amazon-ssm-agent)/environ | grep -e "https_proxy"`
            Note7=N/A
        else
            Results7b="http_proxys=NULL"
            Note7=$Proxy_doc
        fi
        sudo xargs --null --max-args=1 < /proc/$(pidof amazon-ssm-agent)/environ | grep -e "no_proxy" > /dev/null 2>/dev/null
        if [ $? -eq 0 ];then
            Results7c=`sudo xargs --null --max-args=1 < /proc/$(pidof amazon-ssm-agent)/environ | grep -e "no_proxy"`
            Note7=N/A
        else
            Results7c="no_proxy=NULL"
            Note7=$Proxy_doc
        fi
        printf "$Test7|$Results7a,$Results7b,$Results7c|$Note7\n" >> /tmp/ssmtoolkitscript-output.txt
    fi


    #-------Test8-------

    Test8="System Wide Proxy Settings"
    env | grep -e "http_proxy" > /dev/null 2>/dev/null
    if [ $? -eq 0 ];then
     Results8a=`env | grep -e "http_proxy"`
     Note8=N/A
    else
     Results8a="http_proxy=NULL"
     Note8="No System wide proxy settings detected"
    fi
    env | grep -e "https_proxy" > /dev/null 2>/dev/null
    if [ $? -eq 0 ];then
     Results8b=`env | grep -e "https_proxy"`
     Note8=N/A
    else
     Results8b="https_proxy=NULL"
     Note8="No System Wide proxy settings detected"
    fi
    env | grep -e "no_proxy" > /dev/null 2>/dev/null
    if [ $? -eq 0 ];then
     Results8c=`env | grep -e "no_proxy"`
    else
     Results8c="no_proxy=NULL"
    fi
    printf "$Test8|$Results8a,$Results8b,$Results8c|$Note8\n" >> /tmp/ssmtoolkitscript-output.txt
      


    #-------Test9------

    Test9="Nameservers(DNS) configured on the server"
    nameservers=($(cat /etc/resolv.conf  | grep -v '^#' | grep nameserver | awk '{print $2}'))
    if [ ${#nameservers[@]} -eq 0 ]; then
        Results9="Fail"
        Note9="No DNS servers found in /etc/resolv.conf"
    else
        Results9=${nameservers[@]}
        Note9="DNS servers found in /etc/resolv.conf"
    fi    
    printf "$Test9|$Results9|$Note9\n" >> /tmp/ssmtoolkitscript-output.txt


    #-------Test10------

    Test10=""Resolving" $ssmend"
    ip=($(dig +short $ssmend))
    if (( ${#ip[@]} ));then
     Results10=${ip[@]}
     Note10="N/A"
    else
     Results10="Null"
     Note10="Couldnt resolve $ssmend. Check if DNS is working."
    fi
    printf "$Test10|$Results10|$Note10\n" >> /tmp/ssmtoolkitscript-output.txt

    #-------Test11------

    Test11="Checking for Hybrid Activation"
    hybrid_doc="https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-managedinstances.html"
    if [ -f /var/lib/amazon/ssm/Vault/Store/RegistrationKey ]
    then
     hybrid_instance_id=`cat /var/lib/amazon/ssm/Vault/Store/RegistrationKey | tr -d '{}' | cut '-d"' -f4`
     Results11=$hybrid_instance_id
     Note11="RegistrationKey file exist. The Instance is registered with Hybrid activation."
    else
     Results11="Instance not registered with Hybrid Activation."
     Note11="Ref: $hybrid_doc" 
    fi
    printf "$Test11|$Results11|$Note11\n" >> /tmp/ssmtoolkitscript-output.txt 
    cat /tmp/ssmtoolkitscript-output.txt  | column -t -s "|"
    rm -rf /tmp/ssmtoolkitscript-output.txt
    echo " "
}

# Function to collect Logs

CollectLogs()
{
read -t 4 -p "Press S for SSM agent Logs. Press R for Run Command Logs. Values are case sensitive: " REPLY
echo "No Input Provided. The default value is ${REPLY:=S}. Collecting SSM Agent logs.."

if [ $REPLY == "S" ];then
 tar -cf AWS_SSMLOGS_$(date +%F).tar --absolute-names /var/log/amazon/ssm/ --exclude='/var/log/amazon/ssm/download'
 echo "Logs stored in the current working directory : AWS_SSMLOGS_$(date +%F).tar"
elif [ $REPLY == "R" ];then
 echo -n "Enter the Command execution ID: ";
 read;
 ExecID=$REPLY
 instance=`curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/instance-id`
 #check logs exist
 if [ -e /var/lib/amazon/ssm/$instance/document/orchestration/$ExecID/ ];then
  tar -cf AWS_RunCommand_Logs_$ExecID.tar  --absolute-names /var/lib/amazon/ssm/$instance/document/orchestration/$ExecID/
  echo "Logs stored in the current working directory : AWS_RunCommand_Logs_$ExecID.tar"
 else
  echo "Logs cannot be found for the execution id provided" 
 fi
else
 echo "Wrong input provided"
fi  
}

# Help function

GetHelp()
{
   # Display Help
   echo "Description of the script options here."
   echo
   echo "Syntax: ssmagent-toolkit-Linux.sh [-h|r|l]"
   echo "options:"
   echo "-h     Print this Help."
   echo -e "-r     Enter Region. Useful with On-Premise/Hybrid Instances."
   echo "-l     Collect Logs."
   echo ""
   echo -e  "Examples: "
   echo -e "1) To run the Test: \n \t ssmagent-toolkit-Linux.sh \n"
   echo -e "2) To run the Test with us-east-1 region: \n \t ssmagent-toolkit-Linux.sh -r us-east-1\n"
   echo -e "3) To Collect SSM Agent Logs \n \t ssmagent-toolkit-Linux.sh -l \n"

}



# Process the input options. Add options as needed. 
# Get the options

while getopts ":hr:ld" option; do
 case $option in
  h)
    GetHelp
    ;;
  r)
    regions_list="us-east-1 us-east-2 us-west-1 us-west-2 af-south-1 ap-east-1 ap-south-1 ap-northeast-3 ap-northeast-2 ap-northeast-1 ap-southeast-1 ap-southeast-2 ca-central-1 cn-north-1 cn-northwest-1 eu-central-1 eu-west-1 eu-west-2 eu-west-3 eu-south-1 eu-north-1 sa-east-1 us-gov-east-1 us-gov-west-1"
    for item in $regions_list; do
    if [ "$OPTARG" = "$item" ]
    then
     fetchregion=$OPTARG
    fi
    done
        
    if [ -z "$fetchregion" ]
    then
     echo "The region entered does not exist. Please provide correct AWS Region."
     exit 1
    else
      runtests $fetchregion
    fi
    ;;    

  l)
    CollectLogs
    ;;
  :)
    echo "Error: Missing option argument for -$OPTARG" >&2; 
    exit 1
    ;;
  
  ?)
    echo "Error: Invalid option was specified -$OPTARG. Use -h for help menu.";;
  
  esac
done

if ((OPTIND == 1))
then
  curl -s --connect-timeout 5 http://169.254.169.254/  > /dev/null
  exitcode=$?
  if [ $exitcode -ne 0 ]; then
   echo "Metadata URL is not accessible. Possible issue could be proxy. Alternatively, you can run this test with -r option to specify the region."
  else
    fetchregion=$(curl -s --connect-timeout 5 http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | cut -d " " -f5 | tr -d '",')
    runtests $fetchregion
  fi  
fi
