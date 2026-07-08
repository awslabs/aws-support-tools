# curl_for_latency

_Bash script for checking latency when communicating with API Gateway through CloudFront._

---

This script will execute three (3) requests to the endpoint at two (2) second intervals. The results show the total time taken for the request and response, and the time for each step. Descriptions are included for what is occurring.

The initial request will take the longest, after which time the `time_connect` and `time_appconnect` will be 0 as a TCP connection is re-used between requests.

## Requirements

### The script `curl_for_latency.sh` requires the following arguments.

You will need to supply the request method and URL:

```
./curl_for_latency.sh GET https://1234567890.execute-api.us-west-2.amazonaws.com/stage/resource
```

### The script `curl_for_latency.sh` may require some modifications, dependant on your API configuration.

There are various parameters you may want to change on this example script:

- The request method from POST to GET
- Removing (or adjusting) the 2 second interval between requests by altering the `--rate 30/m` argument
- Adding cache-busting query strings to each request. You may consider adding `?nocaching=$(uuidgen)` into the URLs that are called by doing `-X POST "$2?nocaching=$(uuidgen)" "$2?nocaching=$(uuidgen)" "$2?nocaching=$(uuidgen)"`
- Adding custom authentication headers by including them below the verbose option `-v` as `-H 'header-key:value'`
