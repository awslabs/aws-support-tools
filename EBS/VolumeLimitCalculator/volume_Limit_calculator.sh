#!/bin/bash

########################################################################
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
# 
#     http://aws.amazon.com/apache2.0/
# 
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.


min () { printf '                # calculating minimum of two floating numbers
    define x(a, b) {
        if (a < b) {
           return (a);
        }
        return (b);
     }
     x(%s, %s)
    ' $1 $2 | bc -l
}

max () { printf '                # calculating maximum of two floating numbers
    define x(a, b) {
        if (a > b) {
           return (a);
        }
        return (b);
     }
     x(%s, %s)
    ' $1 $2 | bc -l
}

############################################################

verify_input_as_integers () { 
if ! [[ "$1" =~ ^[0-9]+$ ]]
    then
        echo -e "+----------------------------------------------------+\n"
        echo "> Sorry, volume Size, provisioned IOPS and provisioned throughput needs to be an interger value."
        echo -e "\n+----------------------------------------------------+"
        exit 1
fi
}

############################################################


calculate_gp2_limits () {       # Calculating limits for Gp2 volume type


if [[ $volumeSize -lt 1 || $volumeSize -gt 16384 ]]
    then
        echo -e "+----------------------------------------------------+\n"
        echo -e "> Volume size for $volumeType can not be less than 1GiB or greater than 16384GiB"
        echo -e "\n+----------------------------------------------------+"
        exit 1
fi


if [ $volumeSize -gt 1000 ]
        then
                max_available_iops=16000                # Max IOPS available for this volume type
                max_available_throughput=250            # Max throughput available for this volume type
                calculate_iops=$(( 3*$volumeSize )) 
                baseline_iops=$(min $calculate_iops $max_available_iops)             # Baseline for Gp2 can not be more than max_available_iops
                baseline_throughput=$max_available_throughput   # For volumes greater than 1000GiB, max throughput is always 250MiB/s. 
                echo -e "+----------------------------------------------------+\n"
                echo -e "> Maximum available IOPS are $baseline_iops"
                echo -e "> Maximum Available throughput is $baseline_throughput MiB/s "
                echo -e "\n+----------------------------------------------------+"
        else
                baseline_iops=$(( 3*$volumeSize ))
                burst=3000
                if [ $volumeSize -le 170 ]
                        then
                                max_available_throughput=128                            # Gp2 volumes of size less than 170GiB have a throughput cap at 128MiB/s
                                calculate_iops=$(( 3*$volumeSize )) 
                                baseline_iops=$(max $calculate_iops 100)                # Baseline for Gp2 can not be less than 100. 
                                calculate_tp=$(echo "scale=2; $baseline_iops/4;" | bc)  # Calculating throughput from IOPS with max block size as 256KiB
                                baseline_throughput=$(min $max_available_throughput $calculate_tp)      # Throughput can not exceed max_available_throughput
                                echo -e "+----------------------------------------------------+\n"
                                echo -e "> Maximum Baseline IOPS are $baseline_iops and volume can burst upto $burst IOPS "
                                echo -e "> Maximum Available throughput using burst is $max_available_throughput MiB/s, if burst bucket is empty maximum available throughput will be $baseline_throughput MiB/s "
                                echo -e "\n+----------------------------------------------------+"
                        else
                                max_available_throughput=250
                                calculate_iops=$(( 3*$volumeSize )) 
                                baseline_iops=$calculate_iops
                                calculate_tp=$(echo "scale=2; $baseline_iops/4;" | bc)
                                baseline_throughput=$(min $max_available_throughput $calculate_tp)      # Throughput can not exceed max_available_throughput
                                echo -e "+----------------------------------------------------+\n"
                                echo -e "> Maximum Baseline IOPS are $baseline_iops and volume can burst upto $burst "
                                echo -e "> Maximum Available throughput using burst is $max_available_throughput MiB/s, if burst bucket is empty maximum available throughput will be $baseline_throughput MiB/s "
                                echo -e "\n+----------------------------------------------------+"
                fi
fi

}

############################################################

