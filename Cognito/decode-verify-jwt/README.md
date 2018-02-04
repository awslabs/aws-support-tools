# Decode and verify Amazon Cognito JWT tokens

## Issue
I want to use an Amazon Cognito user pool as the authentication method for my application. What is a secure way for me to verify the ID and access tokens sent by clients to my application?

## Short Description

When clients authenticate to your application with a user pool, Amazon Cognito sends an ID token. You might have cases where you need to manually verify the ID token in order to trust the information contained in it. Some examples include:

- You created a web application and want to use an Amazon Cognito user pool for authentication.
- You use an Amazon Cognito user pool for authentication and an Amazon Cognito identity pool to retrieve STS temporary credentials. AWS Lambda is invoked with those credentials, but Lambda doesn’t have information about who originally authenticated with the user pool.

## Resolution

After a user logs in, an Amazon Cognito user pool returns a JWT, which is a base64-encoded JSON string that contains information about the user (called claims). Amazon Cognito returns three tokens: the ID token, access token, and refresh token—the ID token contains the user fields defined in the Amazon Cognito user pool.

JWT tokens include three sections: a header, payload, and signature.

The following is the header of a sample ID token. The header contains the key ID (“kid”), as well as the algorithm (“alg”) used to sign the token. In this example, the algorithm is “RS256”, which is an RSA signature with SHA-256.
```
{
  "kid": "abcdefghijklmnopqrstuvwxyz=",
  "alg": "RS256"
}
```
The following is an example of the payload, which has information about the user, as well as timestamps of the token creation and expiration.
```
{
  "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "aud": "xxxxxxxxxxxxxxxxxxx",
  "email_verified": true,
  "token_use": "id",
  "auth_time": 1500009400,
  "iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_XXXxxXXxX",
  "cognito:username": "emanuele",
  "exp": 1500013000,
  "given_name": "Emanuele",
  "iat": 1500009400,
  "email": "something@example.com"
}
```
The following is an example of the signature, which is a hashed combination of the header and the payload. Amazon Cognito generates two pairs of RSA keys for each user pool. One of the private keys is used to sign the token, and the corresponding public key becomes available at an address in this format:
```
https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json
```
The JSON file is structured in this format:
```
{
    "keys": [{
        "alg": "RS256",
        "e": "AQAB",
        "kid": "abcdefghijklmnopqrstuvwxyz=",
        "kty": "RSA",
        "n": "lsjhglskjhgslkjgh43lj5h34lkjh34lkjht34ljth3l",
        "use": "sig"
    }, {
        "alg":
        "RS256",
        "e": "AQAB",
        "kid": "fgjhlkhjlkhj5jkl5h=",
        "kty": "RSA",
        "n": "sgjhlk6jp98ugp98up34hpoi65hgh",
        "use": "sig"
    }]
}
```
To verify the signature of an Amazon Cognito JWT, search for the key with a key ID that matches the key ID of the JWT, then use libraries to decode the token and verify the signature. Be sure to also verify that:

- The token is not expired.
- The audience ("aud") specified in the payload matches the app client ID created in the Amazon Cognito user pool.


## Requirements

### Python 2.7
For the Python version I've used <a href="https://github.com/mpdavis/python-jose">python-jose</a>, to handle the JWT token decoding and signature verification; that library is already part of the Lambda environment, so no additional steps are required.
However, if ran locally, it will be necessary to install it. As an example, can be installed via "pip" with
```
pip install python-jose
```

### NodeJS 4.3
For the NodeJS version I've used <a href="https://www.npmjs.com/package/node-jose">node-jose</a> which needs to be included in the Lambda deployment package. It can be done via NPM with
```
npm install node-jose
```
from within the script directory. Please refer to the AWS <a href="http://docs.aws.amazon.com/lambda/latest/dg/nodejs-create-deployment-pkg.html">documentation</a> for more details.