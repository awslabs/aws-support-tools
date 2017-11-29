/*!
 * algorithms/aes-cbc-hmac-sha2.js - AES-CBC-HMAC-SHA2 Composited Encryption
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var helpers = require("./helpers.js"),
    HMAC = require("./hmac.js"),
    sha = require("./sha.js"),
    forge = require("../deps/forge.js"),
    DataBuffer = require("../util/databuffer.js"),
    util = require("../util");

function checkIv(iv) {
  if (16 !== iv.length) {
    throw new Error("invalid iv");
  }
}

function commonCbcEncryptFN(size) {
  // ### 'fallback' implementation -- uses forge
  var fallback = function(encKey, pdata, iv) {
    try {
      checkIv(iv);
    } catch (err) {
      return Promise.reject(err);
    }

    var promise = Promise.resolve();

    promise = promise.then(function() {
      var cipher = forge.cipher.createCipher("AES-CBC", new DataBuffer(encKey));
      cipher.start({
        iv: new DataBuffer(iv)
      });

      // TODO: chunk data
      cipher.update(new DataBuffer(pdata));
      if (!cipher.finish()) {
        return Promise.reject(new Error("encryption failed"));
      }

      var cdata = cipher.output.native();
      return cdata;
    });

    return promise;
  };

  // ### WebCryptoAPI implementation
  // TODO: cache CryptoKey sooner
  var webcrypto = function(encKey, pdata, iv) {
    try {
      checkIv(iv);
    } catch (err) {
      return Promise.reject(err);
    }

    var promise = Promise.resolve();

    promise = promise.then(function() {
      var alg = {
        name: "AES-CBC"
      };
      return helpers.subtleCrypto.importKey("raw", encKey, alg, true, ["encrypt"]);
    });
    promise = promise.then(function(key) {
      var alg = {
        name: "AES-CBC",
        iv: iv
      };
      return helpers.subtleCrypto.encrypt(alg, key, pdata);
    });
    promise = promise.then(function(cdata) {
      cdata = new Buffer(cdata);
      return cdata;
    });

    return promise;
  };

  // ### NodeJS implementation
  var nodejs = function(encKey, pdata, iv) {
    try {
      checkIv(iv);
    } catch (err) {
      return Promise.reject(err);
    }

    var promise = Promise.resolve(pdata);

    promise = promise.then(function(pdata) {
      var name = "AES-" + size + "-CBC";
      var cipher = helpers.nodeCrypto.createCipheriv(name, encKey, iv);
      var cdata = Buffer.concat([
        cipher.update(pdata),
        cipher.final()
      ]);
      return cdata;
    });

    return promise;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function commonCbcDecryptFN(size) {
  // ### 'fallback' implementation -- uses forge
  var fallback = function(encKey, cdata, iv) {
    // validate inputs
    try {
      checkIv(iv);
    } catch (err) {
      return Promise.reject(err);
    }

    var promise = Promise.resolve();

    promise = promise.then(function() {
      var cipher = forge.cipher.createDecipher("AES-CBC", new DataBuffer(encKey));
      cipher.start({
        iv: new DataBuffer(iv)
      });

      // TODO: chunk data
      cipher.update(new DataBuffer(cdata));
      if (!cipher.finish()) {
        return Promise.reject(new Error("encryption failed"));
      }

      var pdata = cipher.output.native();
      return pdata;
    });

    return promise;
  };

  // ### WebCryptoAPI implementation
  // TODO: cache CryptoKey sooner
  var webcrypto = function(encKey, cdata, iv) {
    // validate inputs
    try {
      checkIv(iv);
    } catch (err) {
      return Promise.reject(err);
    }

    var promise = Promise.resolve();

    promise = promise.then(function() {
      var alg = {
        name: "AES-CBC"
      };
      return helpers.subtleCrypto.importKey("raw", encKey, alg, true, ["decrypt"]);
    });
    promise = promise.then(function(key) {
      var alg = {
        name: "AES-CBC",
        iv: iv
      };
      return helpers.subtleCrypto.decrypt(alg, key, cdata);
    });
    promise = promise.then(function(pdata) {
      pdata = new Buffer(pdata);
      return pdata;
    });

    return promise;
  };

  // ### NodeJS implementation
  var nodejs = function(encKey, cdata, iv) {
    // validate inputs
    try {
      checkIv(iv);
    } catch (err) {
      return Promise.reject(err);
    }

    var promise = Promise.resolve();

    promise = promise.then(function() {
      var name = "AES-" + size + "-CBC";
      var cipher = helpers.nodeCrypto.createDecipheriv(name, encKey, iv);
      var pdata = Buffer.concat([
        cipher.update(cdata),
        cipher.final()
      ]);
      return pdata;
    });

    return promise;
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

function checkKey(key, size) {
  if ((size << 1) !== (key.length << 3)) {
    throw new Error("invalid encryption key size");
  }
}

function cbcHmacEncryptFN(size) {
  var commonEncrypt = commonCbcEncryptFN(size);
  return function(key, pdata, props) {
    // validate inputs
    try {
      checkKey(key, size);
    } catch (err) {
      return Promise.reject(err);
    }

    var eKey = key.slice(size / 8),
        iKey = key.slice(0, size / 8),
        iv = props.iv || new Buffer(0),
        adata = props.aad || props.adata || new Buffer(0);

    // STEP 1 -- Encrypt
    var promise = commonEncrypt(eKey, pdata, iv);

    // STEP 2 -- MAC
    promise = promise.then(function(cdata){
      var mdata = Buffer.concat([
        adata,
        iv,
        cdata,
        helpers.int64ToBuffer(adata.length * 8)
      ]);

      var promise;
      promise = HMAC["HS" + (size * 2)].sign(iKey, mdata, {
        length: size
      });
      promise = promise.then(function(result) {
        // TODO: move slice to hmac.js
        var tag = result.mac.slice(0, size / 8);
        return {
          data: cdata,
          tag: tag
        };
      });
      return promise;
    });

    return promise;
  };
}

function cbcHmacDecryptFN(size) {
  var commonDecrypt = commonCbcDecryptFN(size);

  return function(key, cdata, props) {
    // validate inputs
    try {
      checkKey(key, size);
    } catch (err) {
      return Promise.reject(err);
    }

    var eKey = key.slice(size / 8),
        iKey = key.slice(0, size / 8),
        iv = props.iv || new Buffer(0),
        adata = props.aad || props.adata || new Buffer(0),
        tag = props.tag || props.mac || new Buffer(0);

    var promise = Promise.resolve();

    // STEP 1 -- MAC
    promise = promise.then(function() {
      var promise;
      // construct MAC input
      var mdata = Buffer.concat([
        adata,
        iv,
        cdata,
        helpers.int64ToBuffer(adata.length * 8)
      ]);
      promise = HMAC["HS" + (size * 2)].verify(iKey, mdata, tag, {
        length: size
      });
      promise = promise.then(function() {
        return cdata;
      }, function() {
        // failure -- invalid tag error
        throw new Error("mac check failed");
      });
      return promise;
    });

    // STEP 2 -- Decrypt
    promise = promise.then(function(){
      return commonDecrypt(eKey, cdata, iv);
    });

    return promise;
  };
}

var EncryptionLabel = new Buffer("Encryption", "utf8");
var IntegrityLabel = new Buffer("Integrity", "utf8");
var DotLabel = new Buffer(".", "utf8");

function generateCek(masterKey, alg, epu, epv) {
  var masterSize = masterKey.length * 8;
  var cekSize = masterSize / 2;
  var promise = Promise.resolve();

  promise = promise.then(function(){
    var input = Buffer.concat([
      helpers.int32ToBuffer(1),
      masterKey,
      helpers.int32ToBuffer(cekSize),
      new Buffer(alg, "utf8"),
      epu,
      epv,
      EncryptionLabel
    ]);

    return input;
  });

  promise = promise.then( function(input) {
    return sha["SHA-" + masterSize].digest(input).then(function(digest) {
      return digest.slice(0, cekSize / 8);
    });
  });
  promise = Promise.resolve(promise);

  return promise;
}

function generateCik(masterKey, alg, epu, epv) {
  var masterSize = masterKey.length * 8;
  var cikSize = masterSize;
  var promise = Promise.resolve();

  promise = promise.then(function(){
    var input = Buffer.concat([
      helpers.int32ToBuffer(1),
      masterKey,
      helpers.int32ToBuffer(cikSize),
      new Buffer(alg, "utf8"),
      epu,
      epv,
      IntegrityLabel
    ]);

    return input;
  });

  promise = promise.then( function(input) {
    return sha["SHA-" + masterSize].digest(input).then(function(digest) {
      return digest.slice(0, cikSize / 8);
    });
  });
  promise = Promise.resolve(promise);

  return promise;
}

function concatKdfCbcHmacEncryptFN(size, alg) {
  var commonEncrypt = commonCbcEncryptFN(size);

  return function(key, pdata, props) {
    var epu = props.epu || helpers.int32ToBuffer(0),
        epv = props.epv || helpers.int32ToBuffer(0),
        iv = props.iv || new Buffer(0),
        adata = props.aad || props.adata || new Buffer(0),
        kdata = props.kdata || new Buffer(0);

    // Pre Step 1 -- Generate Keys
    var promises = [
      generateCek(key, alg, epu, epv),
      generateCik(key, alg, epu, epv)
    ];

    var cek,
        cik;
    var promise = Promise.all(promises).then(function(keys) {
      cek = keys[0];
      cik = keys[1];
    });

    // STEP 1 -- Encrypt
    promise = promise.then(function(){
      return commonEncrypt(cek, pdata, iv);
    });

    // STEP 2 -- Mac
    promise = promise.then(function(cdata){
      var mdata = Buffer.concat([
        adata,
        DotLabel,
        new Buffer(kdata),
        DotLabel,
        new Buffer(util.base64url.encode(iv), "utf8"),
        DotLabel,
        new Buffer(util.base64url.encode(cdata), "utf8")
      ]);
      return Promise.all([
        Promise.resolve(cdata),
        HMAC["HS" + (size * 2)].sign(cik, mdata, { length: size })
      ]);
    });
    promise = promise.then(function(result){
      return {
        data: result[0],
        tag: result[1].mac
      };
    });

    return promise;
  };
}

function concatKdfCbcHmacDecryptFN(size, alg) {
  var commonDecrypt = commonCbcDecryptFN(size);

  return function(key, cdata, props) {
    var epu = props.epu || helpers.int32ToBuffer(0),
        epv = props.epv || helpers.int32ToBuffer(0),
        iv = props.iv || new Buffer(0),
        adata = props.aad || props.adata || new Buffer(0),
        kdata = props.kdata || new Buffer(0),
        tag = props.tag || props.mac || new Buffer(0);

    // Pre Step 1 -- Generate Keys
    var promises = [
      generateCek(key, alg, epu, epv),
      generateCik(key, alg, epu, epv)
    ];

    var cek,
        cik;
    var promise = Promise.all(promises).then(function(keys){
      cek = keys[0];
      cik = keys[1];
    });


    // STEP 1 -- MAC
    promise = promise.then(function() {
      // construct MAC input
      var mdata = Buffer.concat([
        adata,
        DotLabel,
        new Buffer(kdata),
        DotLabel,
        new Buffer(util.base64url.encode(iv), "utf8"),
        DotLabel,
        new Buffer(util.base64url.encode(cdata), "utf8")
      ]);

      try {
        return HMAC["HS" + (size * 2)].verify(cik, mdata, tag, {
          loose: false
        });
      } catch (e) {
        throw new Error("mac check failed");
      }
    });

    // STEP 2 -- Decrypt
    promise = promise.then(function(){
      return commonDecrypt(cek, cdata, iv);
    });

    return promise;
  };
}

// ### Public API
// * [name].encrypt
// * [name].decrypt
var aesCbcHmacSha2 = {};
[
  "A128CBC-HS256",
  "A192CBC-HS384",
  "A256CBC-HS512"
].forEach(function(alg) {
  var size = parseInt(/A(\d+)CBC-HS(\d+)?/g.exec(alg)[1]);
  aesCbcHmacSha2[alg] = {
    encrypt: cbcHmacEncryptFN(size),
    decrypt: cbcHmacDecryptFN(size)
  };
});

[
  "A128CBC+HS256",
  "A192CBC+HS384",
  "A256CBC+HS512"
].forEach(function(alg) {
  var size = parseInt(/A(\d+)CBC\+HS(\d+)?/g.exec(alg)[1]);
  aesCbcHmacSha2[alg] = {
    encrypt: concatKdfCbcHmacEncryptFN(size, alg),
    decrypt: concatKdfCbcHmacDecryptFN(size, alg)
  };
});

module.exports = aesCbcHmacSha2;
