/*!
 * jwe/encrypt.js - Encrypt to a JWE
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var assign = require("lodash.assign"),
    clone = require("lodash.clone"),
    util = require("../util"),
    generateCEK = require("./helpers").generateCEK,
    JWK = require("../jwk"),
    slice = require("./helpers").slice,
    zlib = require("zlib"),
    CONSTANTS = require("../algorithms/constants");

var DEFAULTS = require("./defaults");

/**
 * @class JWE.Encrypter
 * @classdesc
 * Generator of encrypted data.
 *
 * @description
 * **NOTE:** This class cannot be instantiated directly. Instead call {@link
 * JWE.createEncrypt}.
 */
function JWEEncrypter(cfg, fields, recipients) {
  var finalized = false,
    format = cfg.format || "general",
    protectAll = !!cfg.protectAll,
    content = new Buffer(0);

  /**
   * @member {String} JWE.Encrypter#zip
   * @readonly
   * @description
   * Indicates the compression algorithm applied to the plaintext
   * before it is encrypted.  The possible values are:
   *
   * + **`"DEF"`**: Compress the plaintext using the DEFLATE algorithm.
   * + **`""`**: Do not compress the plaintext.
   */
  Object.defineProperty(this, "zip", {
    get: function() {
      return fields.zip || "";
    },
    enumerable: true
  });
  /**
   * @member {Boolean} JWE.Encrypter#compact
   * @readonly
   * @description
   * Indicates whether the output of this encryption generator is
   * using the Compact serialization (`true`) or the JSON
   * serialization (`false`).
   */
  Object.defineProperty(this, "compact", {
    get: function() { return "compact" === format; },
    enumerable: true
  });
  /**
   * @member {String} JWE.Encrypter#format
   * @readonly
   * @description
   * Indicates the format the output of this encryption generator takes.
   */
  Object.defineProperty(this, "format", {
    get: function() { return format; },
    enumerable: true
  });
  /**
   * @member {String[]} JWE.Encrypter#protected
   * @readonly
   * @description
   * The header parameter names that are protected. Protected header fields
   * are first serialized to UTF-8 then encoded as util.base64url, then used as
   * the additional authenticated data in the encryption operation.
   */
  Object.defineProperty(this, "protected", {
    get: function() {
      return clone(cfg.protect);
    },
    enumerable: true
  });
  /**
   * @member {Object} JWE.Encrypter#header
   * @readonly
   * @description
   * The global header parameters, both protected and unprotected. Call
   * {@link JWE.Encrypter#protected} to determine which parameters will
   * be protected.
   */
  Object.defineProperty(this, "header", {
    get: function() {
      return clone(fields);
    },
    enumerable: true
  });

  /**
   * @method JWE.Encrypter#update
   * @description
   * Updates the plaintext data for the encryption generator. The plaintext
   * is appended to the end of any other plaintext already applied.
   *
   * If {data} is a Buffer, {encoding} is ignored. Otherwise, {data} is
   * converted to a Buffer internally to {encoding}.
   *
   * @param {Buffer|String} [data] The plaintext to apply.
   * @param {String} [encoding] The encoding of the plaintext.
   * @returns {JWE.Encrypter} This encryption generator.
   * @throws {Error} If ciphertext has already been generated.
   */
  Object.defineProperty(this, "update", {
    value: function(data, encoding) {
      if (finalized) {
        throw new Error("already final");
      }
      if (data != null) {
        data = util.asBuffer(data, encoding);
        if (content.length) {
          content = Buffer.concat([content, data],
                      content.length + data.length);
        } else {
          content = data;
        }
      }

      return this;
    }
  });
  /**
   * @method JWE.Encrypter#final
   * @description
   * Finishes the encryption operation.
   *
   * The returned Promise, when fulfilled, is the JSON Web Encryption (JWE)
   * object, either in the Compact (if {@link JWE.Encrypter#compact} is
   * `true`) or the JSON serialization.
   *
   * @param {Buffer|String} [data] The final plaintext data to apply.
   * @param {String} [encoding] The encoding of the final plaintext data
   *        (if any).
   * @returns {Promise} A promise for the encryption operation.
   * @throws {Error} If ciphertext has already been generated.
   */
  Object.defineProperty(this, "final", {
    value: function(data, encoding) {
      if (finalized) {
        return Promise.reject(new Error("already final"));
      }

      // last-minute data
      this.update(data, encoding);

      // mark as done...ish
      finalized = true;
      var promise = Promise.resolve({});

      // determine CEK and IV
      var encAlg = fields.enc;
      var encKey;
      promise = promise.then(function(jwe) {
        if (cfg.cek) {
          encKey = JWK.asKey(cfg.cek);
        }
        return jwe;
      });

      // process recipients
      promise = promise.then(function(jwe) {
        var procR = function(r, one) {
          var props = {};
          props = assign(props, fields);
          props = assign(props, r.header);

          var algKey = r.key,
              algAlg = props.alg;

          // generate Ephemeral EC Key
          var tks,
              rpromise;
          if (props.alg.indexOf("ECDH-ES") === 0) {
            tks = algKey.keystore.temp();
            if (r.epk) {
              rpromise = Promise.resolve(r.epk).
                then(function(epk) {
                  r.header.epk = epk.toJSON(false, ["kid"]);
                  props.epk = epk.toObject(true, ["kid"]);
                });
            } else {
              rpromise = tks.generate("EC", algKey.get("crv")).
                then(function(epk) {
                  r.header.epk = epk.toJSON(false, ["kid"]);
                  props.epk = epk.toObject(true, ["kid"]);
                });
            }
          } else {
            rpromise = Promise.resolve();
          }

          // encrypt the CEK
          rpromise = rpromise.then(function() {
            var cek,
                p;
            // special case 'alg=dir'
            if ("dir" === algAlg && one) {
              encKey = Promise.resolve(algKey);
              p = encKey.then(function(jwk) {
                // fixup encAlg
                if (!encAlg) {
                  props.enc = fields.enc = encAlg = jwk.algorithms(JWK.MODE_ENCRYPT)[0];
                }
                return {
                  once: true,
                  direct: true
                };
              });
            } else {
              if (!encKey) {
                if (!encAlg) {
                  props.enc = fields.enc = encAlg = cfg.contentAlg;
                }
                encKey = generateCEK(encAlg);
              }
              p = encKey.then(function(jwk) {
                cek = jwk.get("k", true);
                // algKey may or may not be a promise
                return algKey;
              });
              p = p.then(function(algKey) {
                return algKey.wrap(algAlg, cek, props);
              });
            }
            return p;
          });
          rpromise = rpromise.then(function(wrapped) {
            if (wrapped.once && !one) {
              return Promise.reject(new Error("cannot use 'alg':'" + algAlg + "' with multiple recipients"));
            }

            var rjwe = {},
                cek;
            if (wrapped.data) {
              cek = wrapped.data;
              cek = util.base64url.encode(cek);
            }

            if (wrapped.direct && cek) {
              // replace content key
              encKey = JWK.asKey({
                kty: "oct",
                k: cek
              });
            } else if (cek) {
              /* eslint camelcase: [0] */
              rjwe.encrypted_key = cek;
            }

            if (r.header && Object.keys(r.header).length) {
              rjwe.header = clone(r.header || {});
            }
            if (wrapped.header) {
              rjwe.header = assign(rjwe.header || {},
                                     wrapped.header);
            }

            return rjwe;
           });
           return rpromise;
        };

        var p = Promise.all(recipients);
        p = p.then(function(rcpts) {
          var single = (1 === rcpts.length);
          rcpts = rcpts.map(function(r) {
            return procR(r, single);
          });
          return Promise.all(rcpts);
        });
        p = p.then(function(rcpts) {
          jwe.recipients = rcpts.filter(function(r) { return !!r; });
          return jwe;
        });
        return p;
      });

      // normalize headers
      var props = {};
      promise = promise.then(function(jwe) {
        var protect,
          lenProtect,
          unprotect,
          lenUnprotect;

        unprotect = clone(fields);
        if ((protectAll && jwe.recipients.length === 1) || "compact" === format) {
          // merge single recipient into fields
          protect = assign(jwe.recipients[0].header || {},
                     unprotect);
          lenProtect = Object.keys(protect).length;

          unprotect = undefined;
          lenUnprotect = 0;

          delete jwe.recipients[0].header;
          if (Object.keys(jwe.recipients[0]).length === 0) {
            jwe.recipients.splice(0, 1);
          }
        } else {
          protect = {};
          lenProtect = 0;
          lenUnprotect = Object.keys(unprotect).length;
          cfg.protect.forEach(function(f) {
            if (!(f in unprotect)) {
              return;
            }
            protect[f] = unprotect[f];
            lenProtect++;

            delete unprotect[f];
            lenUnprotect--;
          });
        }

        if (!jwe.recipients || jwe.recipients.length === 0) {
          delete jwe.recipients;
        }

        // "serialize" (and setup merged props)
        if (unprotect && lenUnprotect > 0) {
          props = assign(props, unprotect);
          jwe.unprotected = unprotect;
        }
        if (protect && lenProtect > 0) {
          props = assign(props, protect);
          protect = JSON.stringify(protect);
          jwe.protected = util.base64url.encode(protect, "utf8");
        }

        return jwe;
      });

      // (OPTIONAL) compress plaintext
      promise = promise.then(function(jwe) {
        var pdata = content;
        if (!props.zip) {
          jwe.plaintext = pdata;
          return jwe;
        } else if (props.zip === "DEF") {
          return new Promise(function(resolve, reject) {
            zlib.deflateRaw(new Buffer(pdata, "binary"), function(err, data) {
              if (err) {
                reject(err);
              }
              else {
                jwe.plaintext = data;
                resolve(jwe);
              }
            });
          });
        }
        return Promise.reject(new Error("unsupported 'zip' mode"));
      });

      // encrypt plaintext
      promise = promise.then(function(jwe) {
        props.adata = jwe.protected;
        if ("aad" in cfg && cfg.aad != null) {
          props.adata += "." + cfg.aad;
          props.adata = new Buffer(props.adata, "utf8");
        }
        // calculate IV
        var iv = cfg.iv ||
                 util.randomBytes(CONSTANTS.NONCELENGTH[encAlg] / 8);
        if ("string" === typeof iv) {
          iv = util.base64url.decode(iv);
        }
        props.iv = iv;

        if ("recipients" in jwe && jwe.recipients.length === 1) {
          props.kdata = jwe.recipients[0].encrypted_key;
        }

        if ("epu" in cfg && cfg.epu != null) {
          props.epu = cfg.epu;
        }

        if ("epv" in cfg && cfg.epv != null) {
          props.epv = cfg.epv;
        }

        var pdata = jwe.plaintext;
        delete jwe.plaintext;
        return encKey.then(function(encKey) {
          var p = encKey.encrypt(encAlg, pdata, props);
          p = p.then(function(result) {
            jwe.iv = util.base64url.encode(iv, "binary");
            if ("aad" in cfg && cfg.aad != null) {
             jwe.aad = cfg.aad;
            }
            jwe.ciphertext = util.base64url.encode(result.data, "binary");
            jwe.tag = util.base64url.encode(result.tag, "binary");
            return jwe;
          });
          return p;
        });
      });

      // (OPTIONAL) compact/flattened results
      switch (format) {
        case "compact":
          promise = promise.then(function(jwe) {
            var compact = new Array(5);

            compact[0] = jwe.protected;
            if (jwe.recipients && jwe.recipients[0]) {
              compact[1] = jwe.recipients[0].encrypted_key;
            }

            compact[2] = jwe.iv;
            compact[3] = jwe.ciphertext;
            compact[4] = jwe.tag;
            compact = compact.join(".");

            return compact;
          });
          break;
        case "flattened":
          promise = promise.then(function(jwe) {
            var flattened = {},
                rcpt = jwe.recipients && jwe.recipients[0];

            if (jwe.protected) {
              flattened.protected = jwe.protected;
            }
            if (jwe.unprotected) {
              flattened.unprotected = jwe.unprotected;
            }
            ["header", "encrypted_key"].forEach(function(f) {
              if (!rcpt) { return; }
              if (!(f in rcpt)) { return; }
              flattened[f] = rcpt[f];
            });
            if (jwe.aad) {
              flattened.aad = jwe.aad;
            }
            flattened.iv = jwe.iv;
            flattened.ciphertext = jwe.ciphertext;
            flattened.tag = jwe.tag;

            return flattened;
          });
          break;
      }

      return promise;
    }
  });
}

