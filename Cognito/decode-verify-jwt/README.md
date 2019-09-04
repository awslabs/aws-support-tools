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
  "kid": "abcdefghijklmnopqrsexample=",
  "alg": "RS256"
}
```
The following is an example of the payload, which has information about the user, as well as timestamps of the token creation and expiration.
```
{
  "sub": "aaaaaaaa-bbbb-cccc-dddd-example",
  "aud": "xxxxxxxxxxxxexample",
  "email_verified": true,
  "token_use": "id",
  "auth_time": 1500009400,
  "iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_example",
  "cognito:username": "anaya",
  "exp": 1500013000,
  "given_name": "Anaya",
  "iat": 1500009400,
  "email": "anaya@example.com"
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
        "kid": "abcdefghijklmnopqrsexample=",
        "kty": "RSA",
        "n": "lsjhglskjhgslkjgh43lj5h34lkjh34lkjht3example",
        "use": "sig"
    }, {
        "alg":
        "RS256",
        "e": "AQAB",
        "kid": "fgjhlkhjlkhexample=",
        "kty": "RSA",
        "n": "sgjhlk6jp98ugp98up34hpexample",
        "use": "sig"
    }]
}
```
To verify the signature of an Amazon Cognito JWT, search for the key with a key ID that matches the key ID of the JWT, then use libraries to decode the token and verify the signature. Be sure to also verify that:

- The token is not expired.
- The audience ("aud") specified in the payload matches the app client ID created in the Amazon Cognito user pool.


## Requirements

Please refer to the [Verifying a JSON Web Token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html) section of the Amazon Cognito Developer Guide for other programming languages and runtimes.

Per the [Security in AWS Lambda shared responsibility](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html), you are responsible for updating libraries as needed, as well as other factors including the sensitivity of your data, your company’s requirements, and applicable laws and regulations.

### Python 3
The Python code uses [python-jose](https://github.com/mpdavis/python-jose) to handle the JWT token decoding and signature verification; that library must be included in the Lambda deployment package using one of the methods discussed in the [Deployment Package in Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html) section of the AWS Lambda Developer Guide. 

