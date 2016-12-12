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

# Parameters
app_name=$1
app_download_url=$2

# Ensure user is root
function check_root_user {
	if [ "$(id -u)" != "0" ]; then
	   echo "This script must be run as root. Use 'sudo ./<script>'." 1>&2
	   exit 1
	fi
}

# Install packages
function install_packages {
	apt-get update
	apt-get install -y unzip
	apt-get install -y python
	apt-get install -y python-dev
	apt-get install -y python-pip
	pip install flask
	apt-get install -y apache2
	update-rc.d apache2 defaults
	apt-get install -y libapache2-mod-wsgi
	a2enmod wsgi
}

# Setup app user and apache configuration
function setup_appuser {
	useradd -m appuser
	mkdir /home/appuser/$app_name
}

# Configure apache
function configure_apache {
	# Create apache config
	cat << EOF > /etc/apache2/sites-available/000-$app_name.conf
<VirtualHost *:80>
        ServerAdmin webmaster@localhost
        ErrorLog /var/log/apache2/error.log
        CustomLog /var/log/apache2/access.log combined

        # python wsgi configuration
        WSGIDaemonProcess $app_name user=appuser group=appuser threads=50
        WSGIScriptAlias / /home/appuser/$app_name/$app_name.wsgi
        <Directory /home/appuser/$app_name>
                WSGIProcessGroup $app_name
                WSGIApplicationGroup %{GLOBAL}
                Order deny,allow
                Allow from all
                Options Indexes FollowSymLinks
                AllowOverride None
                Require all granted
        </Directory>
</VirtualHost>	
EOF
		
	# Disable apache default site and enable new site and apply changes
	a2dissite 000-default
	a2ensite 000-$app_name
	service apache2 restart
}

# Deploy application
function deploy_app {
	# Download application and deploy
	if [ -z $app_download_url ] ; then
		echo "Skipping application download. Use did not specify app download url."
	else
		wget $app_download_url -O /tmp/$app_name.zip
		mkdir /tmp/$app_name
		unzip -o /tmp/$app_name.zip -d /tmp/$app_name/
		cd /tmp/$app_name/*
		mv -f * /home/appuser/$app_name/
	fi
	
	# Create wsgi file
	cat << EOF > /home/appuser/$app_name/$app_name.wsgi
import sys
sys.path.append('/home/appuser/$app_name')
from app import app as application
EOF

	# Make appuser file owner
	chown -R appuser. /home/appuser/$app_name
	
}

# === Execution starts here ===

# First check if user is root
check_root_user

# Check if app name specified in parameter
if [ -z $app_name ] ; then
	echo "App name not specified."
	echo "Usage:"
	echo "./<script.sh> myapp"
	echo "./<script.sh> nyapp http://my_app_download_url/myapp.zip"
	exit 1;
fi

# Install required packages
install_packages

# Setup app user
setup_appuser

# Deploy application
deploy_app

# Configure apache
configure_apache

