Quick Instance EC2
==================
Quick Instance **qi.py** lets you launch, deploy applications and terminate AWS ec2 instances using CloudFormation. 
This is useful when a disposable ec2 instance is needed to quickly test or deploy an application on a supported OS.

Examples:
--------
Launch a vanilla Amazon Linux ec2 instance without bootstrapping it:

```bash
./qi.py amazon-linux
```

Launch Ubuntu ec2 instance with Apache Tomcat7 configured:

```bash
./qi.py ubuntu --bootstrap "wget https://github.com/awslabs/aws-support-tools/EC2/QuickInstanceEC2/DeployScripts/tomcat7_ubuntu14.04_install.sh?raw=1 -O /tmp/install.sh && chmod +x /tmp/install.sh && /tmp/install.sh"
```

Launch Ubuntu ec2 instance with Apache (wsgi) and deploy a sample Python Flask application:

```bash
./qi.py ubuntu --bootstrap "wget https://github.com/awslabs/aws-support-tools/EC2/QuickInstanceEC2/DeployScripts/flask_deploy.sh?raw=1 -O /tmp/install.sh && chmod +x /tmp/install.sh && /tmp/install.sh example_app https://github.com/saidalisamed/tools/raw/master/PythonFlask/example-python-flask/archive/master.zip"
```

Launch Amazon Linux with LAMP stack configured:

```bash
./qi.py amazon-linux --bootstrap "yum update -y && yum groupinstall -y 'Web Server' 'MySQL Database' 'PHP Support' && yum install -y php-mysql && service httpd start && chkconfig httpd on && groupadd www && usermod -a -G www ec2-user && chown -R root:www /var/www && chmod 2775 /var/www && find /var/www -type d -exec chmod 2775 {} + && find /var/www -type f -exec chmod 0664 {} + && echo '<?php phpinfo(); ?>' > /var/www/html/phpinfo.php"
```

Launch Amazon Linux and install/configure a CRM software (SuiteCRM):

```bash
./qi.py amazon-linux --bootstrap "yum update -y && yum groupinstall -y 'Web Server' 'MySQL Database' 'PHP Support' && yum install -y php-mysql && yum install -y php-mbstring && service httpd start && chkconfig httpd on && chkconfig mysqld on && groupadd www && usermod -a -G www ec2-user && chown -R root:www /var/www && chmod 2775 /var/www && find /var/www -type d -exec chmod 2775 {} + && find /var/www -type f -exec chmod 0664 {} + && wget -O /tmp/crm.zip  http://downloads.sourceforge.net/project/suitecrm/suitecrm-7.2.1.zip && mkdir /tmp/crm && unzip /tmp/crm.zip -d /tmp/crm/ && shopt -s dotglob nullglob && mv /tmp/crm/*/* /var/www/html/ && chown -R apache:www /var/www/html/ && /etc/init.d/mysqld restart"
```

Launch Ubuntu instance and install/configure SuiteCRM with HHVM and nginx:

```bash
./qi.py ubuntu --bootstrap "wget https://github.com/awslabs/aws-support-tools/EC2/QuickInstanceEC2/DeployScripts/nginx_hhvm_suitecrm_ubuntu14.04_install.sh?raw=1 -O /tmp/install.sh && chmod +x /tmp/install.sh && /tmp/install.sh"
```

Launch six difference ec2 instances simultaneously:

```bash
for os in amazon-linux nat-instance ubuntu redhat-linux windows-2008 windows-2012; do ./qi.py $os & done
```

Launch Ubuntu ec2 instance with a 100GB root volume size by overriding the default configuration:

```bash
./qi.py ubuntu --volume 100
```

To terminate, run the same command again:

```bash
./qi.py ubuntu
./qi.py amazon-linux
```

Installation:
------------
Installation on Linux and Mac OSX:

```bash
curl -o qi.py https://github.com/awslabs/aws-support-tools/EC2/QuickInstanceEC2/qi.py?raw=1
chmod +x qi.py
```

For installation on Windows, save [this](https://github.com/awslabs/aws-support-tools/EC2/QuickInstanceEC2/qi.py?raw=1).

To install boto3 on Windows and launching an ec2 instance:

```bash
C:\Python27\python.exe -m pip install boto3
C:\Python27\python.exe qi.py amazon-linux
```

Configuration:
-------------
Run `configure` when running for the first time to configure quick instance.

```bash
./qi.py configure
```

Requirements:
------------
- Python 2.7 or above.
- Boto3 python module.
- Python pip required to install boto3 module.
- AWS credentials in ~/.aws/credentials or ec2 instance role with appropriate IAM permissions. Follow this [guide](http://blogs.aws.amazon.com/security/post/Tx3D6U6WSFGOK2H/A-New-and-Standardized-Way-to-Manage-Credentials-in-the-AWS-SDKs) to set up AWS credentials.
