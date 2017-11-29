/*!
 * algorithms/helpers.js - Internal functions and fields used in Cryptographic
 * Algorithms
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

if (typeof Promise === "undefined") {
  require("es6-promise").polyfill();
}

// ###
exports.int32ToBuffer = function(v, b) {
  b = b || new Buffer(4);
  b[0] = (v >>> 24) & 0xff;
  b[1] = (v >>> 16) & 0xff;
  b[2] = (v >>> 8) & 0xff;
  b[3] = v & 0xff;
  return b;
};

var MAX_INT32 = Math.pow(2, 32);
exports.int64ToBuffer = function(v, b) {
  b = b || new Buffer(8);
  var hi = Math.floor(v / MAX_INT32),
      lo = v % MAX_INT32;
  hi = exports.int32ToBuffer(hi);
  lo = exports.int32ToBuffer(lo);
  b = Buffer.concat([hi, lo]);
  return b;
};

// ### crypto and DOMException in browsers ###
/* global crypto:false, DOMException:false */

function getCryptoSubtle() {
  if ("undefined" !== typeof crypto) {
    if ("undefined" !== typeof crypto.subtle) {
      return crypto.subtle;
    }
  }

  return undefined;
}
function getCryptoNodeJS() {
  var crypto;
  try {
    crypto = require("crypto");
  } catch (err) {
    return undefined;
  }

  if (!Object.keys(crypto).length) {
    // treat empty the same as missing
    return undefined;
  }

  return crypto;
}

var supported = {};
Object.defineProperty(exports, "subtleCrypto", {
  get: function() {
    var result;

    if ("subtleCrypto" in supported) {
      result = supported.subtleCrypto;
    } else {
      result = supported.subtleCrypto = getCryptoSubtle();
    }

    return result;
  },
  enumerable: true
});
Object.defineProperty(exports, "nodeCrypto", {
  get: function() {
    var result;

    if ("nodeCrypto" in supported) {
      result = supported.nodeCrypto;
    } else {
      result = supported.nodeCrypto = getCryptoNodeJS();
    }

    return result;
  },
  enumerable: true
});

exports.setupFallback = function(nodejs, webcrypto, fallback) {
  var impl;

  if (nodejs && exports.nodeCrypto) {
    impl = function main() {
      var args = arguments,
          promise;

      function check(err) {
        if (0 === err.message.indexOf("unsupported algorithm:")) {
          impl = fallback;
          return impl.apply(null, args);
        }

        return Promise.reject(err);
      }

      try {
        promise = Promise.resolve(nodejs.apply(null, args));
      } catch(err) {
        promise = check(err);
      }

      return promise;
    };
  } else if (webcrypto && exports.subtleCrypto) {
    impl = function main() {
      var args = arguments,
         promise;

      function check(err) {
        if (err.code === DOMException.NOT_SUPPORTED_ERR ||
            // Firefox rejects some operations erroneously complaining about inputs
            err.message === "Only ArrayBuffer and ArrayBufferView objects can be passed as CryptoOperationData" ||
            // MS Edge rejects with not an Error
            !(err instanceof Error)) {
          // not actually supported -- always use fallback
          impl = fallback;
          return impl.apply(null, args);
        }

       return Promise.reject(err);
      }

      try {
        promise = webcrypto.apply(null, args);
        promise = promise.catch(check);
      } catch(err) {
        promise = check(err);
      }

      return promise;
    };
  } else {
    impl = fallback;
  }

  return impl;
};
