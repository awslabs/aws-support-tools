# node-jose #

[![Greenkeeper badge](https://badges.greenkeeper.io/cisco/node-jose.svg)](https://greenkeeper.io/)
[![Build Status](https://travis-ci.org/cisco/node-jose.svg?branch=master)](https://travis-ci.org/cisco/node-jose)

A JavaScript implementation of the JSON Object Signing and Encryption (JOSE) for current web browsers and node.js-based servers.  This library implements (wherever possible) all algorithms, formats, and options in [JWS](https://tools.ietf.org/html/rfc7515 "Jones, M., J. Bradley and N. Sakimura, 'JSON Web Signature (JWS)' RFC 7515, May 2015"), [JWE](https://tools.ietf.org/html/rfc7516 "Jones, M. and J. Hildebrand 'JSON Web Encryption (JWE)', RFC 7516, May 2015"), [JWK](https://tools.ietf.org/html/rfc7517 "Jones, M., 'JSON Web Key (JWK)', RFC 7517, May 2015"), and [JWA](https://tools.ietf.org/html/rfc7518 "Jones, M., 'JSON Web Algorithms (JWA)', RFC 7518, May 2015") and uses native cryptographic support ([WebCrypto API](http://www.w3.org/TR/WebCryptoAPI/) or node.js' "[crypto](https://nodejs.org/api/crypto.html)" module) where feasible.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Installing](#installing)
- [Basics](#basics)
- [Keys and Key Stores](#keys-and-key-stores)
  - [Obtaining a KeyStore](#obtaining-a-keystore)
  - [Exporting a KeyStore](#exporting-a-keystore)
  - [Retrieving Keys](#retrieving-keys)
  - [Searching for Keys](#searching-for-keys)
  - [Managing Keys](#managing-keys)
  - [Importing and Exporting a Single Key](#importing-and-exporting-a-single-key)
  - [Obtaining a Key's Thumbprint](#obtaining-a-keys-thumbprint)
- [Signatures](#signatures)
  - [Keys Used for Signing and Verifying](#keys-used-for-signing-and-verifying)
  - [Signing Content](#signing-content)
  - [Verifying a JWS](#verifying-a-jws)
    - [Handling `crit` Header Members](#handling-crit-header-members)
- [Encryption](#encryption)
  - [Keys Used for Encrypting and Decrypting](#keys-used-for-encrypting-and-decrypting)
  - [Encrypting Content](#encrypting-content)
  - [Decrypting a JWE](#decrypting-a-jwe)
    - [Handling `crit` Header Members](#handling-crit-header-members-1)
- [Useful Utilities](#useful-utilities)
  - [Converting to Buffer](#converting-to-buffer)
  - [URI-Safe Base64](#uri-safe-base64)
  - [Random Bytes](#random-bytes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Installing ##

To install the latest from [NPM](https://npmjs.com/):

```
  npm install node-jose
```

Or to install a specific release:

```
  npm install node-jose@0.3.0
```

Alternatively, the latest unpublished code can be installed directly from the repository:

```
  npm install git+https://github.com/cisco/node-jose.git
```

## Basics ##

Require the library as normal:

```
var jose = require('node-jose');
```

This library uses [Promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) for nearly every operation.

This library supports [Browserify](http://browserify.org/) and [Webpack](https://webpack.github.io/).  To use in a web browser, `require('node-jose')` and bundle with the rest of your app.

The content to be signed/encrypted -- or returned from being verified/decrypted -- are [Buffer](https://nodejs.org/api/buffer.html) objects.

## Keys and Key Stores ##

The `jose.JWK` namespace deals with JWK and JWK-sets.

* `jose.JWK.Key` is a logical representation of a JWK, and is the "raw" entry point for various cryptographic operations (e.g., sign, verify, encrypt, decrypt).
* `jose.JWK.KeyStore` represents a collection of Keys.

Creating a JWE or JWS ultimately require one or more explicit Key objects.

Processing a JWE or JWS relies on a KeyStore.

### Obtaining a KeyStore ###
To create an empty keystore:

```
keystore = jose.JWK.createKeyStore();
```

To import a JWK-set as a keystore:

```
// {input} is a String or JSON object representing the JWK-set
jose.JWK.asKeyStore(input).
     then(function(result) {
       // {result} is a jose.JWK.KeyStore
       keystore = result;
     });
```

### Exporting a KeyStore ###

To export the public keys of a keystore as a JWK-set:

```
output = keystore.toJSON();
```

To export **all** the keys of a keystore:

```
output = keystore.toJSON(true);
```

### Retrieving Keys ###

To retrieve a key from a keystore:

```
// by 'kid'
key = keystore.get(kid);
```

This retrieves the first key that matches the given {kid}.  If multiple keys have the same {kid}, you can further narrow what to retrieve:

```
// ... and by 'kty'
key = keystore.get(kid, { kty: 'RSA' });

// ... and by 'use'
key = keystore.get(kid, { use: 'enc' });

// ... and by 'alg'
key = keystore.get(kid, { use: 'RSA-OAEP' });

// ... and by 'kty' and 'use'
key = keystore.get(kid, { kty: 'RSA', use: 'enc' });

// same as above, but with a single {props} argument
key = keystore.get({ kid: kid, kty: 'RSA', use: 'enc' });
```

### Searching for Keys ###

To retrieve all the keys from a keystore:

```
everything = keystore.all();
```

`all()` can be filtered much like `get()`:

```
// filter by 'kid'
everything = keystore.all({ kid: kid });

// filter by 'kty'
everything = keystore.all({ kty: 'RSA' });

// filter by 'use'
everything = keystore.all({ use: 'enc' });

// filter by 'alg'
everything = keystore.all({ alg: 'RSA-OAEP' });

// filter by 'kid' + 'kty' + 'alg'
everything = keystore.all({ kid: kid, kty: 'RSA', alg: 'RSA-OAEP' });
```

### Managing Keys ###

To import an existing Key (as a JSON object or Key instance):

```
// input is either a:
// *  jose.JWK.Key to copy from; or
// *  JSON object representing a JWK; or
keystore.add(input).
        then(function(result) {
          // {result} is a jose.JWK.Key
          key = result;
        });
```

To import and existing Key from a PEM or DER:

```
// input is either a:
// *  String serialization of a JSON JWK/(base64-encoded) PEM/(binary-encoded) DER
// *  Buffer of a JSON JWK/(base64-encoded) PEM/(binary-encoded) DER
// form is either a:
// * "json" for a JSON stringified JWK
// * "private" for a DER encoded 'raw' private key
// * "pkcs8" for a DER encoded (unencrypted!) PKCS8 private key
// * "public" for a DER encoded SPKI public key (alternate to 'spki')
// * "spki" for a DER encoded SPKI public key
// * "pkix" for a DER encoded PKIX X.509 certificate
// * "x509" for a DER encoded PKIX X.509 certificate
// * "pem" for a PEM encoded of PKCS8 / SPKI / PKIX
keystore.add(input, form).
        then(function(result) {
          // {result} is a jose.JWK.Key
        });
```

To generate a new Key:

```
// first argument is the key type (kty)
// second is the key size (in bits) or named curve ('crv') for "EC"
keystore.generate("oct", 256).
        then(function(result) {
          // {result} is a jose.JWK.Key
          key = result;
        });

// ... with properties
var props = {
  kid: 'gBdaS-G8RLax2qgObTD94w',
  alg: 'A256GCM',
  use: 'enc'
};
keystore.generate("oct", 256, props).
        then(function(result) {
          // {result} is a jose.JWK.Key
          key = result;
        });
```

To remove a Key from its Keystore:
```
keystore.remove(key);
// NOTE: key.keystore does not change!!
```

### Importing and Exporting a Single Key ###

To import a single Key:

```
// where input is either a:
// *  jose.JWK.Key instance
// *  JSON Object representation of a JWK
jose.JWK.asKey(input).
        then(function(result) {
          // {result} is a jose.JWK.Key
          // {result.keystore} is a unique jose.JWK.KeyStore
        });

// where input is either a:
// *  String serialization of a JSON JWK/(base64-encoded) PEM/(binary-encoded) DER
// *  Buffer of a JSON JWK/(base64-encoded) PEM/(binary-encoded) DER
// form is either a:
// * "json" for a JSON stringified JWK
// * "pkcs8" for a DER encoded (unencrypted!) PKCS8 private key
// * "spki" for a DER encoded SPKI public key
// * "pkix" for a DER encoded PKIX X.509 certificate
// * "x509" for a DER encoded PKIX X.509 certificate
// * "pem" for a PEM encoded of PKCS8 / SPKI / PKIX
jose.JWK.asKey(input, form).
        then(function(result) {
          // {result} is a jose.JWK.Key
          // {result.keystore} is a unique jose.JWK.KeyStore
        });
```

To export the public portion of a Key as a JWK:

```
var output = key.toJSON();
```

To export the public **and** private portions of a Key:

```
var output = key.toJSON(true);
```

### Obtaining a Key's Thumbprint ###

To get or calculate a [RFC 7638](https://tools.ietf.org/html/rfc7638) thumbprint for a key:

```
// where hash is a supported algorithm, currently one of:
// * SHA-1
// * SHA-256
// * SHA-384
// * SHA-512
key.thumbprint(hash).
    then(function(print) {
      // {print} is a Buffer containing the thumbprint binary value
    });
```

When importing or generating a key that does not have a "kid" defined, a
"SHA-256" thumbprint is calculated and used as the "kid".

## Signatures ##

### Keys Used for Signing and Verifying ###

When signing content, the key is expected to meet one of the following:

1. A secret key (e.g, `"kty":"oct"`)
2. The **private** key from a PKI (`"kty":"EC"` or `"kty":"RSA"`) key pair

When verifying content, the key is expected to meet one of the following:

1. A secret key (e.g, `"kty":"oct"`)
2. The **public** key from a PKI (`"kty":"EC"` or `"kty":"RSA"`) key pair


### Signing Content ###

At its simplest, to create a JWS:

```
// {input} is a Buffer
jose.JWS.createSign(key).
        update(input).
        final().
        then(function(result) {
          // {result} is a JSON object -- JWS using the JSON General Serialization
        });
```

The JWS is signed using the preferred algorithm appropriate for the given Key.  The preferred algorithm is the first item returned by `key.algorithms("sign")`.

To create a JWS using another serialization format:

```
jose.JWS.createSign({ format: 'flattened' }, key).
        update(input).
        final().
        then(function(result) {
          // {result} is a JSON object -- JWS using the JSON Flattened Serialization
        });

jose.JWS.createSign({ format: 'compact' }, key).
        update(input).
        final().
        then(function(result) {
          // {result} is a String -- JWS using the Compact Serialization
        });
```

To create a JWS using a specific algorithm:
```
jose.JWS.createSign({ alg: 'PS256' }, key).
        update(input).
        final().
        then(function(result) {
          // ....
        });
```

To create a JWS for a specified content type:

```
jose.JWS.createSign({ fields: { cty: 'jwk+json' } }, key).
        update(input).
        final().
        then(function(result) {
          // ....
        });
```

To create a JWS from String content:

```
jose.JWS.createSign(key).
        update(input, "utf8").
        final().
        then(function(result) {
          // ....
        });
```

To create a JWS with multiple signatures:

```
// {keys} is an Array of jose.JWK.Key instances
jose.JWS.createSign(keys).
        update(input).
        final().
        then(function(result) {
          // ....
        });
```

### Verifying a JWS ###

To verify a JWS, and retrieve the payload:

```
jose.JWS.createVerify(keystore).
        verify(input).
        then(function(result) {
          // {result} is a Object with:
          // *  header: the combined 'protected' and 'unprotected' header members
          // *  payload: Buffer of the signed content
          // *  signature: Buffer of the verified signature
          // *  key: The key used to verify the signature
        });
```

To verify using an implied Key:

```
// {key} can be:
// *  jose.JWK.Key
// *  JSON object representing a JWK
jose.JWS.createVerify(key).
        verify(input).
        then(function(result) {
          // ...
        });
```

To verify using a key embedded in the JWS:

```
jose.JWS.createVerify().
        verify(input).
        then(function(result) {
          // ...
        });
```

The key can be embedded using either 'jwk' or 'x5c', and can be located in either the JWS Unprotected Header or JWS Protected Header.

**NOTE:** `verify()` will use the embedded key (if found) instead of any other key.

#### Handling `crit` Header Members ####

To accept 'crit' field members, add the `handlers` member to the options Object.  The `handlers` member is itself an Object, where its member names are the `crit` header member, and the value is one of:

* `Boolean`: accepts (if `true`) -- or rejects (if `false`) -- the JWS if the member is present.
* `Function`: takes the JWE decrypt output (just prior to decrypting) and returns a Promise for the processing of the member.
* `Object`: An object with the following `Function` members:
  * "prepare" -- takes the JWE decrypt output (just prior to decrypting) and returns a Promise for the processing of the member.
  * "complete" -- takes the JWE decrypt output (immediately after decrypting) and returns a Promise for the processing of the member.

**NOTE** If the handler function returns a promise, the fulfilled value is ignored.  It is expected these handler functions will modify the provided value directly.

To simply accept a `crit` header member:

```
var opts = {
  handlers: {
    "exp": true
  }
};
jose.JWS.createVerify(key, opts).
        verify(input).
        then(function(result) {
          // ...
        });
```

To perform additional (pre-verify) processing on a `crit` header member:

```
var opts = {
  handlers: {
    "exp": function(jws) {
      // {jws} is the JWS verify output, pre-verification
      jws.header.exp = new Date(jws.header.exp);
    }
  }
};
jose.JWS.createVerify(key, opts).
        verify(input).
        then(function(result) {
          // ...
        });
```

To perform additional (post-verify) processing on a `crit` header member:

```
var opts = {
  handlers: {
    "exp": {
      complete: function(jws) {
        // {jws} is the JWS verify output, post-verification
        jws.header.exp = new Date(jws.header.exp);
      }
    }
  }
};
jose.JWS.createVerify(key, opts).
        verify(input).
        then(function(result) {
          // ...
        });
```


## Encryption ##


### Keys Used for Encrypting and Decrypting ###

When encrypting content, the key is expected to meet one of the following:

1. A secret key (e.g, `"kty":"oct"`)
2. The **public** key from a PKI (`"kty":"EC"` or `"kty":"RSA"`) key pair

When decrypting content, the key is expected to meet one of the following:

1. A secret key (e.g, `"kty":"oct"`)
2. The **private** key from a PKI (`"kty":"EC"` or `"kty":"RSA"`) key pair


### Encrypting Content ###

At its simplest, to create a JWE:

```
// {input} is a Buffer
jose.JWE.createEncrypt(key).
        update(input).
        final().
        then(function(result) {
          // {result} is a JSON Object -- JWE using the JSON General Serialization
        });
```

How the JWE content is encrypted depends on the provided Key.

* If the Key only supports content encryption algorithms, then the preferred algorithm is used to encrypt the content and the key encryption algorithm (i.e., the "alg" member) is set to "dir".  The preferred algorithm is the first item returned by `key.algorithms("encrypt")`.
* If the Key supports key management algorithms, then the JWE content is encrypted using "A128CBC-HS256" by default, and the Content Encryption Key is encrypted using the preferred algorithms for the given Key.  The preferred algorithm is the first item returned by `key.algorithms("wrap")`.


To create a JWE using a different serialization format:

```
jose.JWE.createEncrypt({ format: 'compact' }, key).
        update(input).
        final().
        then(function(result) {
          // {result} is a String -- JWE using the Compact Serialization
        });

jose.JWE.createEncrypt({ format: 'flattened' }, key).
        update(input).
        final().
        then(function(result) {
          // {result} is a JSON Object -- JWE using the JSON Flattened Serialization
        });
```

To create a JWE and compressing the content before encrypting:

```
jose.JWE.createEncrypt({ zip: true }, key).
        update(input).
        final().
        then(function(result) {
          // ....
        });
```

To create a JWE for a specific content type:

```
jose.JWE.createEncrypt({ fields: { cty : 'jwk+json' } }, key).
        update(input).
        final().
        then(function(result) {
          // ....
        });
```

To create a JWE with multiple recipients:

```
// {keys} is an Array of jose.JWK.Key instances
jose.JWE.createEncrypt(keys).
        update(input).
        final().
        then(function(result) {
          // ....
        });
```

### Decrypting a JWE ###

To decrypt a JWE, and retrieve the plaintext:

```
jose.JWE.createDecrypt(keystore).
        decrypt(input).
        then(function(result) {
          // {result} is a Object with:
          // *  header: the combined 'protected' and 'unprotected' header members
          // *  protected: an array of the member names from the "protected" member
          // *  key: Key used to decrypt
          // *  payload: Buffer of the decrypted content
          // *  plaintext: Buffer of the decrypted content (alternate)
        });
```

To decrypt a JWE using an implied key:

```
jose.JWE.createDecrypt(key).
        decrypt(input).
        then(function(result) {
          // ....
        });
```

#### Handling `crit` Header Members ####

To accept 'crit' field members, add the `handlers` member to the options Object.  The `handlers` member is itself an Object, where its member names are the `crit` header member, and the value is one of:

* `Boolean`: accepts (if `true`) -- or rejects (if `false`) -- the JWE if the member is present.
* `Function`: takes the JWE decrypt output (just prior to decrypting) and returns a Promise for the processing of the member.
* `Object`: An object with the following `Function` members:
  * "prepare" -- takes the JWE decrypt output (just prior to decrypting) and returns a Promise for the processing of the member.
  * "complete" -- takes the JWE decrypt output (immediately after decrypting) and returns a Promise for the processing of the member.

**NOTE** If the handler function returns a promise, the fulfilled value is ignored.  It is expected these handler functions will modify the provided value directly.

To simply accept a `crit` header member:

```
var opts = {
  handlers: {
    "exp": true
  }
};
jose.JWE.createDecrypt(key, opts).
        decrypt(input).
        then(function(result) {
          // ...
        });
```

To perform additional (pre-decrypt) processing on a `crit` header member:

```
var opts = {
  handlers: {
    "exp": function(jwe) {
      // {jwe} is the JWE decrypt output, pre-decryption
      jwe.header.exp = new Date(jwe.header.exp);
    }
  }
};
jose.JWE.createDecrypt(key, opts).
        decrypt(input).
        then(function(result) {
          // ...
        });
```

To perform additional (post-decrypt) processing on a `crit` header member:

```
var opts = {
  handlers: {
    "exp": {
      complete: function(jwe) {
        // {jwe} is the JWE decrypt output, post-decryption
        jwe.header.exp = new Date(jwe.header.exp);
      }
    }
  }
};
jose.JWE.createDecrypt(key, opts).
        decrypt(input).
        then(function(result) {
          // ...
        });
```

## Useful Utilities ##

### Converting to Buffer ###

To convert a [Typed Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Typed_arrays), [ArrayBuffer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer), or Array of Numbers to a Buffer:

```
buff = jose.util.asBuffer(input);
```

### URI-Safe Base64 ###

This exposes [urlsafe-base64](https://github.com/RGBboy/urlsafe-base64)'s `encode` and `decode` methods as `encode` and `decode` (respectively).

To convert from a Buffer to a base64uri-encoded String:

```
var output = jose.util.base64url.encode(input);
```

To convert a String to a base64uri-encoded String:

```
// explicit encoding
output = jose.util.base64url.encode(input, "utf8");

// implied "utf8" encoding
output = jose.util.base64url.encode(input);
```

To convert a base64uri-encoded String to a Buffer:

```
var output = jose.util.base64url.decode(input);
```

### Random Bytes ###

To generate a Buffer of octets, regardless of platform:

```
// argument is size (in bytes)
var rnd = jose.util.randomBytes(32);
```

This function uses:

* `crypto.randomBytes()` on node.js
* `crypto.getRandomValues()` on modern browsers
* A PRNG based on AES and SHA-1 for older platforms
