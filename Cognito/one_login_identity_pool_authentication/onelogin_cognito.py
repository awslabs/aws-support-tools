import requests
import boto3
import json

#First Call to get the access token Reference - https://developers.onelogin.com/api-docs/1/oauth20-tokens/generate-tokens-2

get_oauth_tokens = requests.post('https://api.us.onelogin.com/auth/oauth2/v2/token',
  auth=('<appclient_id_onelogin>','<appclient_secret_onelogin>'),
  json={
    "grant_type": "client_credentials"
  }
)

get_oauth_tokens = get_oauth_tokens.json()

print("The OneLogin Access Token is ",get_oauth_tokens['access_token'])

print ("-----------------------------------------------")

access_token = get_oauth_tokens['access_token']

#Second Call to get the SAML response token - https://developers.onelogin.com/api-docs/1/saml-assertions/generate-saml-assertion

payload = {
  "username_or_email": "<email>",
  "password": "<password>",
  "app_id": "<app_id>",
  "subdomain":"<your_subdomain>" #The name of the subdomain that got created when you created the OneLogin account.
}

headers = {'Authorization': 'bearer:'+access_token,'Content-Type' : 'application/json'}

get_saml_assertion = requests.post(url = 'https://api.us.onelogin.com/api/1/saml_assertion',headers = headers,data=json.dumps(payload))

#print(list(get_saml_assertion))

saml_assertion = get_saml_assertion.json()["data"]

print("The SAML Assertion from OneLogin is ", saml_assertion)

print ("-----------------------------------------------")

account_id,identity_pool_id = '<aws_account_id>','<identity_pool_id>'

identity = boto3.client('cognito-identity')

#Third Call to get the identity-id using the cognito get-id call

get_identity_id = identity.get_id(AccountId=account_id, IdentityPoolId=identity_pool_id,Logins={'<iam_saml_identity_provider_configured_with_onelogin>':saml_assertion})

identity_id = get_identity_id['IdentityId']

#Fourth Call to get the AWS temporary credentials

get_temporary_aws_credentials = identity.get_credentials_for_identity(IdentityId=identity_id,Logins={'<iam_saml_identity_provider_configured_with_onelogin>':saml_assertion})

print("The temporary AWS credentials are ", get_temporary_aws_credentials)

print ("-----------------------------------------------")