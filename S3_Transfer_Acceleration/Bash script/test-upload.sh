#! /bin/bash

: <<'END'
Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS"
BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under the License.
END

# Error handling of the script.This comamnd makes sure that the script will stop and exit if there is an error.
set -e

# Taking Input parameters from the user
echo -n "Enter the local path of the file you want to upload: "
read FILENAME
echo -n "Enter the destination file name: "
read S3_FILENAME
echo -n "Enter the name of the bucket:"
read bucketname
echo -n "Enter the region of your Bucket (e.g. us-west-2): "
read region
i=1
while [ $i -gt 0 ]
do
    echo -n "Do you want to upload via Transfer Acceleration: (y/n) "
    read input

    if [ $input == "y" ] || [ $input == "n" ]
    # Uploading the file to the S3 Bucket via a Direct upload.
    then
        if [ $input == "n" ]
        then
            FILESIZE="$(wc -c <"$FILENAME")"
            STARTTIME=$(date +"%s.%N")
            #echo "start-time-1:$STARTTIME"
            STARTTIME_us=$(expr $STARTTIME*$((1000000)) | bc -l)
            #echo "start-time-2:$STARTTIME_us"
            aws s3 cp $FILENAME s3://$bucketname/$S3_FILENAME --region $region
            ENDTIME=$(date +"%s.%N")
            #echo "end-time-1:$ENDTIME"
            ENDTIME_us=$(expr $ENDTIME*$((1000000)) | bc -l)
            #echo "end-time-2:$ENDTIME_us"
            Time_elapsed=$(expr $ENDTIME_us-$STARTTIME_us | bc -l)
            #echo "Time_elapsed:$Time_elapsed"
            Throughput=$(expr $(($FILESIZE*8))/$Time_elapsed | bc -l)
            Throughput_in_Mbps=$(expr $Throughput/$((1024*1024)) | bc -l)
            echo "File uploaded without acceleration at $(expr $Throughput_in_Mbps*$((1000000)) | bc -l) Mbps speed."
            i=$(( i-1 ))
            j=1
            # Taking user input to check whether the user wants to delete the uploaded file.
            while [ $j -gt 0 ]
            do
                echo -n "Do you want to delete the uploaded file: (y/n) "
                read input_1

                if [ $input_1 == "y" ] || [ $input_1 == "n" ]
                then
                    if [[ $input_1 == "y"  ]]; then
                        aws s3 rm s3://$bucketname/$S3_FILENAME --region $region
                        j=$(( j-1 ))
                    else
                        j=$(( j-1 ))
                    fi
                else
                    echo "Invalid input.Valid inputs are 'y' or 'n'."
                fi
            done



        # Uploading the file to the S3 Bucket via a Transfer Acceleration.
        else
            FILESIZE="$(wc -c <"$FILENAME")"
            STARTTIME=$(date +"%s.%N")
            STARTTIME_us=$(expr $STARTTIME*$((1000000)) | bc -l)
            aws configure set s3.addressing_style virtual
            aws s3 cp $FILENAME s3://$bucketname/$S3_FILENAME --region $region --endpoint-url http://s3-accelerate.amazonaws.com
            ENDTIME=$(date +"%s.%N")
            ENDTIME_us=$(expr $ENDTIME*$((1000000)) | bc -l)
            Time_elapsed=$(expr $ENDTIME_us-$STARTTIME_us | bc -l)
            Throughput=$(expr $(($FILESIZE*8))/$Time_elapsed | bc -l)
            Throughput_in_Mbps=$(expr $Throughput/$((1024*1024)) | bc -l)
            echo "File uploaded with acceleration at $(expr $Throughput_in_Mbps*$((1000000)) | bc -l) Mbps speed."
            i=$(( i-1 ))
            k=1
            # Taking user input to check whether the user wants to delete the uploaded file.
            while [ $k -gt 0 ]
            do
                echo -n "Do you want to delete the uploaded file: (y/n) "
                read input_1

                if [ $input_1 == "y" ] || [ $input_1 == "n" ]
                then
                    if [[ $input_1 == "y"  ]]; then
                        aws s3 rm s3://$bucketname/$S3_FILENAME --region $region
                        k=$(( k-1 ))
                    else
                        k=$(( k-1 ))
                    fi
                else
                    echo "Invalid input.Valid inputs are 'y' or 'n'."
                fi
            done


        fi
    else
        echo "Invalid input.Valid inputs are 'y' or 'n'."
    fi
done
