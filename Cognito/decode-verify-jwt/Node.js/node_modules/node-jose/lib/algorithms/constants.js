/*!
 * algorithms/constants.js - Constants used in Cryptographic Algorithms
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
 "use strict";

module.exports = {
  CHUNK_SIZE: 1024,
  HASHLENGTH: {
    "SHA-1": 160,
    "SHA-256": 256,
    "SHA-384": 384,
    "SHA-512": 512
  },
  ENCLENGTH: {
    "AES-128-CBC": 128,
    "AES-192-CBC": 192,
    "AES-256-CBC": 256,
    "AES-128-KW": 128,
    "AES-192-KW": 192,
    "AES-256-KW": 256
  },
  KEYLENGTH: {
    "A128CBC-HS256": 256,
    "A192CBC-HS384": 384,
    "A256CBC-HS512": 512,
    "A128CBC+HS256": 256,
    "A192CBC+HS384": 384,
    "A256CBC+HS512": 512,
    "A128GCM": 128,
    "A192GCM": 192,
    "A256GCM": 256,
    "A128KW": 128,
    "A192KW": 192,
    "A256KW": 256,
    "ECDH-ES+A128KW": 128,
    "ECDH-ES+A192KW": 192,
    "ECDH-ES+A256KW": 256
  },
  NONCELENGTH: {
    "A128CBC-HS256": 128,
    "A192CBC-HS384": 128,
    "A256CBC-HS512": 128,
    "A128CBC+HS256": 128,
    "A192CBC+HS384": 128,
    "A256CBC+HS512": 128,
    "A128GCM": 96,
    "A192GCM": 96,
    "A256GCM": 96
  }
};
