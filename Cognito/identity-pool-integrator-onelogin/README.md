Cognito Identity Pool and OneLogin SAML Authentication Integration tester script

Requirements - boto3 installed and aws cli configured

usage: onelogin_cognito.py [-h] [-d DEBUGFLAG] -e EMAILORUSERNAME -p PASSWORD
                           -a APPID -s SUBDOMAIN -i IDENTITYPROVIDERNAME -c
                           ACCOUNTID -t IDENTITYPOOLID

Cognito Identity Pool and OneLogin SAML Authentication Integrator

optional arguments:
  -h, --help            show this help message and exit
  -d DEBUGFLAG, --debugflag DEBUGFLAG
                        Enter Y to enable debugging. This will print the
                        credentials into STDOUT
  -e EMAILORUSERNAME, --emailorusername EMAILORUSERNAME
                        Enter email to login/username to your User Pool
  -p PASSWORD, --password PASSWORD
                        Enter password to login to your User Pool
  -a APPID, --appid APPID
                        Enter your Cognito App Id
  -s SUBDOMAIN, --subdomain SUBDOMAIN
                        The name of the subdomain that got created when you
                        created the OneLogin account
  -i IDENTITYPROVIDERNAME, --identityprovidername IDENTITYPROVIDERNAME
                        This tag to be filled below is the IAM SAML Identity
                        Provider name of the Identity Provider we have created
                        for OneLogin
  -c ACCOUNTID, --accountid ACCOUNTID
                        Account ID of your AWS Account
  -t IDENTITYPOOLID, --identitypoolid IDENTITYPOOLID
                        ID of your Cognito Identity Pool
