# echo-api-lambda-proxy

*Respond with the ingested event to echo back what is received. The response is formatted for Lambda Proxy Integration in API Gateway.*

---

This Function is an example of how to respond back to a Lambda Proxy Integration request from API Gateway.  By default, it will echo back the request payload (Lambda event object), but you can easily modify it to respond with a base64 encoded binary payload as well.