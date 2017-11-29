/*!
 * algorithms/pbes2.js - Password-Based Encryption (v2) Algorithms
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js"),
    util = require("../util"),
    helpers = require("./helpers.js"),
    CONSTANTS = require("./constants.js"),
    KW = require("./aes-kw.js");

var NULL_BUFFER = new Buffer([0]);

function fixSalt(hmac, kw, salt) {
  var alg = "PBES2-" + hmac + "+" + kw;
  var output = [
    new Buffer(alg, "utf8"),
    NULL_BUFFER,
    salt
  ];
  return Buffer.concat(output);
}

function pbkdf2Fn(hash) {
  function prepareProps(props) {
    props = props || {};
    var keyLen = props.length || 0;
    var salt = util.asBuffer(props.salt || new Buffer(0), "base64u4l"),
        itrs = props.iterations || 0;

    if (0 >= keyLen) {
      throw new Error("invalid key length");
    }
    if (0 >= itrs) {
      throw new Error("invalid iteration count");
    }

    props.length = keyLen;
    props.salt = salt;
    props.iterations = itrs;

    return props;
  }

  var fallback = function(key, props) {
    try {
      props = prepareProps(props);
    } catch (err) {
      return Promise.reject(err);
    }

    var keyLen = props.length,
        salt = props.salt,
        itrs = props.iterations;

    var promise = new Promise(function(resolve, reject) {
      var md = forge.md[hash.replace("-", "").toLowerCase()].create();
      var cb = function(err, dk) {
        if (err) {
          reject(err);
        } else {
          dk = new Buffer(dk, "binary");
          resolve(dk);
        }
      };

      forge.pkcs5.pbkdf2(key.toString("binary"),
                         salt.toString("binary"),
                         itrs,
                         keyLen,
                         md,
                         cb);
    });
    return promise;
  };
  var webcrypto = function(key, props) {
    try {
      props = prepareProps(props);
    } catch (err) {
      return Promise.reject(err);
    }

    var keyLen = props.length,
        salt = props.salt,
        itrs = props.iterations;

    var promise = Promise.resolve(key);
    promise = promise.then(function(keyval) {
      return helpers.subtleCrypto.importKey("raw", keyval, "PBKDF2", false, ["deriveBits"]);
    });
    promise = promise.then(function(key) {
      var mainAlgo = {
        name: "PBKDF2",
        salt: salt,
        iterations: itrs,
        hash: hash
      };

      return helpers.subtleCrypto.deriveBits(mainAlgo, key, keyLen * 8);
    });
    promise = promise.then(function(result) {
      return util.asBuffer(result);
    });
    return promise;
  };
  var nodejs = function(key, props) {
    if (6 > helpers.nodeCrypto.pbkdf2.length) {
      throw new Error("unsupported algorithm: PBES2-" + hmac + "+" + kw);
    }

    try {
      props = prepareProps(props);
    } catch (err) {
      return Promise.reject(err);
    }

    var keyLen = props.length,
        salt = props.salt,
        itrs = props.iterations;

        var md = hash.replace("-", "");
    var promise = new Promise(function(resolve, reject) {
      function cb(err, dk) {
        if (err) {
          reject(err);
        } else {
          resolve(dk);
        }
      }
      helpers.nodeCrypto.pbkdf2(key, salt, itrs, keyLen, md, cb);
    });
    return promise;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function pbes2EncryptFN(hmac, kw) {
  var keyLen = CONSTANTS.KEYLENGTH[kw] / 8;

  var fallback = function(key, pdata, props) {
    props = props || {};

    var salt = util.asBuffer(props.p2s || new Buffer(0), "base64url"),
        itrs = props.p2c || 0;

    if (0 >= itrs) {
      throw new Error("invalid iteration count");
    }
    if (8 > salt.length) {
      throw new Error("salt too small");
    }
    salt = fixSalt(hmac, kw, salt);

    var promise;

    // STEP 1: derive shared key
    promise = new Promise(function(resolve, reject) {
      var md = forge.md[hmac.replace("HS", "SHA").toLowerCase()].create();
      var cb = function(err, dk) {
        if (err) {
          reject(err);
        } else {
          dk = new Buffer(dk, "binary");
          resolve(dk);
        }
      };

      forge.pkcs5.pbkdf2(key.toString("binary"),
                         salt.toString("binary"),
                         itrs,
                         keyLen,
                         md,
                         cb);
    });

    // STEP 2: encrypt cek
    promise = promise.then(function(dk) {
      return KW[kw].encrypt(dk, pdata);
    });
    return promise;
  };

  var webcrypto = function(key, pdata, props) {
    props = props || {};

    var salt = util.asBuffer(props.p2s || new Buffer(0), "base64url"),
        itrs = props.p2c || 0;

    if (0 >= itrs) {
      throw new Error("invalid iteration count");
    }
    if (8 > salt.length) {
      throw new Error("salt too small");
    }
    salt = fixSalt(hmac, kw, salt);

    var promise;

    // STEP 1: derive shared key
    var hash = hmac.replace("HS", "SHA-");
    promise = Promise.resolve(key);
    promise = promise.then(function(keyval) {
      return helpers.subtleCrypto.importKey("raw", keyval, "PBKDF2", false, ["deriveKey"]);
    });
    promise = promise.then(function(key) {
      var mainAlgo = {
        name: "PBKDF2",
        salt: salt,
        iterations: itrs,
        hash: hash
      };
      var deriveAlgo = {
        name: "AES-KW",
        length: keyLen * 8
      };

      return helpers.subtleCrypto.deriveKey(mainAlgo, key, deriveAlgo, true, ["wrapKey", "unwrapKey"]);
    });
    // STEP 2: encrypt cek
    promise = promise.then(function(dk) {
      // assume subtleCrypto for keywrap
      return Promise.all([
        helpers.subtleCrypto.importKey("raw", pdata, { name: "HMAC", hash: "SHA-256" }, true, ["sign"]),
        dk
      ]);
    });
    promise = promise.then(function(keys) {
      return helpers.subtleCrypto.wrapKey("raw",
                                          keys[0], // key
                                          keys[1], // wrappingKey
                                          "AES-KW");
    });
    promise = promise.then(function(result) {
      result = new Buffer(result);

      return {
        data: result
      };
    });
    return promise;
  };

  var nodejs = function(key, pdata, props) {
    if (6 > helpers.nodeCrypto.pbkdf2.length) {
      throw new Error("unsupported algorithm: PBES2-" + hmac + "+" + kw);
    }

    props = props || {};

    var salt = util.asBuffer(props.p2s || new Buffer(0), "base64url"),
        itrs = props.p2c || 0;

    if (0 >= itrs) {
      throw new Error("invalid iteration count");
    }
    if (8 > salt.length) {
      throw new Error("salt too small");
    }
    salt = fixSalt(hmac, kw, salt);

    var promise;

    // STEP 1: derive shared key
    var hash = hmac.replace("HS", "SHA");
    promise = new Promise(function(resolve, reject) {
      function cb(err, dk) {
        if (err) {
          reject(err);
        } else {
          resolve(dk);
        }
      }
      helpers.nodeCrypto.pbkdf2(key, salt, itrs, keyLen, hash, cb);
    });

    // STEP 2: encrypt cek
    promise = promise.then(function(dk) {
      return KW[kw].encrypt(dk, pdata);
    });

    return promise;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function pbes2DecryptFN(hmac, kw) {
  var keyLen = CONSTANTS.KEYLENGTH[kw] / 8;

  var fallback = function(key, cdata, props) {
    props = props || {};

    var salt = util.asBuffer(props.p2s || new Buffer(0), "base64url"),
        itrs = props.p2c || 0;

    if (0 >= itrs) {
      return Promise.reject(new Error("invalid iteration count"));
    }

    if (8 > salt.length) {
      return Promise.reject(new Error("salt too small"));
    }
    salt = fixSalt(hmac, kw, salt);

    var promise;

    // STEP 1: derived shared key
    promise = new Promise(function(resolve, reject) {
      var md = forge.md[hmac.replace("HS", "SHA").toLowerCase()].create();
      var cb = function(err, dk) {
        if (err) {
          reject(err);
        } else {
          dk = new Buffer(dk, "binary");
          resolve(dk);
        }
      };

      forge.pkcs5.pbkdf2(key.toString("binary"),
                         salt.toString("binary"),
                         itrs,
                         keyLen,
                         md,
                         cb);
    });

    // STEP 2: decrypt cek
    promise = promise.then(function(dk) {
      return KW[kw].decrypt(dk, cdata);
    });
    return promise;
  };

  var webcrypto = function(key, cdata, props) {
    props = props || {};

    var salt = util.asBuffer(props.p2s || new Buffer(0), "base64url"),
        itrs = props.p2c || 0;

    if (0 >= itrs) {
      return Promise.reject(new Error("invalid iteration count"));
    }

    if (8 > salt.length) {
      return Promise.reject(new Error("salt too small"));
    }
    salt = fixSalt(hmac, kw, salt);

    var hash = hmac.replace("HS", "SHA-");
    var promise;
    promise = Promise.resolve(key);
    promise = promise.then(function(keyval) {
      return helpers.subtleCrypto.importKey("raw", keyval, "PBKDF2", false, ["deriveKey"]);
    });
    promise = promise.then(function(key) {
      var mainAlgo = {
        name: "PBKDF2",
        salt: salt,
        iterations: itrs,
        hash: hash
      };
      var deriveAlgo = {
        name: "AES-KW",
        length: keyLen * 8
      };

      return helpers.subtleCrypto.deriveKey(mainAlgo, key, deriveAlgo, true, ["wrapKey", "unwrapKey"]);
    });
    // STEP 2: decrypt cek
    promise = promise.then(function(key) {
      return helpers.subtleCrypto.unwrapKey("raw", cdata, key, "AES-KW", {name: "HMAC", hash: "SHA-256"}, true, ["sign"]);
    });
    promise = promise.then(function(result) {
      // unwrapped CryptoKey -- extract raw
      return helpers.subtleCrypto.exportKey("raw", result);
    });
    promise = promise.then(function(result) {
      result = new Buffer(result);
      return result;
    });
    return promise;
  };

  var nodejs = function(key, cdata, props) {
    if (6 > helpers.nodeCrypto.pbkdf2.length) {
      throw new Error("unsupported algorithm: PBES2-" + hmac + "+" + kw);
    }

    props = props || {};

    var salt = util.asBuffer(props.p2s || new Buffer(0), "base64url"),
        itrs = props.p2c || 0;

    if (0 >= itrs) {
      return Promise.reject(new Error("invalid iteration count"));
    }

    if (8 > salt.length) {
      return Promise.reject(new Error("salt too small"));
    }
    salt = fixSalt(hmac, kw, salt);

    var promise;

    // STEP 1: derive shared key
    var hash = hmac.replace("HS", "SHA");
    promise = new Promise(function(resolve, reject) {
      function cb(err, dk) {
        if (err) {
          reject(err);
        } else {
          resolve(dk);
        }
      }
      helpers.nodeCrypto.pbkdf2(key, salt, itrs, keyLen, hash, cb);
    });

    // STEP 2: decrypt cek
    promise = promise.then(function(dk) {
      return KW[kw].decrypt(dk, cdata);
    });

    return promise;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

// ### Public API
var pbes2 = {};

// * [name].derive
[
  "PBKDF2-SHA-256",
  "PBKDF2-SHA-384",
  "PBKDF2-SHA-512"
].forEach(function(alg) {
  var hash = alg.replace("PBKDF2-", "");
  pbes2[alg] = {
    derive: pbkdf2Fn(hash)
  };
});

// [name].encrypt
// [name].decrypt
[
  "PBES2-HS256+A128KW",
  "PBES2-HS384+A192KW",
  "PBES2-HS512+A256KW"
].forEach(function(alg) {
  var parts = /PBES2-(HS\d+)\+(A\d+KW)/g.exec(alg);
  var hmac = parts[1],
      kw = parts[2];
  pbes2[alg] = {
    encrypt: pbes2EncryptFN(hmac, kw),
    decrypt: pbes2DecryptFN(hmac, kw)
  };
});

module.exports = pbes2;
