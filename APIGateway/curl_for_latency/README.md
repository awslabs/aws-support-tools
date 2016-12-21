# curl_for_latency

*Bash script for checking latency when communicating with API Gateway through CloudFront.*

----

This script will execute three (3) requests to the endpoint at two (2) second intervals.  The results show the total time taken for the request and response, and the time for each step.  Descriptions are included for what is occurring.

## Requirements

* The script `curl_for_latency.sh` requires the following modifications.
  * Replace the `method` and `URL` in the curl command
    * *-X `GET` `"https://1234567890.execute-api.us-west-2.amazonaws.com/stage/resource?nocaching=$(uuidgen)"`*
  * Optional: Add custom headers by including them below the verbose option `-v` as `-H 'header-key:value'`