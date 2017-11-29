/*!
 * algorithms/ecdh.js - Elliptic Curve Diffie-Hellman algorithms
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var clone = require("lodash.clone"),
    merge = require("../util/merge"),
    omit = require("lodash.omit"),
    pick = require("lodash.pick"),
    util = require("../util"),
    ecUtil = require("./ec-util.js"),
    hkdf = require("./hkdf.js"),
    concat = require("./concat.js"),
    aesKw = require("./aes-kw.js"),
    helpers = require("./helpers.js"),
    CONSTANTS = require("./constants.js");

function idealHash(curve) {
  switch (curve) {
    case "P-256":
      return "SHA-256";
    case "P-384":
      return "SHA-384";
    case "P-521":
      return "SHA-512";
    default:
      throw new Error("unsupported curve: " + curve);
  }
}

// ### Exported
var ecdh = module.exports = {};

// ### Derivation algorithms
// ### "raw" ECDH
function ecdhDeriveFn() {
  var alg = {
    name: "ECDH"
  };

  var validatePublic = function(pk, form) {
    var pubKey = pk && ecUtil.convertToForge(pk, true);
    if (!pubKey || !pubKey.isValid()) {
      return Promise.reject(new Error("invalid EC public key"));
    }

    switch (form) {
      case "jwk":
        pubKey = ecUtil.convertToJWK(pk, true);
        break;
      case "buffer":
        pubKey = ecUtil.convertToBuffer(pk, true);
        break;
    }
    return Promise.resolve(pubKey);
  }

  // ### fallback implementation -- uses ecc + forge
  var fallback = function(key, props) {
    props = props || {};
    var keyLen = props.length || 0;
    // assume {key} is privateKey
    // assume {props.public} is publicKey
    var privKey = ecUtil.convertToForge(key, false);

    var p = validatePublic(props.public, "forge");
    p = p.then(function(pubKey) {
      // {pubKey} is "forge"

      var secret = privKey.computeSecret(pubKey);
      if (keyLen) {
        // truncate to requested key length
        if (secret.length < keyLen) {
          return Promise.reject(new Error("key length too large: " + keyLen));
        }
        secret = secret.slice(0, keyLen);
      }

      return secret;
    });
    return p;
  };

  // ### WebCryptoAPI implementation
  // TODO: cache CryptoKey sooner
  var webcrypto = function(key, props) {
    key = key || {};
    props = props || {};

    var keyLen = props.length || 0,
        algParams = merge(clone(alg), {
          namedCurve: key.crv
        });

    // assume {key} is privateKey
    if (!keyLen) {
      // calculate key length from private key size
      keyLen = key.d.length;
    }
    var privKey = ecUtil.convertToJWK(key, false);
    privKey = helpers.subtleCrypto.importKey("jwk",
                                             privKey,
                                             algParams,
                                             false,
                                             [ "deriveBits" ]);

    // assume {props.public} is publicKey
    var pubKey = validatePublic(props.public, "jwk");
    pubKey = pubKey.then(function(pubKey) {
      // {pubKey} is "jwk"
      return helpers.subtleCrypto.importKey("jwk",
                                            pubKey,
                                            algParams,
                                            false,
                                            []);
    });

    var p = Promise.all([privKey, pubKey]);
    p = p.then(function(keypair) {
      var privKey = keypair[0],
          pubKey = keypair[1];

      var algParams = merge(clone(alg), {
        public: pubKey
      });
      return helpers.subtleCrypto.deriveBits(algParams, privKey, keyLen * 8);
    });
    p = p.then(function(result) {
      result = new Buffer(result);
      return result;
    });
    return p;
  };

  var nodejs = function(key, props) {
    if ("function" !== typeof helpers.nodeCrypto.createECDH) {
      throw new Error("unsupported algorithm: ECDH");
    }

    props = props || {};
    var keyLen = props.length || 0;
    var curve;
    switch (key.crv) {
      case "P-256":
        curve = "prime256v1";
        break;
      case "P-384":
        curve = "secp384r1";
        break;
      case "P-521":
        curve = "secp521r1";
        break;
      default:
        return Promise.reject(new Error("invalid curve: " + curve));
    }

    // assume {key} is privateKey
    // assume {props.public} is publicKey
    var privKey = ecUtil.convertToBuffer(key, false);

    var p = validatePublic(props.public, "buffer");
    p = p.then(function(pubKey) {
      // {pubKey} is "buffer"
      var ecdh = helpers.nodeCrypto.createECDH(curve);
      // dummy call so computeSecret doesn't fail
      // ecdh.generateKeys();
      ecdh.setPrivateKey(privKey);
      var secret = ecdh.computeSecret(pubKey);
      if (keyLen) {
        if (secret.length < keyLen) {
          return Promise.reject(new Error("key length too large: " + keyLen));
        }
        secret = secret.slice(0, keyLen);
      }
      return secret;
    });
    return p;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function ecdhConcatDeriveFn() {
  // NOTE: no nodejs/webcrypto/fallback model, since this algorithm is
  //       implemented using other primitives

  var fn = function(key, props) {
    props = props || {};

    var hash;
    try {
      hash = props.hash || idealHash(key.crv);
      if (!hash) {
        throw new Error("invalid hash: " + hash);
      }
      hash.toUpperCase();
    } catch (ex) {
      return Promise.reject(ex);
    }

    var params = ["public"];
    // derive shared secret
    // NOTE: whitelist items from {props} for ECDH
    var promise = ecdh.ECDH.derive(key, pick(props, params));
    // expand
    promise = promise.then(function(shared) {
      // NOTE: blacklist items from {props} for ECDH
      return concat["CONCAT-" + hash].derive(shared, omit(props, params));
    });
    return promise;
  };

  return fn;
}

function ecdhHkdfDeriveFn() {
  // NOTE: no nodejs/webcrypto/fallback model, since this algorithm is
  //       implemented using other primitives

  var fn = function(key, props) {
    props = props || {};

    var hash;
    try {
      hash = props.hash || idealHash(key.crv);
      if (!hash) {
        throw new Error("invalid hash: " + hash);
      }
      hash.toUpperCase();
    } catch (ex) {
      return Promise.reject(ex);
    }

    var params = ["public"];
    // derive shared secret
    // NOTE: whitelist items from {props} for ECDH
    var promise = ecdh.ECDH.derive(key, pick(props, params));
    // extract-and-expand
    promise = promise.then(function(shared) {
      // NOTE: blacklist items from {props} for ECDH
      return hkdf["HKDF-" + hash].derive(shared, omit(props, params));
    });
    return promise;
  };

  return fn;
}

// ### Wrap/Unwrap algorithms
function doEcdhesCommonDerive(privKey, pubKey, props) {
  function prependLen(input) {
    return Buffer.concat([
      helpers.int32ToBuffer(input.length),
      input
    ]);
  }

  var algId = props.algorithm || "",
      keyLen = CONSTANTS.KEYLENGTH[algId],
      apu = util.asBuffer(props.apu || "", "base64url"),
      apv = util.asBuffer(props.apv || "", "base64url");
  var otherInfo = Buffer.concat([
    prependLen(new Buffer(algId, "utf8")),
    prependLen(apu),
    prependLen(apv),
    helpers.int32ToBuffer(keyLen)
  ]);

  var params = {
    public: pubKey,
    length: keyLen / 8,
    hash: "SHA-256",
    otherInfo: otherInfo
  };
  return ecdh["ECDH-CONCAT"].derive(privKey, params);
}

function ecdhesDirEncryptFn() {
  // NOTE: no nodejs/webcrypto/fallback model, since this algorithm is
  //       implemented using other primitives
  var fn = function(key, pdata, props) {
    props = props || {};

    // {props.epk} is private
    if (!props.epk || !props.epk.d) {
      return Promise.reject(new Error("missing ephemeral private key"));
    }
    var epk = ecUtil.convertToObj(props.epk, false);

    // {key} is public
    if (!key || !key.x || !key.y) {
      return Promise.reject(new Error("missing static public key"));
    }
    var spk = ecUtil.convertToObj(key, true);

    // derive ECDH shared
    var promise = doEcdhesCommonDerive(epk, spk, {
      algorithm: props.enc,
      apu: props.apu,
      apv: props.apv
    });
    promise = promise.then(function(shared) {
      return {
        data: shared,
        once: true,
        direct: true
      };
    });
    return promise;
  };

  return fn;
}
function ecdhesDirDecryptFn() {
  // NOTE: no nodejs/webcrypto/fallback model, since this algorithm is
  //       implemented using other primitives
  var fn = function(key, cdata, props) {
    props = props || {};

    // {props.epk} is public
    if (!props.epk || !props.epk.x || !props.epk.y) {
      return Promise.reject(new Error("missing ephemeral public key"));
    }
    var epk = ecUtil.convertToObj(props.epk, true);

    // {key} is private
    if (!key || !key.d) {
      return Promise.reject(new Error("missing static private key"));
    }
    var spk = ecUtil.convertToObj(key, false);

    // derive ECDH shared
    var promise = doEcdhesCommonDerive(spk, epk, {
      algorithm: props.enc,
      apu: props.apu,
      apv: props.apv
    });
    promise = promise.then(function(shared) {
      return shared;
    });
    return promise;
  };

  return fn;
}

function ecdhesKwEncryptFn(wrap) {
  // NOTE: no nodejs/webcrypto/fallback model, since this algorithm is
  //       implemented using other primitives
  var fn = function(key, pdata, props) {
    props = props || {};

    // {props.epk} is private
    if (!props.epk || !props.epk.d) {
      return Promise.reject(new Error("missing ephemeral private key"));
    }
    var epk = ecUtil.convertToObj(props.epk, false);

    // {key} is public
    if (!key || !key.x || !key.y) {
      return Promise.reject(new Error("missing static public key"));
    }
    var spk = ecUtil.convertToObj(key, true);

    // derive ECDH shared
    var promise = doEcdhesCommonDerive(epk, spk, {
      algorithm: props.alg,
      apu: props.apu,
      apv: props.apv
    });
    promise = promise.then(function(shared) {
      // wrap provided key with ECDH shared
      return wrap(shared, pdata);
    });
    return promise;
  };

  return fn;
}

function ecdhesKwDecryptFn(unwrap) {
  // NOTE: no nodejs/webcrypto/fallback model, since this algorithm is
  //       implemented using other primitives
  var fn = function(key, cdata, props) {
    props = props || {};

    // {props.epk} is public
    if (!props.epk || !props.epk.x || !props.epk.y) {
      return Promise.reject(new Error("missing ephemeral public key"));
    }
    var epk = ecUtil.convertToObj(props.epk, true);

    // {key} is private
    if (!key || !key.d) {
      return Promise.reject(new Error("missing static private key"));
    }
    var spk = ecUtil.convertToObj(key, false);

    // derive ECDH shared
    var promise = doEcdhesCommonDerive(spk, epk, {
      algorithm: props.alg,
      apu: props.apu,
      apv: props.apv
    });
    promise = promise.then(function(shared) {
      // unwrap provided key with ECDH shared
      return unwrap(shared, cdata);
    });
    return promise;
  };

  return fn;
}

// ### Public API
// * [name].derive
[
  "ECDH",
  "ECDH-HKDF",
  "ECDH-CONCAT"
].forEach(function(name) {
  var kdf = /^ECDH(?:-(\w+))?$/g.exec(name || "")[1];
  var op = ecdh[name] = ecdh[name] || {};
  switch (kdf || "") {
    case "CONCAT":
      op.derive = ecdhConcatDeriveFn();
      break;
    case "HKDF":
      op.derive = ecdhHkdfDeriveFn();
      break;
    case "":
      op.derive = ecdhDeriveFn();
      break;
    default:
      op.derive = null;
  }
});

// * [name].encrypt
// * [name].decrypt
[
  "ECDH-ES",
  "ECDH-ES+A128KW",
  "ECDH-ES+A192KW",
  "ECDH-ES+A256KW"
].forEach(function(name) {
  var kw = /^ECDH-ES(?:\+(.+))?/g.exec(name || "")[1];
  var op = ecdh[name] = ecdh[name] || {};
  if (!kw) {
    op.encrypt = ecdhesDirEncryptFn();
    op.decrypt = ecdhesDirDecryptFn();
  } else {
    kw = aesKw[kw];
    if (kw) {
      op.encrypt = ecdhesKwEncryptFn(kw.encrypt);
      op.decrypt = ecdhesKwDecryptFn(kw.decrypt);
    } else {
      op.ecrypt = op.decrypt = null;
    }
  }
});
//*/
