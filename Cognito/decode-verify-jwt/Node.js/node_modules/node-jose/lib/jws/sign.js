/*!
 * jws/sign.js - Sign to JWS
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var clone = require("lodash.clone"),
    merge = require("../util/merge"),
    uniq = require("lodash.uniq"),
    util = require("../util"),
    JWK = require("../jwk"),
    slice = require("./helpers").slice;

var DEFAULTS = require("./defaults");

/**
 * @class JWS.Signer
 * @classdesc Generator of signed content.
 *
 * @description
 * **NOTE:** this class cannot be instantiated directly. Instead call {@link
 * JWS.createSign}.
 */
var JWSSigner = function(cfg, signatories) {
  var finalized = false,
      format = cfg.format || "general",
      content = new Buffer(0);

  /**
  * @member {Boolean} JWS.Signer#compact
  * @description
  * Indicates whether the outuput of this signature generator is using
  * the Compact serialization (`true`) or the JSON serialization
  * (`false`).
  */
  Object.defineProperty(this, "compact", {
    get: function() {
      return "compact" === format;
    },
    enumerable: true
  });
  Object.defineProperty(this, "format", {
    get: function() {
      return format;
    },
    enumerable: true
  });

  /**
  * @method JWS.Signer#update
  * @description
  * Updates the signing content for this signature content. The content
  * is appended to the end of any other content already applied.
  *
  * If {data} is a Buffer, {encoding} is ignored. Otherwise, {data} is
  * converted to a Buffer internally to {encoding}.
  *
  * @param {Buffer|String} data The data to sign.
  * @param {String} [encoding="binary"] The encoding of {data}.
  * @returns {JWS.Signer} This signature generator.
  * @throws {Error} If a signature has already been generated.
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
  * @method JWS.Signer#final
  * @description
  * Finishes the signature operation.
  *
  * The returned Promise, when fulfilled, is the JSON Web Signature (JWS)
  * object, either in the Compact (if {@link JWS.Signer#format} is
  * `"compact"`), the flattened JSON (if {@link JWS.Signer#format} is
  * "flattened"), or the general JSON serialization.
  *
  * @param {Buffer|String} [data] The final content to apply.
  * @param {String} [encoding="binary"] The encoding of the final content
  *        (if any).
  * @returns {Promise} The promise for the signatures
  * @throws {Error} If a signature has already been generated.
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
      var promise;

      // map signatory promises to just signatories
      promise = Promise.all(signatories);
      promise = promise.then(function(sigs) {
        // prepare content
        content = util.base64url.encode(content);

        sigs = sigs.map(function(s) {
          // prepare protected
          var protect = {},
              lenProtect = 0,
              unprotect = clone(s.header),
              lenUnprotect = Object.keys(unprotect).length;
          s.protected.forEach(function(h) {
            if (!(h in unprotect)) {
              return;
            }
            protect[h] = unprotect[h];
            lenProtect++;
            delete unprotect[h];
            lenUnprotect--;
          });
          if (lenProtect > 0) {
            protect = JSON.stringify(protect);
            protect = util.base64url.encode(protect);
          } else {
            protect = "";
          }

          // signit!
          var data = new Buffer(protect + "." + content, "ascii");
          s = s.key.sign(s.header.alg, data, s.header);
          s = s.then(function(result) {
            var sig = {};
            if (0 < lenProtect) {
              sig.protected = protect;
            }
            if (0 < lenUnprotect) {
              sig.header = unprotect;
            }
            sig.signature = util.base64url.encode(result.mac);
            return sig;
          });
          return s;
        });
        sigs = [Promise.resolve(content)].concat(sigs);
        return Promise.all(sigs);
      });
      promise = promise.then(function(results) {
        var content = results[0];
        return {
          payload: content,
          signatures: results.slice(1)
        };
      });
      switch (format) {
        case "compact":
          promise = promise.then(function(jws) {
            var compact = [
              jws.signatures[0].protected,
              jws.payload,
              jws.signatures[0].signature
            ];
            compact = compact.join(".");
            return compact;
          });
          break;
        case "flattened":
          promise = promise.then(function(jws) {
            var flattened = {};
            flattened.payload = jws.payload;

            var sig = jws.signatures[0];
            if (sig.protected) {
              flattened.protected = sig.protected;
            }
            if (sig.header) {
              flattened.header = sig.header;
            }
            flattened.signature = sig.signature;

            return flattened;
          });
          break;
      }

      return promise;
    }
  });
};


/**
 * @description
 * Creates a new JWS.Signer with the given options and signatories.
 *
 * @param {Object} [opts] The signing options
 * @param {Boolean} [opts.compact] Use compact serialization?
 * @param {String} [opts.format] The serialization format to use ("compact",
 *                 "flattened", "general")
 * @param {Object} [opts.fields] Additional header fields
 * @param {JWK.Key[]|Object[]} [signs] Signatories, either as an array of
 *        JWK.Key instances; or an array of objects, each with the following
 *        properties
 * @param {JWK.Key} signs.key Key used to sign content
 * @param {Object} [signs.header] Per-signatory header fields
 * @param {String} [signs.reference] Reference field to identify the key
 * @param {String[]|String} [signs.protect] List of fields to integrity
 *        protect ("*" to protect all fields)
 * @returns {JWS.Signer} The signature generator.
 * @throws {Error} If Compact serialization is requested but there are
 *         multiple signatories
 */
function createSign(opts, signs) {
  // fixup signatories
  var options = opts,
      signStart = 1,
      signList = signs;

  if (arguments.length === 0) {
    throw new Error("at least one signatory must be provided");
  }
  if (arguments.length === 1) {
    signList = opts;
    signStart = 0;
    options = {};
  } else if (JWK.isKey(opts) ||
            (opts && "kty" in opts) ||
            (opts && "key" in opts &&
            (JWK.isKey(opts.key) || "kty" in opts.key))) {
    signList = opts;
    signStart = 0;
    options = {};
  } else {
    options = clone(opts);
  }
  if (!Array.isArray(signList)) {
    signList = slice(arguments, signStart);
  }

  // fixup options
  options = merge(clone(DEFAULTS), options);

  // setup header fields
  var allFields = options.fields || {};
  // setup serialization format
  var format = options.format;
  if (!format) {
    format = options.compact ? "compact" : "general";
  }
  if (("compact" === format || "flattened" === format) && 1 < signList.length) {
    throw new Error("too many signatories for compact or flattened JSON serialization");
  }

  // note protected fields (globally)
  // protected fields are per signature
  var protectAll = ("*" === options.protect);
  if (options.compact) {
    protectAll = true;
  }

  signList = signList.map(function(s, idx) {
    var p;

    // resolve a key
    if (s && "kty" in s) {
      p = JWK.asKey(s);
      p = p.then(function(k) {
        return {
          key: k
        };
      });
    } else if (s) {
      p = JWK.asKey(s.key);
      p = p.then(function(k) {
        return {
          header: s.header,
          reference: s.reference,
          protect: s.protect,
          key: k
        };
      });
    } else {
      p = Promise.reject(new Error("missing key for signatory " + idx));
    }

    // resolve the complete signatory
    p = p.then(function(signatory) {
      var key = signatory.key;

      // make sure there is a header
      var header = signatory.header || {};
      header = merge(merge({}, allFields), header);
      signatory.header = header;

      // ensure an algorithm
      if (!header.alg) {
        header.alg = key.algorithms(JWK.MODE_SIGN)[0] || "";
      }

      // determine the key reference
      var ref = signatory.reference;
      delete signatory.reference;
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

      // determine protected fields
      var protect = signatory.protect;
      if (protectAll || "*" === protect) {
        protect = Object.keys(header);
      } else if ("string" === protect) {
        protect = [protect];
      } else if (Array.isArray(protect)) {
        protect = protect.concat();
      } else if (!protect) {
        protect = [];
      } else {
        return Promise.reject(new Error("protect must be a list of fields"));
      }
      protect = uniq(protect);
      signatory.protected = protect;

      // freeze signatory
      signatory = Object.freeze(signatory);
      return signatory;
    });

    return p;
  });

  var cfg = {
    format: format
  };
  return new JWSSigner(cfg,
                       signList);
}

module.exports = {
  signer: JWSSigner,
  createSign: createSign
};
