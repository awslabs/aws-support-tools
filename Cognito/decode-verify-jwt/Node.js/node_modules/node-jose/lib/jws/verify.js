/*!
 * jws/verify.js - Verifies from a JWS
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var clone = require("lodash.clone"),
    merge = require("../util/merge"),
    base64url = require("../util/base64url"),
    JWK = require("../jwk");

/**
 * @class JWS.Verifier
 * @classdesc Parser of signed content.
 *
 * @description
 * **NOTE:** this class cannot be instantiated directly. Instead call {@link
 * JWS.createVerify}.
 */
var JWSVerifier = function(ks, globalOpts) {
  var assumedKey,
      keystore;

  if (JWK.isKey(ks)) {
    assumedKey = ks;
    keystore = assumedKey.keystore;
  } else if (JWK.isKeyStore(ks)) {
    keystore = ks;
  } else {
    keystore = JWK.createKeyStore();
  }

  globalOpts = merge({}, globalOpts);

  Object.defineProperty(this, "defaultKey", {
    value: assumedKey || undefined,
    enumerable: true
  });
  Object.defineProperty(this, "keystore", {
    value: keystore,
    enumerable: true
  });

  Object.defineProperty(this, "verify", {
    value: function(input, opts) {
      opts = merge({}, globalOpts, opts || {});
      var extraHandlers = opts.handlers || {};
      var handlerKeys = Object.keys(extraHandlers);

      if ("string" === typeof input) {
        input = input.split(".");
        input = {
          payload: input[1],
          signatures: [
            {
              protected: input[0],
              signature: input[2]
            }
          ]
        };
      } else if (!input || "object" === input) {
        throw new Error("invalid input");
      }

      // fixup "flattened JSON" to look like "general JSON"
      if (input.signature) {
        input.signatures = [
          {
            protected: input.protected || undefined,
            header: input.header || undefined,
            signature: input.signature
          }
        ];
      }

      // ensure signatories exists
      var sigList = input.signatures || [{}];

      // combine fields and decode signature per signatory
      sigList = sigList.map(function(s) {
        var header = clone(s.header || {});
        var protect = s.protected ?
                      JSON.parse(base64url.decode(s.protected, "utf8")) :
                      {};
        header = merge(header, protect);
        var signature = base64url.decode(s.signature);

        // process "crit" first
        var crit = protect.crit;
        if (crit) {
          if (!Array.isArray(crit)) {
            return Promise.reject(new Error("Invalid 'crit' header"));
          }
          for (var idx = 0; crit.length > idx; idx++) {
            if (-1 === handlerKeys.indexOf(crit[idx])) {
              return Promise.reject(new Error(
                  "Critical extension is not supported: " + crit[idx]
              ));
            }
          }
        }
        protect = Object.keys(protect);

        return Promise.resolve({
          protected: protect,
          aad: s.protected || "",
          header: header,
          signature: signature
        });
      });

      var promise = Promise.all(sigList);
      promise = promise.then(function(sigList) {
        return new Promise(function(resolve, reject) {
          var processSig = function() {
            var sig = sigList.shift();
            if (!sig) {
              reject(new Error("no key found"));
              return;
            }

            sig = merge({}, sig, {
              payload: input.payload
            });
            var p = Promise.resolve(sig);
            // find the key
            p = p.then(function(sig) {
              var algKey;
              // TODO: resolve jku, x5c, x5u
              if (sig.header.jwk) {
                algKey = JWK.asKey(sig.header.jwk);
              } else if (sig.header.x5c) {
                algKey = sig.header.x5c[0];
                algKey = new Buffer(algKey, "base64");
                // TODO: callback to validate chain
                algKey = JWK.asKey(algKey, "pkix");
              } else {
                algKey = Promise.resolve(assumedKey || keystore.get({
                  use: "sig",
                  alg: sig.header.alg,
                  kid: sig.header.kid
                }));
              }
              return algKey.then(function(k) {
                if (!k) {
                  return Promise.reject(new Error("key does not match"));
                }
                sig.key = k;
                return sig;
              });
            });

            // process any prepare-verify handlers
            p = p.then(function(sig) {
              var processing = [];
              handlerKeys.forEach(function(h) {
                h = extraHandlers[h];
                var p;
                if ("function" === typeof h) {
                  p = h(sig);
                } else if ("object" === typeof h && "function" === typeof h.prepare) {
                  p = h.prepare(sig);
                }
                if (p) {
                  processing.push(Promise.resolve(p));
                }
              });
              return Promise.all(processing).then(function() {
                // don't actually care about individual handler results
                // assume {sig} is updated
                return sig;
              });
            });

            // prepare verify inputs
            p = p.then(function(sig) {
              var aad = sig.aad || "",
                  payload = sig.payload || "";
              var content = new Buffer(1 + aad.length + payload.length),
                  pos = 0;
              content.write(aad, pos, "ascii");
              pos += aad.length;
              content.write(".", pos, "ascii");
              pos++;

              if (Buffer.isBuffer(payload)) {
                payload.copy(content, pos);
              } else {
                content.write(payload, pos, "binary");
              }
              sig.content = content;
              return sig;
            });

            p = p.then(function(sig) {
              return sig.key.verify(sig.header.alg,
                                    sig.content,
                                    sig.signature);
            });

            p = p.then(function(result) {
              var payload = sig.payload;
              payload = base64url.decode(payload);
              return {
                protected: sig.protected,
                header: sig.header,
                payload: payload,
                signature: result.mac,
                key: sig.key
              };
            });

            // process any post-verify handlers
            p = p.then(function(jws) {
              var processing = [];
              handlerKeys.forEach(function(h) {
                h = extraHandlers[h];
                var p;
                if ("object" === typeof h && "function" === typeof h.complete) {
                  p = h.complete(jws);
                }
                if (p) {
                  processing.push(Promise.resolve(p));
                }
              });
              return Promise.all(processing).then(function() {
                // don't actually care about individual handler results
                // assume {jws} is updated
                return jws;
              });
            });
            p.then(resolve, processSig);
          };
          processSig();
        });
      });
      return promise;
    }
  });
};

/**
 * @description
 * Creates a new JWS.Verifier with the given Key or KeyStore.
 *
 * @param {JWK.Key|JWK.KeyStore} ks The Key or KeyStore to use for verification.
 * @returns {JWS.Verifier} The new Verifier.
 */
function createVerify(ks) {
  var vfy = new JWSVerifier(ks);

  return vfy;
}

module.exports = {
  verifier: JWSVerifier,
  createVerify: createVerify
};
