/*!
 * jwk/helpers.js - JWK Internal Helper Functions and Constants
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var clone = require("lodash.clone"),
    util = require("../util"),
    forge = require("../deps/forge");

var ALGORITHMS = require("../algorithms");

// ### ASN.1 Validators
// Adapted from digitalbazaar/node-forge/js/asn1.js
// PrivateKeyInfo
var privateKeyValidator = {
  name: "PrivateKeyInfo",
  tagClass: forge.asn1.Class.UNIVERSAL,
  type: forge.asn1.Type.SEQUENCE,
  constructed: true,
  value: [
    {
      // Version (INTEGER)
      name: "PrivateKeyInfo.version",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.INTEGER,
      constructed: false,
      capture: "keyVersion"
    },
    {
      name: "PrivateKeyInfo.privateKeyAlgorithm",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.SEQUENCE,
      constructed: true,
      value: [
        {
          name: "AlgorithmIdentifier.algorithm",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.OID,
          constructed: false,
          capture: "keyOid"
        },
        {
          name: "AlgorithmIdentifier.parameters",
          captureAsn1: "keyParams"
        }
      ]
    },
    {
      name: "PrivateKeyInfo",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.OCTETSTRING,
      constructed: false,
      capture: "keyValue"
    }
  ]
};
// Adapted from digitalbazaar/node-forge/x509.js
var publicKeyValidator = {
  name: "SubjectPublicKeyInfo",
  tagClass: forge.asn1.Class.UNIVERSAL,
  type: forge.asn1.Type.SEQUENCE,
  constructed: true,
  value: [
    {
      name: "SubjectPublicKeyInfo.AlgorithmIdentifier",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.SEQUENCE,
      constructed: true,
      value: [
        {
          name: "AlgorithmIdentifier.algorithm",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.OID,
          constructed: false,
          capture: "keyOid"
        },
        {
          name: "AlgorithmIdentifier.parameters",
          captureAsn1: "keyParams"
        }
      ]
    },
    {
      name: "SubjectPublicKeyInfo.subjectPublicKey",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.BITSTRING,
      constructed: false,
      capture: "keyValue"
    }
  ]
};
// Adapted from digitalbazaar/node-forge/x509.js
var X509CertificateValidator = {
  name: "Certificate",
  tagClass: forge.asn1.Class.UNIVERSAL,
  type: forge.asn1.Type.SEQUENCE,
  constructed: true,
  value: [
    {
      name: "Certificate.TBSCertificate",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.SEQUENCE,
      constructed: true,
      captureAsn1: "certificate",
      value: [
        {
          name: "Certificate.TBSCertificate.version",
          tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
          type: 0,
          constructed: true,
          optional: true,
          value: [
            {
              name: "Certificate.TBSCertificate.version.integer",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.INTEGER,
              constructed: false,
              capture: "certVersion"
            }
          ]
        },
        {
          name: "Certificate.TBSCertificate.serialNumber",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.INTEGER,
          constructed: false,
          capture: "certSerialNumber"
        },
        {
          name: "Certificate.TBSCertificate.signature",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.SEQUENCE,
          constructed: true,
          value: [
            {
              name: "Certificate.TBSCertificate.signature.algorithm",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.OID,
              constructed: false,
              capture: "certSignatureOid"
            }, {
              name: "Certificate.TBSCertificate.signature.parameters",
              tagClass: forge.asn1.Class.UNIVERSAL,
              optional: true,
              captureAsn1: "certSignatureParams"
            }
          ]
        },
        {
          name: "Certificate.TBSCertificate.issuer",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.SEQUENCE,
          constructed: true,
          captureAsn1: "certIssuer"
        },
        {
          name: "Certificate.TBSCertificate.validity",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.SEQUENCE,
          constructed: true,
          // Note: UTC and generalized times may both appear so the capture
          // names are based on their detected order, the names used below
          // are only for the common case, which validity time really means
          // "notBefore" and which means "notAfter" will be determined by order
          value: [
            {
              // notBefore (Time) (UTC time case)
              name: "Certificate.TBSCertificate.validity.notBefore (utc)",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.UTCTIME,
              constructed: false,
              optional: true,
              capture: "certValidity1UTCTime"
            },
            {
              // notBefore (Time) (generalized time case)
              name: "Certificate.TBSCertificate.validity.notBefore (generalized)",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.GENERALIZEDTIME,
              constructed: false,
              optional: true,
              capture: "certValidity2GeneralizedTime"
            },
            {
              // notAfter (Time) (only UTC time is supported)
              name: "Certificate.TBSCertificate.validity.notAfter (utc)",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.UTCTIME,
              constructed: false,
              optional: true,
              capture: "certValidity3UTCTime"
            },
            {
              // notAfter (Time) (only UTC time is supported)
              name: "Certificate.TBSCertificate.validity.notAfter (generalized)",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.GENERALIZEDTIME,
              constructed: false,
              optional: true,
              capture: "certValidity4GeneralizedTime"
            }
          ]
        }, {
          // Name (subject) (RDNSequence)
          name: "Certificate.TBSCertificate.subject",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.SEQUENCE,
          constructed: true,
          captureAsn1: "certSubject"
        },
        // SubjectPublicKeyInfo
        publicKeyValidator,
        {
          // issuerUniqueID (optional)
          name: "Certificate.TBSCertificate.issuerUniqueID",
          tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
          type: 1,
          constructed: true,
          optional: true,
          value: [
            {
              name: "Certificate.TBSCertificate.issuerUniqueID.id",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.BITSTRING,
              constructed: false,
              capture: "certIssuerUniqueId"
            }
          ]
        },
        {
          // subjectUniqueID (optional)
          name: "Certificate.TBSCertificate.subjectUniqueID",
          tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
          type: 2,
          constructed: true,
          optional: true,
          value: [
            {
              name: "Certificate.TBSCertificate.subjectUniqueID.id",
              tagClass: forge.asn1.Class.UNIVERSAL,
              type: forge.asn1.Type.BITSTRING,
              constructed: false,
              capture: "certSubjectUniqueId"
            }
          ]
        },
        {
          // Extensions (optional)
          name: "Certificate.TBSCertificate.extensions",
          tagClass: forge.asn1.Class.CONTEXT_SPECIFIC,
          type: 3,
          constructed: true,
          captureAsn1: "certExtensions",
          optional: true
        }
      ]
    },
    {
      // AlgorithmIdentifier (signature algorithm)
      name: "Certificate.signatureAlgorithm",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.SEQUENCE,
      constructed: true,
      value: [
        {
          // algorithm
          name: "Certificate.signatureAlgorithm.algorithm",
          tagClass: forge.asn1.Class.UNIVERSAL,
          type: forge.asn1.Type.OID,
          constructed: false,
          capture: "certSignatureOid"
        },
        {
          name: "Certificate.TBSCertificate.signature.parameters",
          tagClass: forge.asn1.Class.UNIVERSAL,
          optional: true,
          captureAsn1: "certSignatureParams"
        }
      ]
    },
    {
      // SignatureValue
      name: "Certificate.signatureValue",
      tagClass: forge.asn1.Class.UNIVERSAL,
      type: forge.asn1.Type.BITSTRING,
      constructed: false,
      capture: "certSignature"
    }
  ]
};

var INTERNALS = {
  THUMBPRINT_KEY: "internal\u0000thumbprint",
  THUMBPRINT_HASH: "SHA-256"
};

module.exports = {
  validators: {
    privateKey: privateKeyValidator,
    publicKey: publicKeyValidator,
    certificate: X509CertificateValidator
  },

  thumbprint: function(cfg, json, hash) {
    if ("function" !== typeof cfg.thumbprint) {
      return Promise.reject(new Error("thumbprint not supported"));
    }

    hash = (hash || INTERNALS.THUMBPRINT_HASH).toUpperCase();
    var fields = cfg.thumbprint(json);
    var input = Object.keys(fields).
                sort().
                map(function(k) {
      var v = fields[k];
      if (Buffer.isBuffer(v)) {
        v = util.base64url.encode(v);
      }
      return JSON.stringify(k) + ":" + JSON.stringify(v);
    });
    input = "{" + input.join(",") + "}";
    try {
      return ALGORITHMS.digest(hash, new Buffer(input, "utf8"));
    } catch (err) {
      return Promise.reject(err);
    }
  },
  unpackProps: function(props, allowed) {
    var output;

    // apply all of the existing values
    allowed.forEach(function(cfg) {
      if (!(cfg.name in props)) {
        return;
      }
      output = output || {};
      var value = props[cfg.name];
      switch (cfg.type) {
        case "binary":
          if (Buffer.isBuffer(value)) {
            value = value;
            props[cfg.name] = util.base64url.encode(value);
          } else {
            value = util.base64url.decode(value);
          }
          break;
        case "string":
        case "number":
        case "boolean":
          value = value;
          break;
        case "array":
          value = [].concat(value);
          break;
        case "object":
          value = clone(value);
          break;
        default:
          // TODO: deep clone?
          value = value;
          break;
      }
      output[cfg.name] = value;
    });

    // remove any from json that didn't apply
    var check = output || {};
    Object.keys(props).
           forEach(function(n) {
              if (n in check) { return; }
              delete props[n];
           });

    return output;
  },
  COMMON_PROPS: [
    {name: "kty", type: "string"},
    {name: "kid", type: "string"},
    {name: "use", type: "string"},
    {name: "alg", type: "string"},
    {name: "x5c", type: "array"},
    {name: "x5t", type: "binary"},
    {name: "x5u", type: "string"},
    {name: "key_ops", type: "array"}
  ],
  INTERNALS: INTERNALS
};