calculate_gp3_limits () {       # Calculating limits for Gp3 volume type

if [[ $volumeSize -lt 1 || $volumeSize -gt 16384 ]]
    then
        echo -e "+----------------------------------------------------+\n"
        echo -e "> Volume size for $volumeType can not be less than 1GiB or greater than 16384GiB"
        echo -e "\n+----------------------------------------------------+"
        exit 1
fi

if [[ -z $volumeIOPS ]]
    then
        volumeIOPS=3000               # Set IOPS as Baseline(3000) for gp3 volume if it was created using CLI without provisioned IOPS . 
else
    verify_input_as_integers $volumeIOPS
    if [[ $volumeIOPS -lt 3000 || $volumeIOPS -gt 64000 ]]
        then
            echo -e "+----------------------------------------------------+\n"
            echo -e "> Provisioned IOPS can not be less than 3000 or greater than 16000 for Gp3 volume type.."
            echo -e "\n+----------------------------------------------------+"
            exit 1
    elif [[ $((volumeIOPS / volumeSize)) -gt 500 ]]
        then
            echo -e "+----------------------------------------------------+\n"
            echo -e "> Maximum ratio of 500:1 is permitted between IOPS and volume size for Gp3 volume type."
            echo -e "\n+----------------------------------------------------+"
            exit 1
    fi
fi

if [[ -z $volumeThroughput ]]
    then
        volumeThroughput=125               # Set Throughput as Baseline(125MiB/s) for gp3 volume if it was created using CLI without provisioned Throughput . 
else
    verify_input_as_integers $volumeThroughput
    if [[ $volumeThroughput -lt 125 || $volumeThroughput -gt 1000 ]]
        then
            echo -e "+----------------------------------------------------+\n"
            echo -e "> Provisioned throughput can not be less than 125MiB/s or greater than 1000MiB/s for Gp3 volume type.."
            echo -e "\n+----------------------------------------------------+"
            exit 1
    elif [[ $((volumeIOPS / volumeThroughput)) -lt 4 ]]
        then
            echo -e "+----------------------------------------------------+\n"
            echo -e "> Maximum ratio of 0.25:1 is permitted between Throughput (MiBps) and IOPS for Gp3 volume type."
            echo -e "\n+----------------------------------------------------+"
            exit 1
    fi
fi

echo -e "+----------------------------------------------------+\n"
echo -e "> Maximum available IOPS for your volume are $volumeIOPS"
echo -e "> Maximum Available throughput is $volumeThroughput MiB/s"
echo -e "\n+----------------------------------------------------+"
}
############################################################

calculate_io_limits () {

if [[ $volumeIOPS -lt 100 || $volumeIOPS -gt 64000 ]]
    then
        echo -e "+----------------------------------------------------+\n"
        echo -e "> Provisioned IOPS can not be less than 100 or greater than 64000."
        echo -e "\n+----------------------------------------------------+"
        exit 1
fi


if [ $volumeIOPS -le 32000 ]
        then
                max_available_throughput=500                            # io1/io2 Volumes with less than equal to 32000 provisioned IOPS can achieve 500MiB/s of throughput at max. 
                calculate_tp=$(echo "scale=2; $volumeIOPS/4;" | bc)
                baseline_throughput=$(min $max_available_throughput $calculate_tp)
        else
                max_available_throughput=1000
                calculate_tp=$(echo "scale=2; $volumeIOPS/64;" | bc)    # io1/io2 volume provisioned with more than 32,000 IOPS supports a maximum I/O size of 16 KiB
                baseline_throughput=$(min $max_available_throughput $calculate_tp)

fi
echo -e "+----------------------------------------------------+\n"
echo -e "> Maximum available IOPS are equal to the provisioned IOPS i.e $volumeIOPS"
echo -e "> Maximum Available throughput is $baseline_throughput MiB/s"
echo -e "\n+----------------------------------------------------+"
}

############################################################

