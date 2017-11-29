/*!
 * jwe/decrypt.js - Decrypt from a JWE
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var base64url = require("../util/base64url"),
    JWK = require("../jwk"),
    merge = require("../util/merge"),
    zlib = require("zlib");

/**
 * @class JWE.Decrypter
 * @classdesc Processor of encrypted data.
 *
 * @description
 * **NOTE:** This class cannot be instantiated directly. Instead
 * call {@link JWE.createDecrypt}.
 */
function JWEDecrypter(ks, globalOpts) {
  var assumedKey,
    keystore;

  if (JWK.isKey(ks)) {
    assumedKey = ks;
    keystore = assumedKey.keystore;
  } else if (JWK.isKeyStore(ks)) {
    keystore = ks;
  } else {
    throw new TypeError("Keystore must be provided");
  }

  globalOpts = merge({}, globalOpts);

  /**
   * Decrypts the given input.
   *
   * {opts}, if provided, is used to customize this specific decrypt operation.
   * This argument has the same semantics as {JWE.createDecrypt}, and takes
   * precedence over those options.
   *
   * The returned PRomise, when fulfilled, returns an object with the
   * following members:
   *
   * - `header` - The JOSE Header, combined from the relevant "header" and
   *            "protected" fields from the original JWE object.
   * - `protected` - An array containing the names of the protected fields
   * - `key` - The used to decrypt the content
   * - `payload` - The decrypted content (as a Buffer)
   * - `plaintext` - An alias for `payload`
   *
   * @param {Object|String} input The encrypted content
   * @param {Object} [opts] The options for this decryption operation.
   * @returns {Promise} A promise for the decyprted plaintext
   */
  Object.defineProperty(this, "decrypt", {
    value: function(input, opts) {
      opts = merge({}, globalOpts, opts || {});
      var extraHandlers = opts.handlers || {};
      var handlerKeys = Object.keys(extraHandlers);

      /* eslint camelcase: [0] */
      if (typeof input === "string") {
        input = input.split(".");
        input = {
          protected: input[0],
          recipients: [
            {
              encrypted_key: input[1]
            }
          ],
          iv: input[2],
          ciphertext: input[3],
          tag: input[4]
        };
      } else if (!input || typeof input !== "object") {
        throw new Error("invalid input");
      }
      if ("encrypted_key" in input) {
        input.recipients = [
          {
            encrypted_key: input.encrypted_key
          }
        ];
      }

      var promise;

      // ensure recipients exists
      var rcptList = input.recipients || [{}];
      promise = Promise.resolve(rcptList);

      //combine fields
      var fields,
          protect;
      promise = promise.then(function(rcptList) {
        if (input.protected) {
          protect = base64url.decode(input.protected).toString("utf8");
          protect = JSON.parse(protect);

          // verify "crit" field first
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

          fields = protect;
          protect = Object.keys(protect);
        } else {
          fields = {};
          protect = [];
        }
        fields = merge(input.unprotected || {}, fields);

        rcptList = rcptList.map(function(r) {
          var promise = Promise.resolve();
          var header = r.header || {};
          header = merge(header, fields);
          r.header = header;
          r.protected = protect;
          if (header.epk) {
            promise = promise.then(function() {
              return JWK.asKey(header.epk);
            });
            promise = promise.then(function(epk) {
              header.epk = epk.toObject(false);
            });
          }
          return promise.then(function() {
            return r;
          });
        });

        return Promise.all(rcptList);
      });

      // decrypt with first key found
      var algKey,
        encKey,
        kdata;
      promise = promise.then(function(rcptList) {
        var jwe = {};
        return new Promise(function(resolve, reject) {
          var processKey = function() {
            var rcpt = rcptList.shift();
            if (!rcpt) {
              reject(new Error("no key found"));
              return;
            }

            var algPromise = Promise.resolve(rcpt);
            algPromise = algPromise.then(function(rcpt) {
              // try to unwrap encrypted key
              var prekey = kdata = rcpt.encrypted_key || "";
              prekey = base64url.decode(prekey);
              algKey = assumedKey || keystore.get({
                use: "enc",
                alg: rcpt.header.alg,
                kid: rcpt.header.kid
              });
              if (algKey) {
                return algKey.unwrap(rcpt.header.alg, prekey, rcpt.header);
              } else {
                return Promise.reject();
              }
            });
            algPromise = algPromise.then(function(key) {
              encKey = {
                "kty": "oct",
                "k": base64url.encode(key)
              };
              encKey = JWK.asKey(encKey);
              jwe.key = algKey;
              jwe.header = rcpt.header;
              jwe.protected = rcpt.protected;
              resolve(jwe);
            });
            algPromise.catch(processKey);
          };
          processKey();
        });
      });

      // assign decipher inputs
      promise = promise.then(function(jwe) {
        jwe.iv = input.iv;
        jwe.tag = input.tag;
        jwe.ciphertext = input.ciphertext;

        return jwe;
      });

      // process any prepare-decrypt handlers
      promise = promise.then(function(jwe) {
        var processing = [];
        handlerKeys.forEach(function(h) {
          h = extraHandlers[h];
          var p;
          if ("function" === typeof h) {
            p = h(jwe);
          } else if ("object" === typeof h && "function" === typeof h.prepare) {
            p = h.prepare(jwe);
          }
          if (p) {
            processing.push(Promise.resolve(p));
          }
        });
        return Promise.all(processing).then(function() {
          // don't actually care about individual handler results
          // assume {jwe} is updated
          return jwe;
        });
      });

      // prepare decrypt inputs
      promise = promise.then(function(jwe) {
        if (!Buffer.isBuffer(jwe.ciphertext)) {
          jwe.ciphertext = base64url.decode(jwe.ciphertext);
        }

        return jwe;
      });

      // decrypt it!
      promise = promise.then(function(jwe) {
        var adata = input.protected;
        if ("aad" in input && null != input.aad) {
          adata += "." + input.aad;
        }

        var params = {
          iv: jwe.iv,
          adata: adata,
          tag: jwe.tag,
          kdata: kdata,
          epu: jwe.epu,
          epv: jwe.epv
        };
        var cdata = jwe.ciphertext;

        delete jwe.iv;
        delete jwe.tag;
        delete jwe.ciphertext;

        return encKey.
          then(function(enkKey) {
            return enkKey.decrypt(jwe.header.enc, cdata, params).
              then(function(pdata) {
                jwe.payload = jwe.plaintext = pdata;
                return jwe;
              });
          });
      });

      // (OPTIONAL) decompress plaintext
      promise = promise.then(function(jwe) {
        if ("DEF" === jwe.header.zip) {
          return new Promise(function(resolve, reject) {
            zlib.inflateRaw(new Buffer(jwe.plaintext), function(err, data) {
              if (err) {
                reject(err);
              }
              else {
                jwe.payload = jwe.plaintext = data;
                resolve(jwe);
              }
            });
          });
        }
        return jwe;
      });

      // process any post-decrypt handlers
      promise = promise.then(function(jwe) {
        var processing = [];
        handlerKeys.forEach(function(h) {
          h = extraHandlers[h];
          var p;
          if ("object" === typeof h && "function" === typeof h.complete) {
            p = h.complete(jwe);
          }
          if (p) {
            processing.push(Promise.resolve(p));
          }
        });
        return Promise.all(processing).then(function() {
          // don't actually care about individual handler results
          // assume {jwe} is updated
          return jwe;
        });
      });

      return promise;
    }
  });
}

