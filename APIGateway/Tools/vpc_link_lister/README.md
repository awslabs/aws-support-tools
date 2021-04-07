A Python Lambda function to iterate over the API Gateway REST API vpclinks and list the associated NLB and associated API/Resource/Method/Integration using the vpclink.

To make sure Lambda Function is able to run successfully you would need to provide your function a minimum of following permissions

```
"Effect": "Allow",
"Action": [
    "apigateway:GET"
],
"Resource": [
    "arn:aws:apigateway:REGION::/restapis",
    "arn:aws:apigateway:REGION::/restapis/*",
    "arn:aws:apigateway:REGION::/vpclinks"
]
``` 


Output will look like following:
```
LISTING Resources attached to VPClINK ID mtc1oo 
Associated NLB is ['arn:aws:elasticloadbalancing:ap-southeast-2:xxxxxxxx:loadbalancer/net/NLBAPIGW/576527bf6f9b8c41']
    LISTING FOR API = 5f8xxxxw42
    LISTING FOR API = 6g8xxxxcqi
    LISTING FOR API = 3grxxxxjvl
        API ID='3grxxxxjvl'   Resource ID='gjg60r'   Resource Path='/locations/{Id}/phonenumbers'   HttpMethod='GET' ConnectionType='VPC_LINK' ConnectionId='mtc1oo'
        API ID='3grxxxxjvl'   Resource ID='gjg60r'   Resource Path='/locations/{Id}/phonenumbers'   HttpMethod='POST' ConnectionType='VPC_LINK' ConnectionId='mtc1oo'
        API ID='3grxxxxjvl'   Resource ID='h1o5b3'   Resource Path='/locations/{Id}'   HttpMethod='DELETE' ConnectionType='VPC_LINK'ConnectionId='mtc1oo'
```
