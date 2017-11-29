/*!
 * parse/compact.js - JOSE JSON Serialization Parser
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var merge = require("../util/merge");

var jose = {
  JWE: require("../jwe"),
  JWS: require("../jws"),
  util: require("../util")
};

function parseJSON(input) {
  var type,
      op,
      headers;

  if ("signatures" in input || "signature" in input) {
    // JWS
    type = "JWS";
    op = function(ks) {
      return jose.JWS.createVerify(ks).
             verify(input);
    };
    // headers can be (signatures[].protected, signatures[].header, signature.protected, signature.header)
    headers = input.signatures ||
              [ {
                protected: input.protected,
                header: input.header,
                signature: input.signature
              }];
    headers = headers.map(function(sig) {
      var all = {};
      if (sig.header) {
        all = merge(all, sig.header);
      }

      var prot;
      if (sig.protected) {
        prot = sig.protected;
        prot = jose.util.base64url.decode(prot, "utf8");
        prot = JSON.parse(prot);
        all = merge(all, prot);
      }

      return all;
    });
  } else if ("ciphertext" in input) {
    // JWE
    type = "JWE";
    op = function(ks) {
      return jose.JWE.createDecrypt(ks).
             decrypt(input);
    };
    // headers can be (protected, unprotected, recipients[].header)
    var root = {};
    if (input.protected) {
      root.protected = input.protected;
      root.protected = jose.util.base64url.decode(root.protected, "utf8");
      root.protected = JSON.parse(root.protected);
    }
    if (input.unprotected) {
      root.unprotected = input.unprotected;
    }

    headers = input.recipients || [{}];
    headers = headers.map(function(rcpt) {
      var all = {};
      if (rcpt.header) {
        all = merge(all, rcpt.header);
      }
      if (root.unprotected) {
        all = merge(all, root.unprotected);
      }
      if (root.protected) {
        all = merge(all, root.protected);
      }

      return all;
    });
  }

  return {
    type: type,
    format: "json",
    input: input,
    all: headers,
    perform: op
  };
}

module.exports = parseJSON;
