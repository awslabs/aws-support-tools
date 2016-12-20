
SNS Fast Publish Lambda Function
--------------------------------
This function demonstrates how to use S3 put event to trigger a Lambda function which picks up the dropped device endpoint list and publishes notification to at a very fast rate.

Usage:
------
1. Deploy this function with timeout setting of 5 minutes. Make sure the lambda Role has
   S3 **read/write** permissions to the bucket and SNS publish permission. Configure Lambda environment variables e.g `REGION=us-east-1`, `THREADS=1000`, `LOG_TIME=1`
2. Create a S3 bucket and set up events for **PUT** to trigger this lambda function.
3. In the S3 events configuration, set the event suffix to `.gz`.
4. Create a payloads file i.e `endpoint_list_14032016.json` with contents in the below json format.
    
    ```json
    {
     "Endpoints": [
       {
         "EndpointArn": "arn:aws:sns:us-west-2:1111122222:endpoint/GCM/MyApp/55a1ffbf-aefc-3e7a-bd84-3af5bca4fc63",
         "Message": "{\\\"data\\\": { \\\"message\\\": \\\"Test from Lambda.\\\", \\\"title\\\": \\\"Test\\\"}}"
       }
     ]
    }
    
    ```
5. If sending the same message to all endpoints, use the following json format.

    ```json
    {
     "SameMessage": true,
     "Message": "{\\\"data\\\": { \\\"message\\\": \\\"Same message to all endpoints.\\\", \\\"title\\\": \\\"Test\\\"}}",
     "Endpoints": [
       {
         "EndpointArn": "arn:aws:sns:us-west-2:1111122222:endpoint/GCM/MyApp/55a1ffbf-aefc-3e7a-bd84-3af5bca4fc63"
       }
     ]
    }
    
    ```
6. Compress the file using gzip. e.g `gzip -kf endpoint_list_14032016.json' creates 'endpoint_list_14032016.json.gz`
7. Upload the file `endpoint_list_14032016.json.gz` to the S3 bucket which will trigger this lambda function.
8. This function will publish to all endpoints in the json file and log failures in `<FILENAME>_error.log`.

**Tip:** Publish even faster by distributing endpoints across multiple smaller json files when the number
of endpoints exceed over a few 100,000s or increase `max_threads` variable value to something higher.
