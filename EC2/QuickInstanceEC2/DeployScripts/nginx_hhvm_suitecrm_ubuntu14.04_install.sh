#!/bin/bash

# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

# Ensure user is root
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root. Use 'sudo ./<script>'." 1>&2
   exit 1
fi

# Install nginx with hhvm
apt-get install -y software-properties-common
apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0x5a16e7281be7a449
add-apt-repository -y 'deb http://dl.hhvm.com/ubuntu trusty main'
apt-get update
apt-get install -y nginx
apt-get install -y hhvm
/usr/share/hhvm/install_fastcgi.sh
/etc/init.d/hhvm restart
sed -i s/index.html/index.php/g /etc/nginx/sites-enabled/default
mkdir /var/lib/php5
chown -R www-data:www-data /var/lib/php5
/etc/init.d/nginx restart
update-rc.d hhvm defaults

# Install CRM
apt-get install -y unzip
wget -O /tmp/crm.zip  http://downloads.sourceforge.net/project/suitecrm/suitecrm-7.2.1.zip
mkdir /tmp/crm
unzip /tmp/crm.zip -d /tmp/crm/
shopt -s dotglob nullglob
mv /tmp/crm/*/* /usr/share/nginx/html/
chown -R www-data:www-data /usr/share/nginx/html/

# Install MySQL server
pass=$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-32};echo;)
debconf-set-selections <<< "mysql-server mysql-server/root_password password $pass"
debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $pass"
echo $pass > /root/mysql_pass.txt && chmod 400 /root/mysql_pass.txt
apt-get -y install mysql-server
update-rc.d mysql defaults
/etc/init.d/mysql restart

echo "Installation is complete."
