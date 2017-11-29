/*!
 * algorithms/concat.js - Concat Key Derivation
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var CONSTANTS = require("./constants.js"),
    sha = require("./sha.js");

function concatDeriveFn(name) {
  name = name.replace("CONCAT-", "");

  // NOTE: no nodejs/webcrypto/fallback model, since ConcatKDF is
  //       implemented using the SHA algorithms

  var fn = function(key, props) {
    props = props || {};

    var keyLen = props.length,
        hashLen = CONSTANTS.HASHLENGTH[name];
    if (!keyLen) {
      return Promise.reject(new Error("invalid key length"));
    }

    // setup otherInfo
    if (!props.otherInfo) {
      return Promise.reject(new Error("invalid otherInfo"));
    }
    var otherInfo = props.otherInfo;

    var op = sha[name].digest;
    var N = Math.ceil(keyLen / hashLen),
        idx = 0,
        okm = [];
    function step() {
      if (N === idx++) {
        return Buffer.concat(okm).slice(0, keyLen);
      }

      var T = new Buffer(4 + key.length + otherInfo.length);
      T.writeUInt32BE(idx, 0);
      key.copy(T, 4);
      otherInfo.copy(T, 4 + key.length);
      return op(T).then(function(result) {
        okm.push(result);
        return step();
      });
    }

    return step();
  };

  return fn;
}

// Public API
// * [name].derive
var concat = {};
[
  "CONCAT-SHA-1",
  "CONCAT-SHA-256",
  "CONCAT-SHA-384",
  "CONCAT-SHA-512"
].forEach(function(name) {
  concat[name] = {
    derive: concatDeriveFn(name)
  };
});

module.exports = concat;
