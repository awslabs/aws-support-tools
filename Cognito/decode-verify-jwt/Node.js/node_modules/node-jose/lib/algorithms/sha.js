/*!
 * algorithms/sha.js - Cryptographic Secure Hash Algorithms, versions 1 and 2
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js"),
    helpers = require("./helpers.js");

function hashDigestFN(hash) {
  var md = hash.replace("SHA-", "SHA").toLowerCase();

  var alg = {
    name: hash
  };

  // ### Fallback Implementation -- uses forge
  var fallback = function(pdata /* props */) {
    var digest = forge.md[md].create();
    digest.update(pdata);
    digest = digest.digest().native();

    return Promise.resolve(digest);
  };

  // ### WebCryptoAPI Implementation
  var webcrypto = function(pdata /* props */) {
    var promise;
    promise = helpers.subtleCrypto.digest(alg, pdata);
    promise = promise.then(function(result) {
      result = new Buffer(result);
      return result;
    });
    return promise;
  };

  // ### nodejs Implementation
  var nodejs = function(pdata /* props */) {
    var digest = helpers.nodeCrypto.createHash(md);
    digest.update(pdata);
    return digest.digest();
  };

  return helpers.setupFallback(nodejs, webcrypto, fallback);
}

// Public API
// * [name].digest
var sha = {};
[
  "SHA-1",
  "SHA-256",
  "SHA-384",
  "SHA-512"
].forEach(function(name) {
  sha[name] = {
    digest: hashDigestFN(name)
  };
});

module.exports = sha;
