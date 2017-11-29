/*!
 * jwk/octkey.js - Symmetric Octet Key Representation
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var util = require("../util");

var JWK = {
  BaseKey: require("./basekey.js"),
  helpers: require("./helpers.js")
};

var SIG_ALGS = [
  "HS256",
  "HS384",
  "HS512"
];
var ENC_ALGS = [
  "A128GCM",
  "A192GCM",
  "A256GCM",
  "A128CBC-HS256",
  "A192CBC-HS384",
  "A256CBC-HS512",
  "A128CBC+HS256",
  "A192CBC+HS384",
  "A256CBC+HS512"
];
var WRAP_ALGS = [
  "A128KW",
  "A192KW",
  "A256KW",
  "A128GCMKW",
  "A192GCMKW",
  "A256GCMKW",
  "PBES2-HS256+A128KW",
  "PBES2-HS384+A192KW",
  "PBES2-HS512+A256KW",
  "dir"
];

function adjustDecryptProps(alg, props) {
  if ("iv" in props) {
    props.iv = Buffer.isBuffer(props.iv) ?
               props.iv :
               util.base64url.decode(props.iv || "");
  }
  if ("adata" in props) {
    props.adata = Buffer.isBuffer(props.adata) ?
                  props.adata :
                  new Buffer(props.adata || "", "utf8");
  }
  if ("mac" in props) {
    props.mac = Buffer.isBuffer(props.mac) ?
                props.mac :
                util.base64url.decode(props.mac || "");
  }
  if ("tag" in props) {
    props.tag = Buffer.isBuffer(props.tag) ?
                props.tag :
                util.base64url.decode(props.tag || "");
  }

  return props;
}
function adjustEncryptProps(alg, props) {
  if ("iv" in props) {
    props.iv = Buffer.isBuffer(props.iv) ?
               props.iv :
               util.base64url.decode(props.iv || "");
  }
  if ("adata" in props) {
    props.adata = Buffer.isBuffer(props.adata) ?
                  props.adata :
                  new Buffer(props.adata || "", "utf8");
  }

  return props;
}

var JWKOctetCfg = {
  publicKey: function(props) {
    var fields = JWK.helpers.COMMON_PROPS.concat([
    ]);

    var pk;
    pk = JWK.helpers.unpackProps(props, fields);

    return pk;
  },
  privateKey: function(props) {
    var fields = JWK.helpers.COMMON_PROPS.concat([
      {name: "k", type: "binary"}
    ]);

    var pk;
    pk = JWK.helpers.unpackProps(props, fields);
    if (pk && pk.k) {
      pk.length = pk.k.length * 8;
    } else {
      pk = undefined;
    }

    return pk;
  },

  thumbprint: function(json) {
    if (json.private) {
      json = json.private;
    }
    var fields;
    fields = {
      k: json.k || "",
      kty: "oct"
    };
    return fields;
  },
  algorithms: function(keys, mode) {
    var len = keys.private && (keys.private.k.length * 8);
    var mins = [256, 384, 512];

    if (!len) {
      return [];
    }
    switch (mode) {
      case "encrypt":
      case "decrypt":
        return ENC_ALGS.filter(function(a) {
          return (a === ("A" + (len / 2) + "CBC-HS" + len)) ||
                 (a === ("A" + (len / 2) + "CBC+HS" + len)) ||
                 (a === ("A" + len + "GCM"));
        });
      case "sign":
      case "verify":
        // TODO: allow for HS{less-than-keysize}
        return SIG_ALGS.filter(function(a) {
          var result = false;
          mins.forEach(function(m) {
            if (m > len) { return; }
            result = result | (a === ("HS" + m));
          });
          return result;
        });
      case "wrap":
      case "unwrap":
        return WRAP_ALGS.filter(function(a) {
          return (a === ("A" + len + "KW")) ||
                 (a === ("A" + len + "GCMKW")) ||
                 (a.indexOf("PBES2-") === 0) ||
                 (a === "dir");
        });
    }

    return [];
  },
  encryptKey: function(alg, keys) {
    return keys.private && keys.private.k;
  },
  encryptProps: adjustEncryptProps,

  decryptKey: function(alg, keys) {
    return keys.private && keys.private.k;
  },
  decryptProps: adjustDecryptProps,

  wrapKey: function(alg, keys) {
    return keys.private && keys.private.k;
  },
  wrapProps: adjustEncryptProps,

  unwrapKey: function(alg, keys) {
    return keys.private && keys.private.k;
  },
  unwrapProps: adjustDecryptProps,

  signKey: function(alg, keys) {
    return keys.private && keys.private.k;
  },
  verifyKey: function(alg, keys) {
    return keys.private && keys.private.k;
  }
};

// Factory
var JWKOctetFactory = {
  kty: "oct",
  prepare: function(props) {
    // TODO: validate key properties
    var cfg = JWKOctetCfg;
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
    var key = util.randomBytes(size / 8);

    return Promise.resolve({
      k: key
    });
  }
};

// public API
module.exports = Object.freeze({
  config: JWKOctetCfg,
  factory: JWKOctetFactory
});

// registration
(function(REGISTRY) {
  REGISTRY.register(JWKOctetFactory);
})(require("./keystore").registry);
