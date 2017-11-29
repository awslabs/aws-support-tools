/*!
 * jwk/rsa.js - RSA Key Representation
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var ecutil = require("../algorithms/ec-util.js"),
    forge = require("../deps/forge"),
    depsecc = require("../deps/ecc");

var JWK = {
  BaseKey: require("./basekey.js"),
  helpers: require("./helpers.js")
};

var SIG_ALGS = [
  "ES256",
  "ES384",
  "ES512"
];
var WRAP_ALGS = [
  "ECDH-ES",
  "ECDH-ES+A128KW",
  "ECDH-ES+A192KW",
  "ECDH-ES+A256KW"
];

var EC_OID = "1.2.840.10045.2.1";
function oidToCurveName(oid) {
  switch (oid) {
    case "1.2.840.10045.3.1.7":
      return "P-256";
    case "1.3.132.0.34":
      return "P-384";
    case "1.3.132.0.35":
      return "P-521";
    default:
      return null;
  }
}
function curveNameToOid(crv) {
  switch (crv) {
    case "P-256":
      return "1.2.840.10045.3.1.7";
    case "P-384":
      return "1.3.132.0.34";
    case "P-521":
      return "1.3.132.0.35";
    default:
      return null;
  }
}

var JWKEcCfg = {
  publicKey: function(props) {
    var fields = JWK.helpers.COMMON_PROPS.concat([
      {name: "crv", type: "string"},
      {name: "x", type: "binary"},
      {name: "y", type: "binary"}
    ]);
    var pk = JWK.helpers.unpackProps(props, fields);
    if (pk && pk.crv && pk.x && pk.y) {
      pk.length = ecutil.curveSize(pk.crv);
    } else {
      delete pk.crv;
      delete pk.x;
      delete pk.y;
    }

    return pk;
  },
  privateKey: function(props) {
    var fields = JWK.helpers.COMMON_PROPS.concat([
      {name: "crv", type: "string"},
      {name: "x", type: "binary"},
      {name: "y", type: "binary"},
      {name: "d", type: "binary"}
    ]);
    var pk = JWK.helpers.unpackProps(props, fields);
    if (pk && pk.crv && pk.x && pk.y && pk.d) {
      pk.length = ecutil.curveSize(pk.crv);
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
      crv: json.crv,
      kty: "EC",
      x: json.x,
      y: json.y
    };
    return fields;
  },
  algorithms: function(keys, mode) {
    var len = (keys.public && keys.public.length) ||
              (keys.private && keys.private.length) ||
              0;
    // NOTE: 521 is the actual, but 512 is the expected
    if (len === 521) {
        len = 512;
    }

    switch (mode) {
      case "encrypt":
      case "decrypt":
        return [];
      case "wrap":
        return (keys.public && WRAP_ALGS) || [];
      case "unwrap":
        return (keys.private && WRAP_ALGS) || [];
      case "sign":
        if (!keys.private) {
          return [];
        }
        return SIG_ALGS.filter(function(a) {
          return (a === ("ES" + len));
        });
      case "verify":
        if (!keys.public) {
          return [];
        }
        return SIG_ALGS.filter(function(a) {
          return (a === ("ES" + len));
        });
    }
  },

  encryptKey: function(alg, keys) {
    return keys.public;
  },
  decryptKey: function(alg, keys) {
    return keys.private;
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
    // curveName to OID
    var oid = key.crv;
    oid = curveNameToOid(oid);
    oid = forge.asn1.oidToDer(oid);
    // key as bytes
    var type,
        pub,
        asn1;
    if (isPrivate) {
      type = "EC PRIVATE KEY";
      pub = Buffer.concat([
        new Buffer([0x00, 0x04]),
        key.x,
        key.y
      ]).toString("binary");
      key = key.d.toString("binary");
      asn1 = forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.SEQUENCE, true, [
        forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.INTEGER, false, "\u0001"),
        forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.OCTETSTRING, false, key),
        forge.asn1.create(forge.asn1.Class.CONTEXT_SPECIFIC, 0, true, [
          forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.OID, false, oid.bytes())
        ]),
        forge.asn1.create(forge.asn1.Class.CONTEXT_SPECIFIC, 1, true, [
          forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.BITSTRING, false, pub)
        ])
      ]);
    } else {
      type = "PUBLIC KEY";
      key = Buffer.concat([
        new Buffer([0x00, 0x04]),
        key.x,
        key.y
      ]).toString("binary");
      asn1 = forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.SEQUENCE, true, [
        forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.SEQUENCE, true, [
          forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.OID, false, forge.asn1.oidToDer(EC_OID).bytes()),
          forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.OID, false, oid.bytes())
        ]),
        forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.BITSTRING, false, key)
      ]);
    }
    asn1 = forge.asn1.toDer(asn1).bytes();
    var pem = forge.pem.encode({
      type: type,
      body: asn1
    });
    return pem;
  }
};

// Inspired by digitalbaazar/node-forge/js/rsa.js
var validators = {
  oid: EC_OID,
  privateKey: {
    // ECPrivateKey
    name: "ECPrivateKey",
    tagClass: forge.asn1.Class.UNIVERSAL,
    type: forge.asn1.Type.SEQUENCE,
    constructed: true,
    value: [
      {
        // EC version
        name: "ECPrivateKey.version",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false
      },
      {
        // private value (d)
        name: "ECPrivateKey.private",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.OCTETSTRING,
        constructed: false,
        capture: "d"
      },
      {
        // EC parameters
        tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
        name: "ECPrivateKey.parameters",
        constructed: true,
        value: [
          {
            // namedCurve (crv)
            name: "ECPrivateKey.namedCurve",
            tagClass: forge.asn1.Class.UNIVERSAL,
            type: forge.asn1.Type.OID,
            constructed: false,
            capture: "crv"
          }
        ]
      },
      {
        // publicKey
        name: "ECPrivateKey.publicKey",
        tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
        constructed: true,
        value: [
          {
            name: "ECPrivateKey.point",
            tagClass: forge.asn1.Class.UNIVERSAL,
            type: forge.asn1.Type.BITSTRING,
            constructed: false,
            capture: "point"
          }
        ]
      }
    ]
  },
  embeddedPrivateKey: {
    // ECPrivateKey
    name: "ECPrivateKey",
    tagClass: forge.asn1.Class.UNIVERSAL,
    type: forge.asn1.Type.SEQUENCE,
    constructed: true,
    value: [
      {
        // EC version
        name: "ECPrivateKey.version",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.INTEGER,
        constructed: false
      },
      {
        // private value (d)
        name: "ECPrivateKey.private",
        tagClass: forge.asn1.Class.UNIVERSAL,
        type: forge.asn1.Type.OCTETSTRING,
        constructed: false,
        capture: "d"
      },
      {
        // publicKey
        name: "ECPrivateKey.publicKey",
        tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
        constructed: true,
        value: [
          {
            name: "ECPrivateKey.point",
            tagClass: forge.asn1.Class.UNIVERSAL,
            type: forge.asn1.Type.BITSTRING,
            constructed: false,
            capture: "point"
          }
        ]
      }
    ]
  }
};

var JWKEcFactory = {
  kty: "EC",
  validators: validators,
  prepare: function(props) {
    // TODO: validate key properties
    var cfg = JWKEcCfg;
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
    var keypair = depsecc.generateKeyPair(size);
    var result = {
      "crv": size,
      "x": keypair.public.x,
      "y": keypair.public.y,
      "d": keypair.private.d
    };
    return Promise.resolve(result);
  },
  import: function(input) {
    if (validators.oid !== input.keyOid) {
      return null;
    }

    // coerce key params to OID
    var crv;
    if (input.keyParams && forge.asn1.Type.OID === input.keyParams.type) {
      crv = forge.asn1.derToOid(input.keyParams.value);
      crv = oidToCurveName(crv);
    } else if (input.crv) {
      crv = forge.asn1.derToOid(input.crv);
      crv = oidToCurveName(crv);
    }
    if (!crv) {
      return null;
    }

    if (!input.parsed) {
      var capture = {},
          errors = [];
      if ("private" === input.type) {
        // coerce capture.value to DER *iff* private
        if ("string" === typeof input.keyValue) {
          input.keyValue = forge.asn1.fromDer(input.keyValue);
        } else if (Array.isArray(input.keyValue)) {
          input.keyValue = input.keyValue[0];
        }

        if (!forge.asn1.validate(input.keyValue,
                                 validators.embeddedPrivateKey,
                                 capture,
                                 errors)) {
          return null;
        }
      } else {
        capture.point = input.keyValue;
      }
      input = capture;
    }

    // convert factors to Buffers
    var output = {
      kty: "EC",
      crv: crv
    };
    if (input.d) {
      output.d = new Buffer(input.d, "binary");
    }
    if (input.point) {
      var pt = new Buffer(input.point, "binary");
      // only support uncompressed
      if (4 !== pt.readUInt16BE(0)) {
        return null;
      }
      pt = pt.slice(2);
      var len = pt.length / 2;
      output.x = pt.slice(0, len);
      output.y = pt.slice(len);
    }
    return output;
  }
};
// public API
module.exports = Object.freeze({
  config: JWKEcCfg,
  factory: JWKEcFactory
});

// registration
(function(REGISTRY) {
  REGISTRY.register(JWKEcFactory);
})(require("./keystore").registry);
