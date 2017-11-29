/*!
 * util/index.js - Utilities Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js");

var util;

function asBuffer(input, encoding) {
  if (Buffer.isBuffer(input)) {
    return input;
  }

  if ("string" === typeof input) {
    encoding = encoding || "binary";
    if ("base64url" === encoding) {
      return util.base64url.decode(input);
    }
    return new Buffer(input, encoding);
  }

  // assume input is an Array, ArrayBuffer, or ArrayBufferView
  if (forge.util.isArrayBufferView(input)) {
    input = (input instanceof Uint8Array) ?
            input :
            new Uint8Array(input.buffer, input.byteOffset, input.byteOffset + input.byteLength);
  } else if (forge.util.isArrayBuffer(input)) {
    input = new Uint8Array(input);
  }

  var output;
  output = new Buffer(input);

  return output;
}

function randomBytes(len) {
  return new Buffer(forge.random.getBytes(len), "binary");
}

util = {
  base64url: require("./base64url.js"),
  utf8: require("./utf8.js"),
  asBuffer: asBuffer,
  randomBytes: randomBytes
};
module.exports = util;
