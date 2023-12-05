#!/usr/bin/env bash

# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.


# Created by Andrew R. DeFilippis


# Read into a variable, the block of "curl timing output" text
read -r -d '' TIME_DATA << EOV
\n         ---------Operation is beginning---------
      url_effective :  '%{url_effective}' <-- (The URL that was fetched last.)
          http_code :  %{http_code} <-- (The numerical response code that was found in the last retrieved HTTP(S) or FTP(s) transfer.)
       content_type :  '%{content_type}' <-- (The Content-Type of the requested document, if there was any.)\n
         ---------Local DNS resolution beginning---------
    time_namelookup :  %{time_namelookup} <-- (The time, in seconds, it took from the start until the DNS name resolution was completed.)\n
         ---------Connection to CloudFront beginning---------
       time_connect :  %{time_connect} <-- (The time, in seconds, it took from the start until the TCP connect to the remote host (or proxy) was completed.)
    time_appconnect :  %{time_appconnect} <-- (The time, in seconds, it took from the start until the SSL/SSH/etc connect/handshake to the remote host was completed.)\n
         ---------Communication between CloudFront and API Gateway (via Internet backbone networks) beginning---------
   time_pretransfer :  %{time_pretransfer} <-- (The time, in seconds, it took from the start until the file transfer was just about to begin.)
      time_redirect :  %{time_redirect} <-- (The time, in seconds, it took for all redirection steps before the final transaction was started.)\n
         ---------NOTE: Communication between API Gateway and the Integration Request Endpoint occurring---------
         ---------NOTE: Communication between API Gateway and CloudFront (via Internet backbone networks) occurring---------\n
         ---------Response from CloudFront beginning---------
 time_starttransfer :  %{time_starttransfer} <-- (The time, in seconds, it took from the start until the first byte was just about to be transferred.)
      size_download :  %{size_download} <-- (The total amount of bytes that were downloaded.)\n
         ---------Response has been received---------
         time_total :  %{time_total} <-- (The total time, in seconds, that the full operation lasted.)
         ---------Operation is complete---------\n
EOV


# Execute the curl command
curl \
   --rate 30/m \
   -w "$TIME_DATA" \
   -o /dev/null \
   -s \
   -v \
   -X $1 "$2" "$2" "$2"