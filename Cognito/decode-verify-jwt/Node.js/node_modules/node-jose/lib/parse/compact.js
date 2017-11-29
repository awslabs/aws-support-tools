/*!
 * parse/compact.js - JOSE Compact Serialization Parser
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var jose = {
  JWE: require("../jwe"),
  JWS: require("../jws"),
  util: require("../util")
};

function parseCompact(input) {
  var parts = input.split(".");

  var type,
      op;
  if (3 === parts.length) {
    // JWS
    type = "JWS";
    op = function(ks) {
      return jose.JWS.createVerify(ks).
             verify(input);
    };
  } else if (5 === parts.length) {
    // JWE
    type = "JWE";
    op = function(ks) {
      return jose.JWE.createDecrypt(ks).
             decrypt(input);
    };
  } else {
    throw new TypeError("invalid jose serialization");
  }

  // parse header
  var header;
  header = jose.util.base64url.decode(parts[0], "utf8");
  header = JSON.parse(header);
  return {
    type: type,
    format: "compact",
    input: input,
    header: header,
    perform: op
  };
}

module.exports = parseCompact;
