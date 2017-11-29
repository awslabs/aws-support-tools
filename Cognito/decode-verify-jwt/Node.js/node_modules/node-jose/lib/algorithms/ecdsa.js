/*!
 * algorithms/ecdsa.js - Elliptic Curve Digitial Signature Algorithms
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var ecUtil = require("./ec-util.js"),
    helpers = require("./helpers.js"),
    sha = require("./sha.js");

function idealCurve(hash) {
  switch (hash) {
    case "SHA-256":
      return "P-256";
    case "SHA-384":
      return "P-384";
    case "SHA-512":
      return "P-521";
    default:
      throw new Error("unsupported hash: " + hash);
  }
}

function ecdsaSignFN(hash) {
  var curve = idealCurve(hash);

  // ### Fallback implementation -- uses forge
  var fallback = function(key, pdata /*, props */) {
    if (curve !== key.crv) {
      return Promise.reject(new Error("invalid curve"));
    }
    var pk = ecUtil.convertToForge(key, false);

    var promise;
    // generate hash
    promise = sha[hash].digest(pdata);
    // sign hash
    promise = promise.then(function(result) {
      result = pk.sign(result);
      result = Buffer.concat([result.r, result.s]);
      return {
        data: pdata,
        mac: result
      };
    });
    return promise;
  };

  // ### WebCrypto API implementation
  var webcrypto = function(key, pdata /*, props */) {
    if (curve !== key.crv) {
      return Promise.reject(new Error("invalid curve"));
    }
    var pk = ecUtil.convertToJWK(key, false);

    var promise;
    var alg = {
      name: "ECDSA",
      namedCurve: pk.crv,
      hash: {
        name: hash
      }
    };
    promise = helpers.subtleCrypto.importKey("jwk",
                                             pk,
                                             alg,
                                             true,
                                             [ "sign" ]);
    promise = promise.then(function(key) {
      return helpers.subtleCrypto.sign(alg, key, pdata);
    });
    promise = promise.then(function(result) {
      result = new Buffer(result);
      return {
        data: pdata,
        mac: result
      };
    });
    return promise;
  };

  return helpers.setupFallback(null, webcrypto, fallback);
}

function ecdsaVerifyFN(hash) {
  var curve = idealCurve(hash);

  // ### Fallback implementation -- uses forge
  var fallback = function(key, pdata, mac /*, props */) {
    if (curve !== key.crv) {
      return Promise.reject(new Error("invalid curve"));
    }
    var pk = ecUtil.convertToForge(key, true);

    var promise;
    // generate hash
    promise = sha[hash].digest(pdata);
    // verify hash
    promise = promise.then(function(result) {
      var len = mac.length / 2;
      var rs = {
        r: mac.slice(0, len),
        s: mac.slice(len)
      };
      if (!pk.verify(result, rs)) {
        return Promise.reject(new Error("verification failed"));
      }
      return {
        data: pdata,
        mac: mac,
        valid: true
      };
    });
    return promise;
  };

  // ### WebCrypto API implementation
  var webcrypto = function(key, pdata, mac /* , props */) {
    if (curve !== key.crv) {
      return Promise.reject(new Error("invalid curve"));
    }
    var pk = ecUtil.convertToJWK(key, true);

    var promise;
    var alg = {
      name: "ECDSA",
      namedCurve: pk.crv,
      hash: {
        name: hash
      }
    };
    promise = helpers.subtleCrypto.importKey("jwk",
                                             pk,
                                             alg,
                                             true,
                                             ["verify"]);
    promise = promise.then(function(key) {
      return helpers.subtleCrypto.verify(alg, key, mac, pdata);
    });
    promise = promise.then(function(result) {
      if (!result) {
        return Promise.reject(new Error("verification failed"));
      }
      return {
        data: pdata,
        mac: mac,
        valid: true
      };
    });
    return promise;
  };

  return helpers.setupFallback(null, webcrypto, fallback);
}

// ### Public API
var ecdsa = {};

// * [name].sign
// * [name].verify
[
  "ES256",
  "ES384",
  "ES512"
].forEach(function(name) {
  var hash = name.replace(/ES(\d+)/g, function(m, size) {
    return "SHA-" + size;
  });
  ecdsa[name] = {
    sign: ecdsaSignFN(hash),
    verify: ecdsaVerifyFN(hash)
  };
});

module.exports = ecdsa;