calculate_st1_limits () {

if [[ $volumeSize -lt 500 || $volumeSize -gt 16384 ]]
        then
                echo -e "+----------------------------------------------------+\n"
                echo -e "> Volume size for $volumeType can not be less than 500GiB or greater than 16384GiB"
                echo -e "\n+----------------------------------------------------+"
                exit 1
fi

if [ $volumeSize -gt 12800 ]
        then
                max_available_iops=500
                max_available_throughput=500
                baseline_iops=$max_available_iops
                baseline_throughput=$max_available_throughput
                echo -e "+----------------------------------------------------+\n"
                echo -e "> Maximum Available throughput is $baseline_throughput MiB/s. To achieve this throughput, IO size should be 1MiB"
                echo -e "\n+----------------------------------------------------+"
        else
                if [ $volumeSize -lt 2048 ]
                        then
                                calculate_burst_tp=$(echo "scale=2; $volumeSize*250/1024;" | bc)                # Calculating burst throughput i.e 250MiB/s per TiB. 
                                burst_tp=$calculate_burst_tp
                                baseline_throughput=$(echo "scale=2; $volumeSize*40/1024;" | bc)                # Calculating baseline throughput i.e 40MiB/s per TiB. 
                                baseline_iops=$baseline_throughput
                        else
                                burst_tp=500
                                calculate_baseline_throughput=$(echo "scale=2; $volumeSize*40/1024;" | bc)
                                baseline_throughput=$calculate_baseline_throughput 
                                baseline_iops=$baseline_throughput

                fi
                echo -e "+----------------------------------------------------+\n"
                echo -e "> Maximum Available throughput using burst balance is $burst_tp MiB/s, if burst bucket is empty maximum available throughput will be $baseline_throughput MiB/s "
                echo -e "\n+----------------------------------------------------+"
fi

}

############################################################

calculate_sc1_limits () {

if [[ $volumeSize -lt 500 || $volumeSize -gt 16000 ]]
        then
                echo -e "+----------------------------------------------------+\n"
                echo -e "> Volume size for $volumeType can not be less than 500GiB or greater than 16000GiB"
                echo -e "\n+----------------------------------------------------+"
                exit 1
fi

if [ $volumeSize -lt 3200 ]
        then
                calculate_burst_tp=$(echo "scale=2; $volumeSize*80/1024;" | bc)                 # Calculating burst throughput i.e 80MiB/s per TiB. 
                burst_tp=$calculate_burst_tp
                baseline_throughput=$(echo "scale=2; $volumeSize*12/1024;" | bc)                # Calculating burst throughput i.e 12MiB/s per TiB. 
                baseline_iops=$baseline_throughput
        else
                burst_tp=250
                calculate_baseline_throughput=$(echo "scale=2; $volumeSize*12/1024;" | bc)
                baseline_throughput=$calculate_baseline_throughput
                baseline_iops=$baseline_throughput

fi
echo -e "+----------------------------------------------------+\n"
echo -e "> Maximum Available throughput using burst balance is $burst_tp MiB/s, if burst bucket is empty maximum available throughput will be $baseline_throughput MiB/s "
echo -e "\n+----------------------------------------------------+"
}

############################################################


PATH=/bin:/sbin:/usr/bin:/usr/sbin

echo -e "Enter Volume Type:"
read volumeType

case "$volumeType" in
        [gG][pP][2])                           # If answer is gp2
        echo -e "Enter Volume Size in GiB:"
        read volumeSize
        verify_input_as_integers $volumeSize
        calculate_gp2_limits                    # Calling gp2 function to calculate maximum limits.
        ;;
        [gG][pP][3])                           # If answer is gp2
        echo -e "Enter Volume Size in GiB:"
        read volumeSize
        verify_input_as_integers $volumeSize
        echo -e "Enter Provisioned IOPS, if volume was created via CLI without provisioned IOPS please press Enter:"
        read volumeIOPS
        echo -e "Enter Provisioned Throughput, if volume was created via CLI without provisioned Throughput please press Enter:"
        read volumeThroughput
        calculate_gp3_limits                    # Calling gp2 function to calculate maximum limits.
        ;;
        [iI][oO][12])                           # If answer is io1
        echo -e "Enter Provisioned IOPS:"
        read volumeIOPS
        verify_input_as_integers $volumeIOPS                        # No need to ask for size for io1/io2 volumes. 
        calculate_io_limits                    # Calling io1 function to calculate maximum limits.
        ;;
        [sS][tT][1])                           # If answer is st1
        echo -e "Enter Volume Size in GiB:"
        read volumeSize
        verify_input_as_integers $volumeSize
        calculate_st1_limits                    # Calling st1 function to calculate maximum limits.
        ;;
        [sS][cC][1])                           # If answer is sc1
        echo -e "Enter Volume Size in GiB:"
        read volumeSize
        verify_input_as_integers $volumeSize
        calculate_sc1_limits                    # Calling sc1 function to calculate maximum limits.
        ;;
        *)
        echo -e "+----------------------------------------------------+\n"
        echo "> Please enter correct Volume Type. Also note that the script is not supported for standard volume type."
        echo -e "\n+----------------------------------------------------+"
        ;;

esac
############################################################
############################################################