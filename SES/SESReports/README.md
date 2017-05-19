# Amazon - AWS Simple Email Service | SES | Reports
This is a lambda-function that generate reports of Bounce and Complaint and save on S3 Bucket in a web-format, like a dashboard that allows searchs (message-id, recipient email, etc)
However, the logic to control the Bounce and Complaints notifications is ready to be customized.
The reports looks like:[NotificationType;destination;subtype(ifExist);DiagnosticCode(IfExist);TimeStamp]
 ```
Type	Subtype	Detail	Email	Error	Date	MessageID
Bounce	Permanent	General	bounce@simulator.amazonses.com	smtp; 550 5.1.1 user unknown	2017-03-08T13:30:11.000Z	0102015aae1cde78-2b30806b-7932-425f-bfa3-ac0eca7eebda-000000
Bounce	Permanent	General	bounce@simulator.amazonses.com	smtp; 550 5.1.1 user unknown	2017-03-08T13:30:52.000Z	0102015aae1d7d9f-3b290f2a-1741-4ff2-bac7-6781a1117894-000000
Bounce	Permanent	Suppressed	otoo@simulator.amazonses.com	Suppressed by SES	2017-03-08T13:25:46.782Z	0102015aae18d17a-0976a238-c24d-4411-9fd0-7874229c1f9b-000000
```

I'd like to encourage you to use the Mailbox Simulator provided by SES when deploying this script. It will avoid unnecessary bounces in your account.

## Environment details:
* SES Account up and running 
* SNS Notification for Bounces and Complaints || Notifications
* SQS || Manage the Notification's queue
* CloudWatch Events || Will trigger the Lambda function
* Lambda NodeJS || Will generate the report and send the URL via Email(SES)

## How does it work?
*	Amazon SES
*	Amazon SNS – Bounces and Complaints notifications
*	Amazon SQS – Queue for the Notifications
*	Lambda – Will Process the queue, create the Report, save to S3 and send the report URL via Email using SES
*	CloudWatch – Will trigger the lambda-function using “Scheduled Events"


## Installation:
*	Create an Amazon SNS topic [1].
*	Create an Amazon SQS Standard Queue [2]. Only changing: Default Visibility Timeout to 5m. 
*	Subscribe the queue to SNS Topic previously created [3].
*	Create an Amazon S3 Bucket.
*	Create an IAM policy(Create your Own Policy) with the following permission (changing the YourRecipient@yourDomain.com example for your recipient address, Queue ARN for yours and the BucketName) [4].

 ```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSendEmail",
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail"
            ],
            "Condition": {
                "ForAllValues:StringLike": {
                    "ses:Recipients": [
                        "YourRecipient@yourDomain.com"
                    ]
                }
            },
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "s3allow",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::YourBucketName/*"
            ]
        },
        {
            "Sid": "AllowQueuePermissions",
            "Effect": "Allow",
            "Action": [
                "sqs:ChangeMessageVisibility",
                "sqs:ChangeMessageVisibilityBatch",
                "sqs:DeleteMessage",
                "sqs:DeleteMessageBatch",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage"
            ],
            "Resource": [
                "arn:aws:sqs:REGION:ACCOUNT-ID:QueueName"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": [
                "arn:aws:logs:*:*:*"
            ]
        }
    ]
} 
 ```
## If you want to restric a specific log-group permission on the IAM role, you can use the following ARN instead of "arn:aws:logs:*:*:*" :
```
arn:aws:logs:[REGION]:[ACCOUNT-ID]:log-group:[NAME LOG GROUP]:* 
arn:aws:logs:eu-west-1:123456789123:log-group:/aws/lambda/yourLambda:* 

```
*	Create an IAM Role and attach the policy just created (You will use this Role for lambda execution) [5].
*	Create an Amazon lambda-function following the steps below.

## Creating Lambda Function
Firstly compress(zip) the folder lamba-dep-package’s content (the content, not the folder) which you can find on the “The code” session of this manual.
*  Sign in to the AWS Management Console and open the AWS Lambda console.
* Choose Get Started Now.
* Create a Lambda function go to the Lambda > New function page. 
* Select the Runtime Node.js 4.3
* Choose Black Function
* On Triggers, click on Next (We will do this step later)
* Give a Name and description for your Lambda-Function
* On “Code entry Type” chose “Upload a .ZIP file”, select the zip file created from “lamba-dep-package” CONTENT, not the folder.
* On Environment variables, you need to add the following variables:
```
Region: eu-west-1 // Your Queue Region [REQUIRED]
QueueURL: https://sqs.eu-west-1.am… // The Queue URL [REQUIRED]
ToAddr: yourVerifiedEmail // Email address which will receive the report [Optional – If you don’t create it, no report will be sent via Email]
SrcAddr: youVerifiedEmail // Email address which will send the report [REQUIRED IF using ToAddr]
BucketName: yourBucketName  // Bucket to save the report [REQUIRED]
BucketPrefix: YourPrefix/ // Bucket prefix to save the report [Optional – If present, need to finish with slash “/”]
```

* On role: Select the “Chosen an existing role”> Select the role previously created
* Set the memory  (Advanced tab) to 512MB if less 5000 bounces/complaints per day, 1024MB if more than 5000 or 1536MB if more than 10000.
* Set the Timeout for 5 minutes  
* Click on Next > Review your information and “Create function”

## Enabling the Bounces and Complaints Notifications for your identities 
*	Go to SES Console
*	Edit the notification for the identity
*	Select the SNS topic created for Bounces and Complaints
*	Then go to SQS Console > Select the Queue > Purge Queue (This is a required step because SES sends a confirmation notification and it’s not needed).

## Triggering the Function with CloudWatch Schedule Events
*	Go to CloudWatch console
*	Click on Events > Rules > Create Rule
*	Select Schedule > Fixed rate > 1 Day
*	On Target, select the lambda-function > Configure Details
*	Give a name > Create Rule

DOC Refference: 
[1] Creating SNS Topic: http://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html
[2] Creating SQS Standard Queue: http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-create-queue.html
[3] Subscribing a Queue to SNS Topic: http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-subscribe-queue-sns-topic.html
[4] Creating IAM Policy: http://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html#access_policies_create-editor
[5] Creating IAM Role (AWS Lambda Role): http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-service.html 
[6] CloudWatch Event Schedule: http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLambdaSchedule.html#schedule-create-rule
