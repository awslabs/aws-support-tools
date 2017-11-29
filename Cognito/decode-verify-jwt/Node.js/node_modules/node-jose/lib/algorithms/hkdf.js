/*!
 * algorithms/hkdf.js - HMAC-based Extract-and-Expand Key Derivation
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var CONSTANTS = require("./constants.js"),
    hmac = require("./hmac.js");

function hkdfDeriveFn(name) {
  var hash = name.replace("HKDF-", ""),
      op = name.replace("HKDF-SHA-", "HS");

  // NOTE: no nodejs/webcrypto/fallback model, since this HKDF is
  //       implemented using the HMAC algorithms

  var fn = function(key, props) {
    var hashLen = CONSTANTS.HASHLENGTH[hash] / 8;

    if ("string" === typeof op) {
      op = hmac[op].sign;
    }

    // prepare options
    props = props || {};
    var salt = props.salt;
    if (!salt || 0 === salt.length) {
      salt = new Buffer(hashLen);
      salt.fill(0);
    }
    var info = props.info || new Buffer(0);
    var keyLen = props.length || hashLen;

    var promise;

    // Setup Expansion
    var N = Math.ceil(keyLen / hashLen),
        okm = [],
        idx = 0;
    function expand(key, T) {
      if (N === idx++) {
        return Buffer.concat(okm).slice(0, keyLen);
      }

      if (!T) {
        T = new Buffer(0);
      }
      T = Buffer.concat([T, info, new Buffer([idx])]);
      T = op(key, T);
      T = T.then(function(result) {
        T = result.mac;
        okm.push(T);

        return expand(key, T);
      });
      return T;
    }

    // Step 1: Extract
    promise = op(salt, key, { length: salt.length * 8 });
    promise = promise.then(function(result) {
      // Step 2: Expand
      return expand(result.mac);
    });

    return promise;
  };

  return fn;
}

// Public API
// * [name].derive
var hkdf = {};
[
  "HKDF-SHA-1",
  "HKDF-SHA-256",
  "HKDF-SHA-384",
  "HKDF-SHA-512"
].forEach(function(name) {
  hkdf[name] = {
    derive: hkdfDeriveFn(name)
  };
});

module.exports = hkdf;
