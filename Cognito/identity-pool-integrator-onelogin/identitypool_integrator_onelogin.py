"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import requests
import boto3
import json
import argparse
import sys
import traceback

def main():
    # Get and parse the values passed in arguments to use in the integration tester.
    parser = argparse.ArgumentParser(description='Cognito Identity Pool and OneLogin SAML Authentication Integrator')

    parser.add_argument('-d','--debugflag', help='Enter Y to enable debugging. This will print the credentials into STDOUT', type=str)
    parser.add_argument('-e','--emailorusername', required=True, help='Enter email to login/username to your User Pool', type=str)
    parser.add_argument('-p','--password',required=True, help='Enter password to login to your User Pool', type=str)
    parser.add_argument('-a','--appid', required=True ,help='Enter your Cognito App Id', type=str)
    parser.add_argument('-s','--subdomain', required=True, help='The name of the subdomain that got created when you created the OneLogin account', type=str)
    parser.add_argument('-i','--identityprovidername', required=True, help='This tag to be filled below is the IAM SAML Identity Provider name of the Identity Provider we have created for OneLogin', type=str)
    parser.add_argument('-c','--accountid', required=True, help='Account ID of your AWS Account', type=str)
    parser.add_argument('-t','--identitypoolid', required=True, help='ID of your Cognito Identity Pool', type=str)

    args = vars(parser.parse_args())

    debugflag = args.get("debugflag")

    if debugflag is None:
        debugflag == "N"

    emailorusername = args["emailorusername"]
    password = args["password"]
    appid = args["appid"]
    subdomain = args["subdomain"]
    identityprovidername = args["identityprovidername"]
    accountid = args["accountid"]
    identitypoolid = args["identitypoolid"]

    try:
        # Get the OneLogin App Client ID and App Client Secret. This is stored in AWS systems manager(ssm).
        ssm_client = boto3.client("ssm")

        app_credentials = ssm_client.get_parameter(Name="OneLoginAppCredentials")
        appclientidonelogin, appclientsecretonelogin = app_credentials["Parameter"]["Value"].split(",")

        #First Call to get the access token Reference - https://developers.onelogin.com/api-docs/1/oauth20-tokens/generate-tokens-2
        get_oauth_tokens = requests.post('https://api.us.onelogin.com/auth/oauth2/v2/token',
          auth=(appclientidonelogin,appclientsecretonelogin),
          json={
            "grant_type": "client_credentials"
          }
        )

        get_oauth_tokens = get_oauth_tokens.json()

        if debugflag == "Y":
            print("The OneLogin Access Token is ",get_oauth_tokens['access_token'])
        else:
            print("The OneLogin Access Token has been obtained successfully")

        print("-----------------------------------------------")

        access_token = get_oauth_tokens['access_token']

        #Second Call to get the SAML response token - https://developers.onelogin.com/api-docs/1/saml-assertions/generate-saml-assertion

        payload = {
          "username_or_email": emailorusername,
          "password": password,
          "app_id": appid,
          "subdomain":subdomain #The name of the subdomain that got created when you created the OneLogin account.
        }

        headers = {'Authorization': 'bearer:'+access_token,'Content-Type' : 'application/json'}

        get_saml_assertion = requests.post(url = 'https://api.us.onelogin.com/api/1/saml_assertion',headers = headers,data=json.dumps(payload))

        saml_assertion = get_saml_assertion.json()["data"]

        if debugflag == "Y":
            print("The SAML Assertion from OneLogin is ", saml_assertion)
        else:
            print("The SAML assertion has been obtained successfully")

        print("-----------------------------------------------")

        account_id,identity_pool_id = accountid,identitypoolid

        identity = boto3.client('cognito-identity')

        #Third Call to get the identity-id using the cognito get-id call

        get_identity_id = identity.get_id(AccountId=account_id, IdentityPoolId=identity_pool_id,Logins={identityprovidername:saml_assertion})

        identity_id = get_identity_id['IdentityId']

        #Fourth Call to get the AWS temporary credentials

        get_temporary_aws_credentials = identity.get_credentials_for_identity(IdentityId=identity_id,Logins={identityprovidername:saml_assertion})

        if debugflag == "Y":
            print("The temporary AWS credentials are ", get_temporary_aws_credentials)
        else:
            print("The temporary AWS credentials have been obtained successfully")

        print("-----------------------------------------------")

    except Exception as e:
        print("Error occured")
        traceback.print_exc(file=sys.stdout)

# Main of the program
if __name__ == '__main__':
	main()

