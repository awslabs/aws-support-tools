/*!
 * algorithms/index.js - Cryptographic Algorithms Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

// setup implementations
var implementations = [
  require("./aes-cbc-hmac-sha2.js"),
  require("./aes-gcm.js"),
  require("./aes-kw.js"),
  require("./concat.js"),
  require("./dir.js"),
  require("./ecdh.js"),
  require("./ecdsa.js"),
  require("./hkdf.js"),
  require("./hmac.js"),
  require("./pbes2.js"),
  require("./rsaes.js"),
  require("./rsassa.js"),
  require("./sha.js")
];

var ALGS_DIGEST = {};
var ALGS_DERIVE = {};
var ALGS_SIGN = {},
    ALGS_VRFY = {};
var ALGS_ENC = {},
    ALGS_DEC = {};

implementations.forEach(function(mod) {
  Object.keys(mod).forEach(function(alg) {
    var op = mod[alg];

    if ("function" === typeof op.encrypt) {
      ALGS_ENC[alg] = op.encrypt;
    }
    if ("function" === typeof op.decrypt) {
      ALGS_DEC[alg] = op.decrypt;
    }
    if ("function" === typeof op.sign) {
      ALGS_SIGN[alg] = op.sign;
    }
    if ("function" === typeof op.verify) {
      ALGS_VRFY[alg] = op.verify;
    }
    if ("function" === typeof op.digest) {
      ALGS_DIGEST[alg] = op.digest;
    }
    if ("function" === typeof op.derive) {
      ALGS_DERIVE[alg] = op.derive;
    }
  });
});

// public API
exports.digest = function(alg, data, props) {
  var op = ALGS_DIGEST[alg];
  if (!op) {
    return Promise.reject(new Error("unsupported algorithm: " + alg));
  }

  return op(data, props);
};

exports.derive = function(alg, key, props) {
  var op = ALGS_DERIVE[alg];
  if (!op) {
    return Promise.reject(new Error("unsupported algorithm: " + alg));
  }

  return op(key, props);
};

exports.sign = function(alg, key, pdata, props) {
  var op = ALGS_SIGN[alg];
  if (!op) {
    return Promise.reject(new Error("unsupported algorithm: " + alg));
  }

  return op(key, pdata, props || {});
};

exports.verify = function(alg, key, pdata, mac, props) {
  var op = ALGS_VRFY[alg];
  if (!op) {
    return Promise.reject(new Error("unsupported algorithm: " + alg));
  }

  return op(key, pdata, mac, props || {});
};

exports.encrypt = function(alg, key, pdata, props) {
  var op = ALGS_ENC[alg];
  if (!op) {
    return Promise.reject(new Error("unsupported algorithm: " + alg));
  }

  return op(key, pdata, props || {});
};

exports.decrypt = function(alg, key, cdata, props) {
  var op = ALGS_DEC[alg];
  if (!op) {
    return Promise.reject(new Error("unsupported algorithm: " + alg));
  }

  return op(key, cdata, props || {});
};
