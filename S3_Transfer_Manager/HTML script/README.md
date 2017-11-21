# upload-test

*HTML script to test and compare the upload speeds to S3 Bucket via direct upload and via Transfer Acceleration .*

----

This HTML script is used to browse and select a file from your Web Browser and then upload it to the Bucket via a direct upload method as well as via Transfer Acceleration method.Once the upload is complete the Script displays the Upload speed in Mbps.The output can be used to test and compare the upload speed via both these methods.

## Requirements

* The script `upload-test.html` requires the following modifications.
  * Replace <Access Key ID> with your Access Key ID, and <Secret Access Key> with your Secret Access Key in line
    22 and 23 respectively of the script.
  * The security credentials provided above should have permission to upload objects to S3 Bucket.
  * Replace <region-name> with the region name of the S3 Bucket in line 29 and 38.
    * *region: 'us-west-2' //for PDX region*
  * Replace <Bucket-Name> with the name of the Bucket in lines 56 and 76.
    * *var params = {Bucket: 'myexamplebucket', Key: file.name, ContentType: file.type, Body: file}*
  * Before running the Script, S3 tranfer acceleration should be enabled on the bucket.
  * Before running the Script, we need to make sure to allow PUT method in the CORS configuration of the bucket.
    * *<AllowedMethod>PUT</AllowedMethod>*




