/*!
 * deps/ciphermodes/helpers.js - Cipher Helper Functions
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var pack = require("./pack.js");

function doEncrypt(cipher, inb, inOff, outb, outOff) {
  var input = new Array(4),
      output = new Array(4);

  pack.bigEndianToInt(inb, inOff, input);
  cipher.encrypt(input, output);
  pack.intToBigEndian(output, outb, outOff);
}

module.exports = {
  encrypt: doEncrypt
};
