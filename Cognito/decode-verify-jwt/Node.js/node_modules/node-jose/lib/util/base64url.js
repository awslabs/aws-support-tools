/*!
 * util/base64url.js - Implementation of web-safe Base64 Encoder/Decoder
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var impl = require("base64url");

/**
 * @namespace base64url
 * @description
 * Provides methods to encode and decode data according to the
 * base64url alphabet.
 */
var base64url = {
  /**
   * @function
   * Encodes the input to base64url.
   *
   * If {input} is a Buffer, then {encoding} is ignored. Otherwise,
   * {encoding} can be one of "binary", "base64", "hex", "utf8".
   *
   * @param {Buffer|String} input The data to encode.
   * @param {String} [encoding = binary] The input encoding format.
   * @returns {String} the base64url encoding of {input}.
   */
  encode: function encode(buffer, encoding) {
    if (buffer instanceof ArrayBuffer) {
      buffer = new Uint8Array(buffer);
    }

    if (!Buffer.isBuffer(buffer)) {
      buffer = new Buffer(buffer, encoding);
    }

    return impl.encode(buffer);
  },
  /**
   * @function
   * Decodes the input from base64url.
   *
   * @param {String} input The data to decode.
   * @returns {Buffer|String} the base64url decoding of {input}.
   */
  decode: impl.toBuffer
};

module.exports = base64url;
