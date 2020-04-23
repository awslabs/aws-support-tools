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

set -e

readyn() {
    local input=
    while true; do
        read -p "$* " input
        case $input in
            [yY]) echo true; return;;
            [nN]) echo false; return;;
            *) echo 'Invalid input. Valid inputs are "y" or "n".' >&2;;
        esac
    done
}

calc() {
    printf %s\\n "$*" | bc
}

if command -v gdate >/dev/null; then
    date() { command gdate "$@"; }
fi

# Taking Input parameters from the user
read -p "Enter the local path of the file you want to upload: " filename
read -p "Enter the destination file name: " s3_filename
read -p "Enter the name of the bucket: " bucketname
read -p "Enter the region of your Bucket (e.g. us-west-2): " region

use_acceleration=$(readyn 'Do you want to upload via Transfer Acceleration: (y/n)')

filesize="$(wc -c <"$filename")"
starttime=$(date +"%s.%N")
if $use_acceleration; then
    # Uploading the file to the S3 Bucket using Transfer Acceleration.
    use_acceleration_str="with acceleration"
    aws configure set s3.addressing_style virtual
    aws s3 cp "$filename" "s3://$bucketname/$s3_filename" --region "$region" --endpoint-url http://s3-accelerate.amazonaws.com
else
    # Uploading the file to the S3 Bucket via a Direct upload.
    use_acceleration_str="without acceleration"
    aws s3 cp "$filename" "s3://$bucketname/$s3_filename" --region "$region"
fi
endtime=$(date +"%s.%N")
time_elapsed=$(calc "$endtime-$starttime")
throughput=$(calc "$filesize*8/$time_elapsed")
throughput_in_mbps=$(calc "$throughput/(1024*1024)")
echo "File uploaded $use_acceleration_str at $throughput_in_mbps Mbps speed."

delete_file=$(readyn 'Do you want to delete the uploaded file: (y/n)')
if $delete_file; then
    aws s3 rm "s3://$bucketname/$s3_filename" --region "$region"
fi