function createEncrypt(opts, rcpts) {
  // fixup recipients
  var options = opts,
    rcptStart = 1,
    rcptList = rcpts;

  if (arguments.length === 0) {
    throw new Error("at least one recipient must be provided");
  }
  if (arguments.length === 1) {
    // assume opts is the recipient list
    rcptList = opts;
    rcptStart = 0;
    options = {};
  } else if (JWK.isKey(opts) ||
        (opts && "kty" in opts) ||
        (opts && "key" in opts &&
        (JWK.isKey(opts.key) || "kty" in opts.key))) {
    rcptList = opts;
    rcptStart = 0;
    options = {};
  } else {
    options = clone(opts);
  }
  if (!Array.isArray(rcptList)) {
    rcptList = slice(arguments, rcptStart);
  }

  // fixup options
  options = assign(clone(DEFAULTS), options);

  // setup header fields
  var fields = clone(options.fields || {});
  if (options.zip) {
    fields.zip = (typeof options.zip === "boolean") ?
           (options.zip ? "DEF" : false) :
           options.zip;
  }
  options.format = (options.compact ? "compact" : options.format) || "general";
  switch (options.format) {
    case "compact":
      if ("aad" in opts) {
        throw new Error("additional authenticated data cannot be used for compact serialization");
      }
      /* eslint no-fallthrough: [0] */
    case "flattened":
      if (rcptList.length > 1) {
        throw new Error("too many recipients for compact serialization");
      }
      break;
  }

  // note protected fields (globally)
  // protected fields are global only
  var protectAll = false;
  if ("compact" === options.format || "*" === options.protect) {
    protectAll = true;
    options.protect = Object.keys(fields).concat("enc");
  } else if (typeof options.protect === "string") {
    options.protect = [options.protect];
  } else if (Array.isArray(options.protect)) {
    options.protect = options.protect.concat();
  } else if (!options.protect) {
    options.protect = [];
  } else {
    throw new Error("protect must be a list of fields");
  }

  if (protectAll && 1 < rcptList.length) {
    throw new Error("too many recipients to protect all header parameters");
  }

  rcptList = rcptList.map(function(r, idx) {
    var p;

    // resolve a key
    if (r && "kty" in r) {
      p = JWK.asKey(r);
      p = p.then(function(k) {
        return {
          key: k
        };
      });
    } else if (r) {
      p = JWK.asKey(r.key);
      p = p.then(function(k) {
        return {
          header: r.header,
          reference: r.reference,
          key: k
        };
      });
    } else {
      p = Promise.reject(new Error("missing key for recipient " + idx));
    }

    // convert ephemeral key (if present)
    if (r.epk) {
      p = p.then(function(recipient) {
        return JWK.asKey(r.epk).
          then(function(epk) {
            recipient.epk = epk;
            return recipient;
          });
      });
    }

    // resolve the complete recipient
    p = p.then(function(recipient) {
      var key = recipient.key;

      // prepare the recipient header
      var header = recipient.header || {};
      recipient.header = header;
      var props = {};
      props = assign(props, fields);
      props = assign(props, recipient.header);

      // ensure key protection algorithm is set
      if (!props.alg) {
        props.alg = key.algorithms(JWK.MODE_WRAP)[0];
      }
      header.alg = props.alg;

      // determine the key reference
      var ref = recipient.reference;
      delete recipient.reference;
      if (undefined === ref) {
        // header already contains the key reference
        ref = ["kid", "jku", "x5c", "x5t", "x5u"].some(function(k) {
          return (k in header);
        });
        ref = !ref ? "kid" : null;
      } else if ("boolean" === typeof ref) {
        // explicit (positive | negative) request for key reference
        ref = ref ? "kid" : null;
      }
      var jwk;
      if (ref) {
        jwk = key.toJSON();
        if ("jwk" === ref) {
          if ("oct" === key.kty) {
            return Promise.reject(new Error("cannot embed key"));
          }
          header.jwk = jwk;
        } else if (ref in jwk) {
          header[ref] = jwk[ref];
        }
      }

      // freeze recipient
      recipient = Object.freeze(recipient);
      return recipient;
    });

    return p;
  });

  // create and configure encryption
  var cfg = {
    aad: ("aad" in options) ? util.base64url.encode(options.aad || "") : null,
    contentAlg: options.contentAlg,
    format: options.format,
    protect: options.protect,
    cek: options.cek,
    iv: options.iv,
    protectAll: protectAll
  };
  var enc = new JWEEncrypter(cfg, fields, rcptList);

  return enc;
}

module.exports = {
  encrypter: JWEEncrypter,
  createEncrypt: createEncrypt
};