/**
 * @description
 * Creates a new Decrypter for the given Key or KeyStore.
 *
 * {opts}, when provided, is used to customize decryption processes. The
 * following options are currently supported:
 *
 * - `handlers` - An object where each name is a JOSE header member name and
 *   the value can be a boolean, function, or an object.
 *
 * Handlers are intended to support 'crit' extensions. When a boolean value,
 * the member is expected to be processed once decryption is fully complete.
 * When a function, it is called just before the ciphertext is decrypted
 * (processed as if it were a `prepare` handler, as decribed below). When an
 * object, it can contain any of the following members:
 *
 * - `recipient` - A function called after a valid key is determined; it takes
 *   an object describing the recipient, and returns a Promise that is
 *   fulfilled once the handler's processing is complete.
 * - `prepare` - A function called just prior to decrypting the ciphertext;
 *   it takes an object describing the decryption result (but containing
 *   `ciphertext` and `tag' instead of `payload` and `plaintext`), and
 *   returns a Promise that is fulfilled once the handler's processing is
 *   complete.
 * - `complete` - A function called once decryption is complete, just prior
 *   to fulfilling the Promise returned by `decrypt()`; it takes the object
 *   that will be returned by `decrypt()`'s fulfilled Promise, and returns
 *   a Promise that is fulfilled once the handler's processing is complete.
 *
 * Note that normal processing of `decrypt()` does not continue until all
 * relevant handlers have completed. Any changes handlers make to the
 * provided objects affects `decrypt()`'s processing.
 *
 * @param {JWK.Key|JWK.KeyStore} ks The Key or KeyStore to use for decryption.
 * @param {Object} [opts] The options for this Decrypter.
 * @returns {JWE.Decrypter} The new Decrypter.
 */
function createDecrypt(ks, opts) {
  var dec = new JWEDecrypter(ks, opts);
  return dec;
}

module.exports = {
  decrypter: JWEDecrypter,
  createDecrypt: createDecrypt
};
