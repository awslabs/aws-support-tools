/*!
 * algorithms/rsassa.js - RSA Signatures
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js"),
    CONSTANTS = require("./constants"),
    helpers = require("./helpers.js"),
    rsaUtil = require("./rsa-util.js");

// ### RSASSA-PKCS1-v1_5

function rsassaV15SignFn(name) {
  var md = name.replace("RS", "SHA").toLowerCase(),
      hash = name.replace("RS", "SHA-");

  var alg = {
    name: "RSASSA-PKCS1-V1_5",
    hash: {
      name: hash
    }
  };

  // ### Fallback Implementation -- uses forge
  var fallback = function(key, pdata) {
    // create the digest
    var digest = forge.md[md].create();
    digest.start();
    digest.update(pdata);

    // sign it
    var pki = rsaUtil.convertToForge(key, false);
    var sig = pki.sign(digest, "RSASSA-PKCS1-V1_5");
    sig = new Buffer(sig, "binary");

    return Promise.resolve({
      data: pdata,
      mac: sig
    });
  };

  // ### WebCryptoAPI Implementation
  var webcrypto = function(key, pdata) {
    key = rsaUtil.convertToJWK(key, false);
    var promise;
    promise = helpers.subtleCrypto.importKey("jwk", key, alg, true, ["sign"]);
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

  var nodejs;
  if (helpers.nodeCrypto && helpers.nodeCrypto.getHashes().indexOf(hash) > -1) {
    nodejs = function(key, pdata) {
      key = rsaUtil.convertToPem(key, false);
      var sign = helpers.nodeCrypto.createSign(hash);
      sign.update(pdata);

      return {
        data: pdata,
        mac: sign.sign(rsaUtil.convertToPem(key, false))
      };
    };
  }

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function rsassaV15VerifyFn(name) {
  var md = name.replace("RS", "SHA").toLowerCase(),
      hash = name.replace("RS", "SHA-");
  var alg = {
    name: "RSASSA-PKCS1-V1_5",
    hash: {
      name: hash
    }
  };

  // ### Fallback implementation -- uses forge
  var fallback = function(key, pdata, mac) {
    // create the digest
    var digest = forge.md[md].create();
    digest.start();
    digest.update(pdata);
    digest = digest.digest().bytes();

    // verify it
    var pki = rsaUtil.convertToForge(key, true);
    var sig = mac.toString("binary");
    var result = pki.verify(digest, sig, "RSASSA-PKCS1-V1_5");
    if (!result) {
      return Promise.reject(new Error("verification failed"));
    }
    return Promise.resolve({
      data: pdata,
      mac: mac,
      valid: true
    });
  };

  // ### WebCryptoAPI Implementation
  var webcrypto = function(key, pdata, mac) {
    key = rsaUtil.convertToJWK(key, true);
    var promise;
    promise = helpers.subtleCrypto.importKey("jwk", key, alg, true, ["verify"]);
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

  var nodejs;
  if (helpers.nodeCrypto && helpers.nodeCrypto.getHashes().indexOf(md) > -1) {
    nodejs = function(key, pdata, mac) {
      var verify = helpers.nodeCrypto.createVerify(md);
      verify.update(pdata);
      verify.end();
      var result = verify.verify(rsaUtil.convertToPem(key, true), mac);
      if (!result) {
        return Promise.reject(new Error("verification failed"));
      }

      return {
        data: pdata,
        mac: mac,
        valid: true,
      };
    };
  }

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

// ### RSA-PSS
// NOTE: no WebCryptoAPI variant -- too many browsers don't
// implement it yet (e.g., Firefox, Safari)

function rsassaPssSignFn(name) {
  var md = name.replace("PS", "SHA").toLowerCase(),
      hash = name.replace("PS", "SHA-");

  return function(key, pdata) {
    // create the digest
    var digest = forge.md[md].create();
    digest.start();
    digest.update(pdata);

    // setup padding
    var pss = forge.pss.create({
      md: forge.md[md].create(),
      mgf: forge.mgf.mgf1.create(forge.md[md].create()),
      saltLength: CONSTANTS.HASHLENGTH[hash] / 8
    });

    // sign it
    var pki = rsaUtil.convertToForge(key, false);
    var sig = pki.sign(digest, pss);
    sig = new Buffer(sig, "binary");

    return Promise.resolve({
      data: pdata,
      mac: sig
    });
  };
}

function rsassaPssVerifyFn(name) {
  var md = name.replace("PS", "SHA").toLowerCase(),
      hash = name.replace("PS", "SHA-");

  // ### Fallback implementation -- uses forge
  return function(key, pdata, mac) {
    // create the digest
    var digest = forge.md[md].create();
    digest.start();
    digest.update(pdata);
    digest = digest.digest().bytes();

    // setup padding
    var pss = forge.pss.create({
      md: forge.md[md].create(),
      mgf: forge.mgf.mgf1.create(forge.md[md].create()),
      saltLength: CONSTANTS.HASHLENGTH[hash] / 8
    });

    // verify it
    var pki = rsaUtil.convertToForge(key, true);
    var sig = mac.toString("binary");
    var result = pki.verify(digest, sig, pss);
    if (!result) {
      return Promise.reject(new Error("verification failed"));
    }
    return Promise.resolve({
      data: pdata,
      mac: mac,
      valid: true
    });
  };
}

// ### Public API
// * [name].sign
// * [name].verify
var rsassa = {};
[
  "PS256",
  "PS384",
  "PS512"
].forEach(function(name) {
  rsassa[name] = {
    sign: rsassaPssSignFn(name),
    verify: rsassaPssVerifyFn(name)
  };
});

[
  "RS256",
  "RS384",
  "RS512"
].forEach(function(name) {
  rsassa[name] = {
    sign: rsassaV15SignFn(name),
    verify: rsassaV15VerifyFn(name)
  };
});

module.exports = rsassa;
