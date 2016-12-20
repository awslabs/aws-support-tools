Check SES Quota
===============
Checks AWS SES daily sending quota usage and notifies using AWS SNS if threshold of 80% has been reached.

Make sure to configure Lambda environment variables e.g `REGION=us-east-1`, `ALERT_THRESHOLD=80`, `TOPIC=arn:aws:sns:us-east-1:1111122222:MyTopic`