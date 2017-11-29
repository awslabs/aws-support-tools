/*!
 * algorithms/rsa-util.js - RSA Utility Functions
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var clone = require("lodash.clone"),
    forge = require("../deps/forge.js"),
    util = require("../util");

// ### RSA-specific Helpers
function convertToForge(key, isPublic) {
  var parts = isPublic ?
              ["n", "e"] :
              ["n", "e", "d", "p", "q", "dp", "dq", "qi"];
  parts = parts.map(function(f) {
    return new forge.jsbn.BigInteger(key[f].toString("hex"), 16);
  });

  var fn = isPublic ?
           forge.pki.rsa.setPublicKey :
           forge.pki.rsa.setPrivateKey;
  return fn.apply(forge.pki.rsa, parts);
}

function convertToJWK(key, isPublic) {
  var result = clone(key);
  var parts = isPublic ?
              ["n", "e"] :
              ["n", "e", "d", "p", "q", "dp", "dq", "qi"];
  parts.forEach(function(f) {
    result[f] = util.base64url.encode(result[f]);
  });

  // remove potentially troublesome properties
  delete result.key_ops;
  delete result.use;
  delete result.alg;

  if (isPublic) {
    delete result.d;
    delete result.p;
    delete result.q;
    delete result.dp;
    delete result.dq;
    delete result.qi;
  }

  return result;
}

function convertToPem(key, isPublic) {
  if (key.__cachedPem) {
    return key.__cachedPem;
  }

  var value;
  if (isPublic) {
    value = forge.pki.publicKeyToPem(convertToForge(key, isPublic));
  } else {
    value = forge.pki.privateKeyToPem(convertToForge(key, isPublic));
  }

  Object.defineProperty(key, '__cachedPem', { value: value });
  return value;
}

module.exports = {
  convertToForge: convertToForge,
  convertToJWK: convertToJWK,
  convertToPem: convertToPem
};
