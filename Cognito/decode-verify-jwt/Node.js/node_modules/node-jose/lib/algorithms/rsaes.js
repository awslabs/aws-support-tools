/*!
 * algorithms/rsassa.js - RSA Signatures
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js"),
    helpers = require("./helpers.js"),
    DataBuffer = require("../util/databuffer.js"),
    rsaUtil = require("./rsa-util.js");

// ### RSAES-PKCS1-v1_5

// ### RSAES-OAEP
function rsaesEncryptFn(name) {
  var alg = {
    name: name
  };

  if ("RSA-OAEP-256" === name) {
    alg.name = "RSA-OAEP";
    alg.hash = {
      name: "SHA-256"
    };
  } else if ("RSA-OAEP" === name) {
    alg.hash = {
      name: "SHA-1"
    };
  } else {
    alg.name = "RSAES-PKCS1-v1_5";
  }

  // ### Fallback Implementation -- uses forge
  var fallback = function(key, pdata) {
    // convert pdata to byte string
    pdata = new DataBuffer(pdata).bytes();

    // encrypt it
    var pki = rsaUtil.convertToForge(key, true),
        params = {};
    if ("RSA-OAEP" === alg.name) {
      params.md = alg.hash.name.toLowerCase().replace(/\-/g, "");
      params.md = forge.md[params.md].create();
    }
    var cdata = pki.encrypt(pdata, alg.name.toUpperCase(), params);

    // convert cdata to Buffer
    cdata = new DataBuffer(cdata).native();

    return Promise.resolve({
      data: cdata
    });
  };

  // ### WebCryptoAPI Implementation
  var webcrypto;
  if ("RSAES-PKCS1-v1_5" !== alg.name) {
    webcrypto = function(key, pdata) {
      key = rsaUtil.convertToJWK(key, true);
      var promise;
      promise = helpers.subtleCrypto.importKey("jwk", key, alg, true, ["encrypt"]);
      promise = promise.then(function(key) {
        return helpers.subtleCrypto.encrypt(alg, key, pdata);
      });
      promise = promise.then(function(result) {
        var cdata = new Buffer(result);
        return {
          data: cdata
        };
      });

      return promise;
    };
  } else {
    webcrypto = null;
  }

  return helpers.setupFallback(null, webcrypto, fallback);
}

function rsaesDecryptFn(name) {
  var alg = {
    name: name
  };

  if ("RSA-OAEP-256" === name) {
    alg.name = "RSA-OAEP";
    alg.hash = {
      name: "SHA-256"
    };
  } else if ("RSA-OAEP" === name) {
    alg.hash = {
      name: "SHA-1"
    };
  } else {
    alg.name = "RSAES-PKCS1-v1_5";
  }

  // ### Fallback Implementation -- uses forge
  var fallback = function(key, cdata) {
    // convert cdata to byte string
    cdata = new DataBuffer(cdata).bytes();

    // decrypt it
    var pki = rsaUtil.convertToForge(key, false),
        params = {};
    if ("RSA-OAEP" === alg.name) {
      params.md = alg.hash.name.toLowerCase().replace(/\-/g, "");
      params.md = forge.md[params.md].create();
    }
    var pdata = pki.decrypt(cdata, alg.name.toUpperCase(), params);

    // convert pdata to Buffer
    pdata = new DataBuffer(pdata).native();

    return Promise.resolve(pdata);
  };

  // ### WebCryptoAPI Implementation
  var webcrypto;
  if ("RSAES-PKCS1-v1_5" !== alg.name) {
    webcrypto = function(key, pdata) {
      key = rsaUtil.convertToJWK(key, false);
      var promise;
      promise = helpers.subtleCrypto.importKey("jwk", key, alg, true, ["decrypt"]);
      promise = promise.then(function(key) {
        return helpers.subtleCrypto.decrypt(alg, key, pdata);
      });
      promise = promise.then(function(result) {
        var pdata = new Buffer(result);
        return pdata;
      });

      return promise;
    };
  } else {
    webcrypto = null;
  }

  var nodejs;
  if (helpers.nodeCrypto && name === "RSA-OAEP") { // node only support SHA1, plain RSA-OAEP
    nodejs = function(key, pdata) {
      key = rsaUtil.convertToPem(key, false);
      return helpers.nodeCrypto.privateDecrypt(key, pdata);
    };
  }

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

// ### Public API
// * [name].encrypt
// * [name].decrypt
var rsaes = {};
[
  "RSA-OAEP",
  "RSA-OAEP-256",
  "RSA1_5"
].forEach(function(name) {
  rsaes[name] = {
    encrypt: rsaesEncryptFn(name),
    decrypt: rsaesDecryptFn(name)
  };
});

module.exports = rsaes;
