#!/bin/bash

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

calculate_gp2_limits () {       # Calculating limits for Gp2 volume type

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

calculate_io_limits () {

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
echo -e "> Maximum Available throughput is $baseline_throughput "
echo -e "\n+----------------------------------------------------+"
}

############################################################

calculate_st1_limits () {

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
                                if [ $volumeSize -lt 500 ]
                                        then
                                                echo -e "+----------------------------------------------------+\n"
                                                echo -e "> Volume size for st1 can not be less than 500GiB"
                                                echo -e "\n+----------------------------------------------------+"
                                                exit 1
                                fi
                                calculate_burst_tp=$(echo "scale=2; $volumeSize*250/1024;" | bc)                # Calculating burst throughput i.e 250MiB/s per TiB. 
                                burst_tp=$calculate_burst_tp
                                baseline_throughput=$(echo "scale=2; $volumeSize*40/1024;" | bc)                # Calculating baseline throughput i.e 40MiB/s per TiB. 
                                baseline_iops=$baseline_throughput
                        else
                                burst_tp=500
                                calculate_baseline_throughput=$(echo "scale=2; $volumeSize*40/1024;" | bc)
                                baseline_throughput=$(min $calculate_baseline_throughput $max_available_throughput)     # Baseline can not be more than max_available_throughput
                                baseline_iops=$baseline_throughput

                fi
                echo -e "+----------------------------------------------------+\n"
                echo -e "> Maximum Available throughput using burst balance is $burst_tp MiB/s, if burst bucket is empty maximum available throughput will be $baseline_throughput MiB/s "
                echo -e "\n+----------------------------------------------------+"
fi

}

############################################################

calculate_sc1_limits () {

if [ $volumeSize -lt 3200 ]
        then
                if [ $volumeSize -lt 500 ]
                        then
                                echo -e "+----------------------------------------------------+\n"
                                echo -e "> Volume size for sc1 can not be less than 500GiB"c
                                echo -e "\n+----------------------------------------------------+"
                                exit 1
                fi
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
        calculate_gp2_limits                    # Calling gp2 function to calculate maximum limits.
        ;;
        [iI][oO][12])                           # If answer is io1
        echo -e "Enter Provisioned IOPS:"
        read volumeIOPS                        # No need to ask for size for io1/io2 volumes. 
        calculate_io_limits                    # Calling io1 function to calculate maximum limits.
        ;;
        [sS][tT][1])                           # If answer is st1
        echo -e "Enter Volume Size in GiB:"
        read volumeSize
        calculate_st1_limits                    # Calling st1 function to calculate maximum limits.
        ;;
        [sS][cC][1])                           # If answer is sc1
        echo -e "Enter Volume Size in GiB:"
        read volumeSize
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