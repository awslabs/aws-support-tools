# Decode and verify Amazon Cognito JWT tokens

## Short Description

In many cases, when using a Cognito User Pool for authentication, it would be nice to have the details of the logged in user available in our back-end application. Some examples are:

    - API Gateway using a User Pool for authorisation; but after that the backend integration is not aware of the details of the user who invoked the API.
    - A Cognito Identity Pool is used to retrieve STS temporary credentials and then Lambda is invoked; but Lambda has no knowledge of the identity of the user that originally authenticated against the User Pool.

In all those cases it would be necessary to pass the user details in the payload to the the backend, but how can we ensure that those details don't get spoofed?

## Resolution

Luckily the JSON Web Tokens (JWT) come to help us. Upon login, Cognito User Pool returns a base64-encoded JSON string called JWT that contains important information (called claims) about the user. It actually returns 3 tokens called ID, Access and Refresh token, each one with its own purpose; however the token containing all the user fields defined in the User Pool, is the ID one.

Every JWT token is composed of 3 sections: header, payload and signature. Let's have a look at the content of a sample ID Token:

```
{
  "kid": "abcdefghijklmnopqrstuvwxyz=",
  "alg": "RS256"
}
```
The header contains the algorithm used to sign the token (in our case is RS256 which means RSA signature with SHA-256) and a Key ID (kid) that we'll need later on.

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
The payload contains information about the user as well as token creation and expiration dates.

The third section is the signature of a hashed combination of the header and the payload. In particular Cognito generates two pairs of RSA keys for each User Pool, then uses one of the private keys to sign the token and makes the corresponding public key available at the address

```
https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json
```

Such JSON file looks like this

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
        "alg": "RS256",
        "e": "AQAB",
        "kid": "fgjhlkhjlkhj5jkl5h=",
        "kty": "RSA",
        "n": "sgjhlk6jp98ugp98up34hpoi65hgh",
        "use": "sig"
    }]
}
```

All we need to do is to search for the key with a kid matching the kid in our JWT token and then use some libraries to decode the token and verify its signature. The good news is that we can pass the whole token in the payload to the back-end application and rest assured that it cannot be tampered with.

This solution is applicable to virtually any applications that want to verify the identity of a Cognito user from the JWT token, but since a common requirement is to do it from AWS Lambda, I wrote some sample Lambda code in Python 2.7 and Node.js 4.3.