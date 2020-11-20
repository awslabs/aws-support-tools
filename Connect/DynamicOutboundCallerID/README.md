# Connect - Country-based Dynamic Outbound Caller ID

An AWS Lambda function to be put in an outbound whisper flow in an Amazon Connect instance, that allows one to use different caller ID based on destination country.

## External Dependencies

- [`phonenumbers`](https://pypi.org/project/phonenumbers/)

### How to install external dependencies?

- Creating a function deployment package by following the documentation [here](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-dependencies).
- Creating a Lambda layer by following the documentation [here](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-path).

## Internal Dependencies

The following libraries are included in AWS Lambda Python runtimes:
- `json`
- `os`
- `logging`
- `boto3`
- `botocore`
- `re`

## Example Lambda Event

Amazon Connect sends the following payload to Lambda function inside a contact flow:

```
{
    "Details": {
        "ContactData": {
            "Attributes": {},
            "Channel": "VOICE",
            "ContactId": "4a573372-1f28-4e26-b97b-XXXXXXXXXXX",
            "CustomerEndpoint": {
                "Address": "+1234567890",
                "Type": "TELEPHONE_NUMBER"
            },
            "InitialContactId": "4a573372-1f28-4e26-b97b-XXXXXXXXXXX",
            "InitiationMethod": "INBOUND | OUTBOUND | TRANSFER | CALLBACK",
            "InstanceARN": "arn:aws:connect:aws-region:1234567890:instance/c8c0e68d-2200-4265-82c0-XXXXXXXXXX",
            "PreviousContactId": "4a573372-1f28-4e26-b97b-XXXXXXXXXXX",
            "Queue": "QueueName",
            "SystemEndpoint": {
                "Address": "+1234567890",
                "Type": "TELEPHONE_NUMBER"
            }
        },
        "Parameters": {
            "sentAttributeKey": "sentAttributeValue"
        }
    },
    "Name": "ContactFlowEvent"
}
```

This can also be referenced [here](https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html#function-contact-flow).

## Environment Variables

This Lambda function requires two environment variables:

- `BUCKET_NAME`: The S3 bucket name where the routing profile is stored.
- `COUNTRY_ROUTING_LIST_KEY`: The path of the routing profile object.

## Routing file

A list of ISO 3166 country code against the phone number in E164 format.

### Example

```
{
    "US": "+12345678901",
    "GB": "+441234567890",
    "Default": "+19876543210"
}
```

In this example, when calling a customer who has a United States phone number, Amazon Connect uses the phone number +12345678901 for the outbound caller ID. When calling a customer who has a United Kingdom phone number, the phone number +441234567890 is used. When calling a customer in a country that is not listed in the JSON file, the default phone number +19876543210 is used.

Note: During call routing, if the Lambda function fails to invoke for any reason, Amazon Connect uses the queue’s default outbound phone number for the caller instead. This is the number configured in the queue settings in your Amazon Connect instance.

## Example Lambda Response

```
{
    "customer_number": "<Customer's phone number that you're calling>",
    "customer_country": "<Country of the customer's phone number>",
    "outbound_number": "<Outbound phone number that Lambda loads from Amazon S3 and sends to Amazon Connect>",
    "outbound_country": "<Country of the outbound phone number that Lambda sends to Amazon Connect>",
    "default_queue_outbound_number": "<Default outbound phone number set up for the queue>",
    "default_queue_outbound_country": "<Country of the default outbound phone number>"
}
```

## Outbound Whisper Flow

After invoking the Lambda function in an outbound whisper flow, a “[Call Phone Number](https://docs.aws.amazon.com/connect/latest/adminguide/call-phone-number.html)” block needs to be placed. Tick the box of “Caller ID number to display (optional)”, and pick “Use attribute” from the radio buttons. For “Type”, select “External”. For “Attribute”, type in “`outbound_number`“, which is one of the key Lambda responses.

## IAM Permissions

This Lambda function require at least a read access to the routing file stored in S3. The value in square brackets needs to be replaced with genuine value.

### Example

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowGetRoutingProfile",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::<BUCKET_NAME>/<COUNTRY_ROUTING_LIST_KEY>"
            ]
        }
    ]
}
```

## Logging

If the Lambda function has the following permission (provided that the value in square brackets are placed with genuine value), it will send diagnostic logs to CloudWatch log:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:<region>:<account-id>:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:<region>:<account-id>:log-group:/aws/lambda/<lambda-function-name>:*"
            ]
        }
    ]
}
```