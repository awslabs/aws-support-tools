<h1>Cognito Identity Pool and OneLogin SAML Authentication Integration tester script</h1>

<b>Requirements</b>

- boto3 installed and aws cli configured

<b>Usage:</b>

onelogin_cognito.py [-h] [-d DEBUGFLAG] -e EMAILORUSERNAME -p PASSWORD<br>
                           -a APPID -s SUBDOMAIN -i IDENTITYPROVIDERNAME -c<br>
                           ACCOUNTID -t IDENTITYPOOLID

Cognito Identity Pool and OneLogin SAML Authentication Integrator<br><br>

<b>Optional Arguments:<br><br></b>
  -h, --help            show this help message and exit<br><br>
  -d DEBUGFLAG, --debugflag DEBUGFLAG<br><br>
                        Enter Y to enable debugging. This will print the credentials into STDOUT<br><br>
  -e EMAILORUSERNAME, --emailorusername EMAILORUSERNAME<br><br>
                        Enter email to login/username to your User Pool<br><br>
  -p PASSWORD, --password PASSWORD<br><br>
                        Enter password to login to your User Pool<br><br>
  -a APPID, --appid APPID<br><br>
                        Enter your Cognito App Id<br><br>
  -s SUBDOMAIN, --subdomain SUBDOMAIN<br><br>
                        The name of the subdomain that got created when you created the OneLogin account<br><br>
  -i IDENTITYPROVIDERNAME, --identityprovidername IDENTITYPROVIDERNAME<br><br>
                        This tag to be filled below is the IAM SAML Identity Provider name of the Identity Provider we have created for OneLogin<br><br>
  -c ACCOUNTID, --accountid ACCOUNTID<br><br>
                        Account ID of your AWS Account<br><br>
  -t IDENTITYPOOLID, --identitypoolid IDENTITYPOOLID<br><br>
                        ID of your Cognito Identity Pool<br><br>
