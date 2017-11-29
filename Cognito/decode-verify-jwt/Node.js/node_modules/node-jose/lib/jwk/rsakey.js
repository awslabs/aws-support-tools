/*!
 * jwk/rsa.js - RSA Key Representation
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js"),
    rsau = require("../algorithms/rsa-util"),
    nodeCrypto = require("../algorithms/helpers").nodeCrypto;

var JWK = {
  BaseKey: require("./basekey.js"),
  helpers: require("./helpers.js")
};

var SIG_ALGS = [
  "RS256",
  "RS384",
  "RS512",
  "PS256",
  "PS384",
  "PS512"
];
var WRAP_ALGS = [
  "RSA-OAEP",
  "RSA-OAEP-256",
  "RSA1_5"
];

var JWKRsaCfg = {
  publicKey: function(props) {
    var fields = JWK.helpers.COMMON_PROPS.concat([
      {name: "n", type: "binary"},
      {name: "e", type: "binary"}
    ]);
    var pk;
    pk = JWK.helpers.unpackProps(props, fields);
    if (pk && pk.n && pk.e) {
      pk.length = pk.n.length * 8;
    } else {
      delete pk.e;
      delete pk.n;
    }

    return pk;
  },
  privateKey: function(props) {
    var fields = JWK.helpers.COMMON_PROPS.concat([
      {name: "n", type: "binary"},
      {name: "e", type: "binary"},
      {name: "d", type: "binary"},
      {name: "p", type: "binary"},
      {name: "q", type: "binary"},
      {name: "dp", type: "binary"},
      {name: "dq", type: "binary"},
      {name: "qi", type: "binary"}
    ]);

    var pk;
    pk = JWK.helpers.unpackProps(props, fields);
    if (pk && pk.d && pk.n && pk.e && pk.p && pk.q && pk.dp && pk.dq && pk.qi) {
      pk.length = pk.d.length * 8;
    } else {
      pk = undefined;
    }

    return pk;
  },
  thumbprint: function(json) {
    if (json.public) {
      json = json.public;
    }
    var fields = {
      e: json.e,
      kty: "RSA",
      n: json.n
    };
    return fields;
  },
  algorithms: function(keys, mode) {
    switch (mode) {
    case "encrypt":
    case "decrypt":
      return [];
    case "wrap":
      return (keys.public && WRAP_ALGS.slice()) || [];
    case "unwrap":
      return (keys.private && WRAP_ALGS.slice()) || [];
    case "sign":
      return (keys.private && SIG_ALGS.slice()) || [];
    case "verify":
      return (keys.public && SIG_ALGS.slice()) || [];
    }

    return [];
  },

  wrapKey: function(alg, keys) {
    return keys.public;
  },
  unwrapKey: function(alg, keys) {
    return keys.private;
  },

  signKey: function(alg, keys) {
    return keys.private;
  },
  verifyKey: function(alg, keys) {
    return keys.public;
  },

  convertToPEM: function(key, isPrivate) {
    var k = rsau.convertToForge(key, !isPrivate);
    if (!isPrivate) {
      return forge.pki.publicKeyToPem(k);
    }
    return forge.pki.privateKeyToPem(k);
  }
};

function convertBNtoBuffer(bn) {
  bn = bn.toString(16);
  if (bn.length % 2) {
    bn = "0" + bn;
  }
  return new Buffer(bn, "hex");
}

// Adapted from digitalbaazar/node-forge/js/rsa.js
var validators = {
  oid: "1.2.840.113549.1.1.1",
  privateKey: {
    name: "RSAPrivateKey",
    tagClass: forge.asn1.Class.UNIVERSAL,
    type: forge.asn1.Type.SEQUENCE,
    constructed: true,
    value: [
      {
        // Version (INTEGER)
        name: "RSAPrivateKey.version",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "version"
      },
      {
        // modulus (n)
        name: "RSAPrivateKey.modulus",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "n"
      },
      {
        // publicExponent (e)
        name: "RSAPrivateKey.publicExponent",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "e"
      },
      {
        // privateExponent (d)
        name: "RSAPrivateKey.privateExponent",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "d"
      },
      {
        // prime1 (p)
        name: "RSAPrivateKey.prime1",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "p"
      },
      {
        // prime2 (q)
        name: "RSAPrivateKey.prime2",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "q"
      },
      {
        // exponent1 (d mod (p-1))
        name: "RSAPrivateKey.exponent1",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "dp"
      },
      {
        // exponent2 (d mod (q-1))
        name: "RSAPrivateKey.exponent2",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "dq"
      },
      {
        // coefficient ((inverse of q) mod p)
        name: "RSAPrivateKey.coefficient",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "qi"
      }
    ]
  },
  publicKey: {
    // RSAPublicKey
    name: "RSAPublicKey",
    tagClass: forge.asn1.Class.UNIVERSAL,
    type: forge.asn1.Type.SEQUENCE,
    constructed: true,
    value: [
      {
        // modulus (n)
        name: "RSAPublicKey.modulus",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "n"
      },
      {
        // publicExponent (e)
        name: "RSAPublicKey.exponent",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false,
        capture: "e"
      }
    ]
  }
};

// Factory
var JWKRsaFactory = {
  kty: "RSA",
  validators: validators,
  prepare: function(props) {
    // TODO: validate key properties
    var cfg = JWKRsaCfg;
    var p = Promise.resolve(props);
    p = p.then(function(json) {
      return JWK.helpers.thumbprint(cfg, json);
    });
    p = p.then(function(hash) {
      var prints = {};
      prints[JWK.helpers.INTERNALS.THUMBPRINT_HASH] = hash;
      props[JWK.helpers.INTERNALS.THUMBPRINT_KEY] = prints;
      return cfg;
    });
    return p;
  },
  generate: function(size) {
    // TODO: validate key sizes
    var promise;

    if (nodeCrypto) {
      promise = new Promise(function (resolve, reject) {
        forge.pki.rsa.generateKeyPair({
          bits: size,
          e: 0x010001
        }, function (err, key) {
          if (err) return reject(err);
          resolve(key.privateKey);
        });
      });
    } else {
      var key = forge.pki.rsa.generateKeyPair({
        bits: size,
        e: 0x010001
      });
      promise = Promise.resolve(key.privateKey);
    };

    return promise.then(function (key) {

      // convert to JSON-ish
      var result = {};
      [
        "e",
        "n",
        "d",
        "p",
        "q",
        {incoming: "dP", outgoing: "dp"},
        {incoming: "dQ", outgoing: "dq"},
        {incoming: "qInv", outgoing: "qi"}
      ].forEach(function(f) {
        var incoming,
            outgoing;

        if ("string" === typeof f) {
          incoming = outgoing = f;
        } else {
          incoming = f.incoming;
          outgoing = f.outgoing;
        }

        if (incoming in key) {
          result[outgoing] = convertBNtoBuffer(key[incoming]);
        }
      });

      return result;
    });
  },
  import: function(input) {
    if (validators.oid !== input.keyOid) {
      return null;
    }

    if (!input.parsed) {
      // coerce capture.keyValue to DER
      if ("string" === typeof input.keyValue) {
        input.keyValue = forge.asn1.fromDer(input.keyValue);
      } else if (Array.isArray(input.keyValue)) {
        input.keyValue = input.keyValue[0];
      }
      // capture key factors
      var validator = ("private" === input.type) ?
                      validators.privateKey :
                      validators.publicKey;
      var capture = {},
          errors = [];
      if (!forge.asn1.validate(input.keyValue, validator, capture, errors)) {
        return null;
      }
      input = capture;
    }

    // convert factors to Buffers
    var output = {
      kty: "RSA"
    };
    ["n", "e", "d", "p", "q", "dp", "dq", "qi"].forEach(function(f) {
      if (!(f in input)) {
        return;
      }
      var b = new Buffer(input[f], "binary");
      // remove leading zero padding if any
      if (0 === b[0]) {
        b = b.slice(1);
      }
      output[f] = b;
    });
    return output;
  }
};

// public API
module.exports = Object.freeze({
  config: JWKRsaCfg,
  factory: JWKRsaFactory
});

// registration
(function(REGISTRY) {
  REGISTRY.register(JWKRsaFactory);
})(require("./keystore").registry);
