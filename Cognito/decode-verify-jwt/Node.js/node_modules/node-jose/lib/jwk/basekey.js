/*!
 * jwk/basekey.js - JWK Key Base Class Implementation
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var assign = require("lodash.assign"),
    clone = require("lodash.clone"),
    flatten = require("lodash.flatten"),
    intersection = require("lodash.intersection"),
    merge = require("../util/merge"),
    omit = require("lodash.omit"),
    pick = require("lodash.pick"),
    uniq = require("lodash.uniq"),
    uuid = require("uuid");

var ALGORITHMS = require("../algorithms"),
    CONSTANTS = require("./constants.js"),
    HELPERS = require("./helpers.js"),
    UTIL = require("../util");

/**
 * @class JWK.Key
 * @classdesc
 * Represents a JSON Web Key instance.
 *
 * @description
 * **NOTE:** This class cannot be instantiated directly. Instead call
 * {@link JWK.asKey}, {@link JWK.KeyStore#add}, or
 * {@link JWK.KeyStore#generate}.
 */
var JWKBaseKeyObject = function(kty, ks, props, cfg) {
  // ### validate/coerce arguments ###
  if (!kty) {
    throw new Error("kty cannot be null");
  }

  if (!ks) {
    throw new Error("keystore cannot be null");
  }

  if (!props) {
    throw new Error("props cannot be null");
  } else if ("string" === typeof props) {
    props = JSON.parse(props);
  }

  if (!cfg) {
    throw new Error("cfg cannot be null");
  }

  var excluded = [];
  var keys = {},
      json = {},
      prints,
      kid;

  props = clone(props);
  // strip thumbprints if present
  prints = assign({}, props[HELPERS.INTERNALS.THUMBPRINT_KEY] || {});
  delete props[HELPERS.INTERNALS.THUMBPRINT_KEY];
  Object.keys(prints).forEach(function(a) {
    var h = prints[a];
    if (!kid) {
      kid = h;
      if (Buffer.isBuffer(kid)) {
        kid = UTIL.base64url.encode(kid);
      }
    }
    if (!Buffer.isBuffer(h)) {
      h = UTIL.base64url.decode(h);
      prints[a] = h;
    }
  });

  // force certain values
  props.kty = kty;
  props.kid = props.kid || kid || uuid();

  // setup base info
  var included = Object.keys(HELPERS.COMMON_PROPS).map(function(p) {
    return HELPERS.COMMON_PROPS[p].name;
  });
  json.base = pick(props, included);
  excluded = excluded.concat(Object.keys(json.base));

  // setup public information
  json.public = clone(props);
  keys.public = cfg.publicKey(json.public);
  if (keys.public) {
    // exclude public values from extra
    excluded = excluded.concat(Object.keys(json.public));
  }

  // setup private information
  json.private = clone(props);
  keys.private = cfg.privateKey(json.private);
  if (keys.private) {
    // exclude private values from extra
    excluded = excluded.concat(Object.keys(json.private));
  }

  // setup extra information
  json.extra = omit(props, excluded);

  // TODO: validate 'alg' against supported algorithms

  // setup calculated values
  var keyLen;
  if (keys.public && ("length" in keys.public)) {
    keyLen = keys.public.length;
  } else if (keys.private && ("length" in keys.private)) {
    keyLen = keys.private.length;
  } else {
    keyLen = NaN;
  }

  // ### Public Properties ###
  /**
   * @member {JWK.KeyStore} JWK.Key#keystore
   * @description
   * The owning keystore.
   */
  Object.defineProperty(this, "keystore", {
    value: ks,
    enumerable: true
  });
  /**
   * @member {Number} JWK.Key#length
   * @description
   * The size of this Key, in bits.
   */
  Object.defineProperty(this, "length", {
    value: keyLen,
    enumerable: true
  });
  /**
   * @member {String} JWK.Key#kty
   * @description
   * The type of Key.
   */
  Object.defineProperty(this, "kty", {
    value: kty,
    enumerable: true
  });

  /**
   * @member {String} JWK.Key#kid
   * @description
   * The identifier for this Key.
   */
  Object.defineProperty(this, "kid", {
    value: json.base.kid,
    enumerable: true
  });
  /**
   * @member {String} JWK.Key#use
   * @description
   * The usage for this Key.
   */
  Object.defineProperty(this, "use", {
    value: json.base.use || "",
    enumerable: true
  });
  /**
   * @member {String} JWK.Key#alg
   * @description
   * The sole algorithm this key can be used for.
   */
  Object.defineProperty(this, "alg", {
    value: json.base.alg || "",
    enumerable: true
  });

  // ### Public Methods ###
  /**
   * Generates the thumbprint of this Key.
   *
   * @param {String} [] The hash algorithm to use
   * @returns {Promise} The promise for the thumbprint generation.
   */
  Object.defineProperty(this, "thumbprint", {
    value: function(hash) {
      hash = (hash || HELPERS.INTERNALS.THUMBPRINT_HASH).toUpperCase();
      if (prints[hash]) {
        // return cached value
        return Promise.resolve(prints[hash]);
      }
      var p = HELPERS.thumbprint(cfg, json, hash);
      p = p.then(function(result) {
        if (result) {
          prints[hash] = result;
        }
        return result;
      });
      return p;
    }
  });
  /**
   * @method JWK.Key#algorithms
   * @description
   * The possible algorithms this Key can be used for. The returned
   * list is not any particular order, but is filtered based on the
   * Key's intended usage.
   *
   * @param {String} mode The operation mode
   * @returns {String[]} The list of supported algorithms
   * @see JWK.Key#supports
   */
  Object.defineProperty(this, "algorithms", {
    value: function(mode) {
      var modes = [];
      if (!this.use || this.use === "sig") {
        if (!mode || CONSTANTS.MODE_SIGN === mode) {
          modes.push(CONSTANTS.MODE_SIGN);
        }
        if (!mode || CONSTANTS.MODE_VERIFY === mode) {
          modes.push(CONSTANTS.MODE_VERIFY);
        }
      }
      if (!this.use || this.use === "enc") {
        if (!mode || CONSTANTS.MODE_ENCRYPT === mode) {
          modes.push(CONSTANTS.MODE_ENCRYPT);
        }
        if (!mode || CONSTANTS.MODE_DECRYPT === mode) {
          modes.push(CONSTANTS.MODE_DECRYPT);
        }
        if (!mode || CONSTANTS.MODE_WRAP === mode) {
          modes.push(CONSTANTS.MODE_WRAP);
        }
        if (!mode || CONSTANTS.MODE_UNWRAP === mode) {
          modes.push(CONSTANTS.MODE_UNWRAP);
        }
      }

      var self = this;
      var algs = modes.map(function(m) {
        return cfg.algorithms.call(self, keys, m);
      });
      algs = flatten(algs);
      algs = uniq(algs);
      if (this.alg) {
        // TODO: fix this correctly
        var valid;
        if ("oct" === kty) {
          valid = [this.alg, "dir"];
        } else {
          valid = [this.alg];
        }
        algs = intersection(algs, valid);
      }

      return algs;
    }
  });
  /**
   * @method JWK.Key#supports
   * @description
   * Determines if the given algorithm is supported.
   *
   * @param {String} alg The algorithm in question
   * @param {String} [mode] The operation mode
   * @returns {Boolean} `true` if {alg} is supported, and `false` otherwise.
   * @see JWK.Key#algorithms
   */
  Object.defineProperty(this, "supports", {
    value: function(alg, mode) {
      return (this.algorithms(mode).indexOf(alg) !== -1);
    }
  });
  /**
   * @method JWK.Key#has
   * @description
   * Determines if this Key contains the given parameter.
   *
   * @param {String} name The name of the parameter
   * @param {Boolean} [isPrivate=false] `true` if private parameters should be
   *        checked.
   * @returns {Boolean} `true` if the given parameter is present; `false`
   *          otherwise.
   */
  Object.defineProperty(this, "has", {
    value: function(name, isPrivate) {
      var contains = false;
      contains = contains || !!(json.base &&
                                (name in json.base));
      contains = contains || !!(keys.public &&
                                (name in keys.public));
      contains = contains || !!(json.extra &&
                                (name in json.extra));
      contains = contains || !!(isPrivate &&
                                keys.private &&
                                (name in keys.private));
      // TODO: check for export restrictions

      return contains;
    }
  });
  /**
   * @method JWK.Key#get
   * @description
   * Retrieves the value of the given parameter. The value returned by this
   * method is in its natural format, which might not exactly match its
   * JSON encoding (e.g., a binary string rather than a base64url-encoded
   * string).
   *
   * **NOTE:** This method can return `false`. Call
   * {@link JWK.Key#has} to determine if the parameter is present.
   *
   * @param {String} name The name of the parameter
   * @param {Boolean} [isPrivate=false] `true` if private parameters should
   *        be checked.
   * @returns {any} The value of the named parameter, or undefined if
   *          it is not present.
   */
  Object.defineProperty(this, "get", {
    value: function(name, isPrivate) {
      var src;
      if (json.base && (name in json.base)) {
        src = json.base;
      } else if (keys.public && (name in keys.public)) {
        src = keys.public;
      } else if (json.extra && (name in json.extra)) {
        src = json.extra;
      } else if (isPrivate && keys.private && (name in keys.private)) {
        // TODO: check for export restrictions
        src = keys.private;
      }

      return src && src[name] || null;
    }
  });
  /**
   * @method JWK.Key#toJSON
   * @description
   * Returns the JSON representation of this Key.  All properties of the
   * returned JSON object are properly encoded (e.g., base64url encoding for
   * any binary strings).
   *
   * @param {Boolean} [isPrivate=false] `true` if private parameters should be
   *        included.
   * @param {String[]} [excluded] The list of parameters to exclude from
   *        the returned JSON.
   * @returns {Object} The plain JSON object
   */
  Object.defineProperty(this, "toJSON", {
    value: function(isPrivate, excluded) {
      // coerce arguments
      if (Array.isArray(isPrivate)) {
        excluded = isPrivate;
        isPrivate = false;
      }
      var result = {};

      // TODO: check for export restrictions
      result = merge(result,
                       json.base,
                       json.public,
                       ("boolean" === typeof isPrivate && isPrivate) ? json.private : {},
                       json.extra);
      result = omit(result, excluded || []);

      return result;
    }
  });

  /**
   * @method JWK.Key#toPEM
   * @description
   * Returns the PEM representation of this Key as a string.
   *
   * @param {Boolean} [isPrivate=false] `true` if private parameters should be
   *        included.
   * @returns {string} The PEM-encoded string
   */
  Object.defineProperty(this, "toPEM", {
    value: function(isPrivate) {
      if (isPrivate === null) {
        isPrivate = false;
      }

      if (!cfg.convertToPEM) {
        throw new Error("Unsupported key type for PEM encoding");
      }
      var k = (isPrivate) ? keys.private : keys.public;
      if (!k) {
        throw new Error("Invalid key");
      }
      return cfg.convertToPEM.call(this, k, isPrivate);
    }
  });

  /**
   * @method JWK.Key#toObject
   * @description
   * Returns the plain object representing this Key.  All properties of the
   * returned object are in their natural encoding (e.g., binary strings
   * instead of base64url encoded).
   *
   * @param {Boolean} [isPrivate=false] `true` if private parameters should be
   *        included.
   * @param {String[]} [excluded] The list of parameters to exclude from
   *        the returned object.
   * @returns {Object} The plain Object.
   */
  Object.defineProperty(this, "toObject", {
    value: function(isPrivate, excluded) {
      // coerce arguments
      if (Array.isArray(isPrivate)) {
        excluded = isPrivate;
        isPrivate = false;
      }
      var result = {};

      // TODO: check for export restrictions
      result = merge(result,
                       json.base,
                       keys.public,
                       ("boolean" === typeof isPrivate && isPrivate) ? keys.private : {},
                       json.extra);
      result = omit(result, (excluded || []).concat("length"));

      return result;
    }
  });

  /**
   * @method JWK.Key#sign
   * @description
   * Sign the given data using the specified algorithm.
   *
   * **NOTE:** This is the primitive signing operation; the output is
   * _**NOT**_ a JSON Web Signature (JWS) object.
   *
   * The Promise, when fulfilled, returns an Object with the following
   * properties:
   *
   * + **data**: The data that was signed (and should be equal to {data}).
   * + **mac**: The signature or message authentication code (MAC).
   *
   * @param {String} alg The signing algorithm
   * @param {String|Buffer} data The data to sign
   * @param {Object} [props] Additional properties for the signing
   *        algorithm.
   * @returns {Promise} The promise for the signing operation.
   * @throws {Error} If {alg} is not appropriate for this Key; or if
   *         this Key does not contain the appropriate parameters.
   */
  Object.defineProperty(this, "sign", {
    value: function(alg, data, props) {
      // validate appropriateness
      if (this.algorithms("sign").indexOf(alg) === -1) {
        return Promise.reject(new Error("unsupported algorithm"));
      }
      var k = cfg.signKey.call(this, alg, keys);
      if (!k) {
        return Promise.reject(new Error("improper key"));
      }

      // prepare properties (if any)
      props = (props) ?
              clone(props) :
              {};
      if (cfg.signProps) {
        props = merge(props, cfg.signProps.call(this, alg, props));
      }
      return ALGORITHMS.sign(alg, k, data, props);
    }
  });
  /**
   * @method JWK.Key#verify
   * @description
   * Verify the given data and signature using the specified algorithm.
   *
   * **NOTE:** This is the primitive verification operation; the input is
   * _**NOT**_ a JSON Web Signature.</p>
   *
   * The Promise, when fulfilled, returns an Object with the following
   * properties:
   *
   * + **data**: The data that was verified (and should be equal to
   *   {data}).
   * + **mac**: The signature or MAC that was verified (and should be equal
   *   to {mac}).
   * + **valid**: `true` if {mac} is valid for {data}.
   *
   * @param {String} alg The verification algorithm
   * @param {String|Buffer} data The data to verify
   * @param {String|Buffer} mac The signature or MAC to verify
   * @param {Object} [props] Additional properties for the verification
   *        algorithm.
   * @returns {Promise} The promise for the verification operation.
   * @throws {Error} If {alg} is not appropriate for this Key; or if
   *         the Key does not contain the appropriate properties.
   */
  Object.defineProperty(this, "verify", {
    value: function(alg, data, mac, props) {
      // validate appropriateness
      if (this.algorithms("verify").indexOf(alg) === -1) {
        return Promise.reject(new Error("unsupported algorithm"));
      }
      var k = cfg.verifyKey.call(this, alg, keys);
      if (!k) {
        return Promise.reject(new Error("improper key"));
      }

      // prepare properties (if any)
      props = (props) ?
              clone(props) :
              {};
      if (cfg.verifyProps) {
        props = merge(props, cfg.verifyProps.call(this, alg, props));
      }
      return ALGORITHMS.verify(alg, k, data, mac, props);
    }
  });

  /**
   * @method JWK.Key#encrypt
   * @description
   * Encrypts the given data using the specified algorithm.
   *
   * **NOTE:** This is the primitive encryption operation; the output is
   * _**NOT**_ a JSON Web Encryption (JWE) object.
   *
   * **NOTE:** This operation is treated as distinct from {@link
   * JWK.Key#wrap}, as different algorithms and properties are often
   * used for wrapping a key versues encrypting arbitrary data.
   *
   * The Promise, when fulfilled, returns an object with the following
   * properties:
   *
   * + **data**: The ciphertext data
   * + **mac**: The associated message authentication code (MAC).
   *
   * @param {String} alg The encryption algorithm
   * @param {Buffer|String} data The data to encrypt
   * @param {Object} [props] Additional properties for the encryption
   *        algorithm.
   * @returns {Promise} The promise for the encryption operation.
   * @throws {Error} If {alg} is not appropriate for this Key; or if
   *         this Key does not contain the appropriate parameters.
   */
  Object.defineProperty(this, "encrypt", {
    value: function(alg, data, props) {
      // validate appropriateness
      if (this.algorithms("encrypt").indexOf(alg) === -1) {
        return Promise.reject(new Error("unsupported algorithm"));
      }
      var k = cfg.encryptKey.call(this, alg, keys);
      if (!k) {
        return Promise.reject(new Error("improper key"));
      }

      // prepare properties (if any)
      props = (props) ?
              clone(props) :
              {};
      if (cfg.encryptProps) {
        props = merge(props, cfg.encryptProps.call(this, alg, props));
      }
      return ALGORITHMS.encrypt(alg, k, data, props);
    }
  });
  /**
   * @method JWK.Key#decrypt
   * @description
   * Decrypts the given data using the specified algorithm.
   *
   * **NOTE:** This is the primitive decryption operation; the input is
   * _**NOT**_ a JSON Web Encryption (JWE) object.
   *
   * **NOTE:** This operation is treated as distinct from {@link
   * JWK.Key#unwrap}, as different algorithms and properties are often used
   * for unwrapping a key versues decrypting arbitrary data.
   *
   * The Promise, when fulfilled, returns the plaintext data.
   *
   * @param {String} alg The decryption algorithm.
   * @param {Buffer|String} data The data to decypt.
   * @param {Object} [props] Additional data for the decryption operation.
   * @returns {Promise} The promise for the decryption operation.
   * @throws {Error} If {alg} is not appropriate for this Key; or if
   *         the Key does not contain the appropriate properties.
   */
  Object.defineProperty(this, "decrypt", {
    value: function(alg, data, props) {
      // validate appropriateness
      if (this.algorithms("decrypt").indexOf(alg) === -1) {
        return Promise.reject(new Error("unsupported algorithm"));
      }
      var k = cfg.decryptKey.call(this, alg, keys);
      if (!k) {
        return Promise.reject(new Error("improper key"));
      }

      // prepare properties (if any)
      props = (props) ?
              clone(props) :
              {};
      if (cfg.decryptProps) {
        props = merge(props, cfg.decryptProps.call(this, alg, props));
      }
      return ALGORITHMS.decrypt(alg, k, data, props);
    }
  });

  /**
   * @method JWK.Key#wrap
   * @description
   * Wraps the given key using the specified algorithm.
   *
   * **NOTE:** This is the primitive encryption operation; the output is
   * _**NOT**_ a JSON Web Encryption (JWE) object.
   *
   * **NOTE:** This operation is treated as distinct from {@link
   * JWK.Key#encrypt}, as different algorithms and properties are
   * often used for wrapping a key versues encrypting arbitrary data.
   *
   * The Promise, when fulfilled, returns an object with the following
   * properties:
   *
   * + **data**: The ciphertext data
   * + **headers**: The additional header parameters to apply to a JWE.
   *
   * @param {String} alg The encryption algorithm
   * @param {Buffer|String} data The data to encrypt
   * @param {Object} [props] Additional properties for the encryption
   *        algorithm.
   * @returns {Promise} The promise for the encryption operation.
   * @throws {Error} If {alg} is not appropriate for this Key; or if
   *         this Key does not contain the appropriate parameters.
   */
  Object.defineProperty(this, "wrap", {
    value: function(alg, data, props) {
      // validate appropriateness
      if (this.algorithms("wrap").indexOf(alg) === -1) {
        return Promise.reject(new Error("unsupported algorithm"));
      }
      var k = cfg.wrapKey.call(this, alg, keys);
      if (!k) {
        return Promise.reject(new Error("improper key"));
      }

      // prepare properties (if any)
      props = (props) ?
              clone(props) :
              {};
      if (cfg.wrapProps) {
        props = merge(props, cfg.wrapProps.call(this, alg, props));
      }
      return ALGORITHMS.encrypt(alg, k, data, props);
    }
  });
  /**
   * @method JWK.Key#unwrap
   * @description
   * Unwraps the given key using the specified algorithm.
   *
   * **NOTE:** This is the primitive unwrap operation; the input is
   * _**NOT**_ a JSON Web Encryption (JWE) object.
   *
   * **NOTE:** This operation is treated as distinct from {@link
   * JWK.Key#decrypt}, as different algorithms and properties are often used
   * for unwrapping a key versues decrypting arbitrary data.
   *
   * The Promise, when fulfilled, returns the unwrapped key.
   *
   * @param {String} alg The unwrap algorithm.
   * @param {Buffer|String} data The data to unwrap.
   * @param {Object} [props] Additional data for the unwrap operation.
   * @returns {Promise} The promise for the unwrap operation.
   * @throws {Error} If {alg} is not appropriate for this Key; or if
   *         the Key does not contain the appropriate properties.
   */
  Object.defineProperty(this, "unwrap", {
    value: function(alg, data, props) {
      // validate appropriateness
      if (this.algorithms("unwrap").indexOf(alg) === -1) {
        return Promise.reject(new Error("unsupported algorithm"));
      }
      var k = cfg.unwrapKey.call(this, alg, keys);
      if (!k) {
        return Promise.reject(new Error("improper key"));
      }

      // prepare properties (if any)
      props = (props) ?
              clone(props) :
              {};
      if (cfg.unwrapProps) {
        props = merge(props, cfg.unwrapProps.call(this, alg, props));
      }
      return ALGORITHMS.decrypt(alg, k, data, props);
    }
  });
};

module.exports = JWKBaseKeyObject;
