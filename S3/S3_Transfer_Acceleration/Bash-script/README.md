# test-upload.sh

*Bash script to test and compare the upload speeds to S3 Bucket via direct upload and via Transfer Acceleration from a Linux machine.*

# test-upload-macosx.sh

*Bash script to test and compare the upload speeds to S3 Bucket via direct upload and via Transfer Acceleration from a MAC OSX machine.*
----

It is a bash script that facilitates the upload of objects to S3 Buckets via a direct upload as well as via Transfer Acceleration.The script leverages the AWS CLI credentials and commands and can be used to comapre the upload speed to the S3 Bucket via a direct upload or via Transfer Acceleration.Once the file is gets uploaded, the script takes a user input, to check whether the user wants to delete the uploaded file or not.


## Requirements

###General Requirements:

* You need to install and confgiure AWS CLI on your machine.
* In order to install AWS CLI on your machine you may refer the link below:

http://docs.aws.amazon.com/cli/latest/userguide/installing.html

* You need to install bc (an arbitrary precision calculator language) on your Linux machine.
* You may use the following commands to install bc

Ubuntu / Debian based machine:

apt-get install bc

Amazon Linux/ CentOS/ RHEL/ Fedora based machine:

yum install bc

###Requirements for MAC OSX machines:

In order to improve the accuracy of the results, the script calculates the time taken for the upload in microseconds and then converts them in seconds before using them in the script.However the MAC-OSX systems do not natively support sub-second time interval, as the date program in OSX is different than GNU's coreutils date program.Thus,we need to install coreutils (including gnu-date), on MAC OSX using brew installer.

* Installing Homebrew install(if not installed earlier)
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

* Installing coreutils using brew(if not installed earlier)
brew install coreutils

Once the coreutils is installed they can run the script test-upload-macosx.sh












