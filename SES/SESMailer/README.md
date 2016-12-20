SES Mailer
==========
Demonstrates how to send email faster using AWS SES without a backend.

How it works
------------
SES Mailer uses lambda to send mass email. It is invoked by S3 PUT event when a mailing list is dropped into the designated bucket. The function takes its message content from a HTML and plain text message file dropped in the same bucket. It sends multipart/alternative formatted emails.

Usage
-----
1. Deploy `ses_mailer.py` on AWS Lambda with a timeout setting of 5 minutes. Make sure the lambda Role has
   S3 read/write permissions to the bucket and `ses:SendRawEmail` permission. Configure Lambda environment variables e.g `REGION=us-east-1`, `MAX_THREADS=10`, `TEXT_MESSAGE_FILE=email_body.txt`, `HTML_MESSAGE_FILE=email_body.html`
2. Create a S3 bucket and set `put` event to trigger this lambda function.
3. In the S3 events configuration, set the event suffix to `.gz`.
4. Write your html formatted email in file **html_message.html** and upload to S3 bucket.
5. Write the plain text version of your email message in file **text_message.txt** and upload to S3 bucket.
6. Create a mailing list file i.e **mailing_list_14032016.csv** with contents in the below csv format. **Don't** include first row as header fields.

    ```
    Sender Name <me@example.com>, Recipient Name <you@example.com>, subject
    ```
    
7. Compress the file using gzip. e.g `gzip -kf mailing_list_14032016.csv` creates `mailing_list_14032016.csv.gz`
8. Upload the gzipped file **mailing_list_14032016.csv.gz** to the S3 bucket and it will trigger this lambda function.
9. This function will start sending email to all addresses in the csv file and log failures in `<FILENAME>_error.log`.

**Tip:** You can send even faster by splitting email list into multiple smaller csv files when the number of addresses exceed over a few 100,000s or increase `MAX_THREADS` environment variable value to something higher depending on your SES TPS limit.
    