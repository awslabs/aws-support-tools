/*!
 * algorithms/hmac.js - HMAC-based "signatures"
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var CONSTANTS = require("./constants"),
    forge = require("../deps/forge.js"),
    DataBuffer = require("../util/databuffer.js"),
    helpers = require("./helpers.js");

function hmacSignFN(name) {
  var md = name.replace("HS", "SHA").toLowerCase(),
      hash = name.replace("HS", "SHA-");

  function checkKeyLength(len, key) {
    len = (len || CONSTANTS.HASHLENGTH[hash]) / 8;
    if (len > key.length) {
      return Promise.reject(new Error("invalid key length"));
    }

    return Promise.resolve(key);
  }

  // ### Fallback Implementation -- uses forge
  var fallback = function(key, pdata, props) {
    props = props || {};
    var promise;
    promise = checkKeyLength(props.length, key);
    promise = promise.then(function() {
      var sig = forge.hmac.create();
      sig.start(md, key.toString("binary"));
      sig.update(pdata);
      sig = sig.digest().native();

      return {
        data: pdata,
        mac: sig
      }
    });
    return promise;
  };

  // ### WebCryptoAPI Implementation
  var webcrypto = function(key, pdata, props) {
    props = props || {};

    var alg = {
      name: "HMAC",
      hash: {
        name: hash
      }
    };
    var promise;
    promise = checkKeyLength(props.length, key);
    promise = promise.then(function() {
      return helpers.subtleCrypto.importKey("raw", key, alg, true, ["sign"]);
    });
    promise = promise.then(function(key) {
      return helpers.subtleCrypto.sign(alg, key, pdata);
    });
    promise = promise.then(function(result) {
      var sig = new Buffer(result);
      return {
        data: pdata,
        mac: sig
      };
    });

    return promise;
  };

  // ### NodeJS implementation
  var nodejs = function(key, pdata, props) {
    props = props || {};

    var promise;
    promise = checkKeyLength(props.length, key);
    promise = promise.then(function() {
      var hmac = helpers.nodeCrypto.createHmac(md, key);
      hmac.update(pdata);

      var sig = hmac.digest();
      return {
        data: pdata,
        mac: sig
      };
    });
    return promise;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function hmacVerifyFN(name) {
  var md = name.replace("HS", "SHA").toLowerCase(),
      hash = name.replace("HS", "SHA-");

  function compare(len, expected, actual) {
    len = (len || CONSTANTS.HASHLENGTH[hash]) / 8;
    var valid = true;
    for (var idx = 0; len > idx; idx++) {
      valid = valid && (expected[idx] === actual[idx]);
    }
    return valid;
  }

  // ### Fallback Implementation -- uses forge
  var fallback = function(key, pdata, mac, props) {
    props = props || {};

    var vrfy = forge.hmac.create();
    vrfy.start(md, new DataBuffer(key));
    vrfy.update(pdata);
    vrfy = vrfy.digest().native();

    if (compare(props.length, mac, vrfy)) {
      return Promise.resolve({
        data: pdata,
        mac: mac,
        valid: true
      });
    } else {
      return Promise.reject(new Error("verification failed"));
    }
  };

  var webcrypto = function(key, pdata, mac, props) {
    props = props || {};

    var alg = {
      name: "HMAC",
      hash: {
        name: hash
      }
    };
    var promise;
    if (props.length) {
      promise = helpers.subtleCrypto.importKey("raw", key, alg, true, ["sign"]);
      promise = promise.then(function(key) {
        return helpers.subtleCrypto.sign(alg, key, pdata);
      });
      promise = promise.then(function(result) {
        var sig = new Buffer(result);
        return compare(props.length, mac, sig);
      });
    } else {
      promise = helpers.subtleCrypto.importKey("raw", key, alg, true, ["verify"]);
      promise = promise.then(function(key) {
        return helpers.subtleCrypto.verify(alg, key, mac, pdata);
      });
    }
    promise = promise.then(function(result) {
      if (!result) {
        return Promise.reject(new Error("verifaction failed"));
      }

      return {
        data: pdata,
        mac: mac,
        valid: true
      };
    });

    return promise;
  };

  var nodejs = function(key, pdata, mac, props) {
    props = props || {};

    var hmac = helpers.nodeCrypto.createHmac(md, key);
    hmac.update(pdata);

    var sig = hmac.digest();
    if (!compare(props.length, mac, sig)) {
      throw new Error("verification failed");
    }
    return {
      data: pdata,
      mac: sig,
      valid: true
    };
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

// ### Public API
// * [name].sign
// * [name].verify
var hmac = {};
[
  "HS1",
  "HS256",
  "HS384",
  "HS512"
].forEach(function(alg) {
  hmac[alg] = {
    sign: hmacSignFN(alg),
    verify: hmacVerifyFN(alg)
  };
});

module.exports = hmac;
