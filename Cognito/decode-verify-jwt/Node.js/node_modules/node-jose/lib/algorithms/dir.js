/*!
 * algorithms/dir.js - Direct key mode
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

function dirEncryptFN(key) {
  // NOTE: pdata unused
  // NOTE: props unused
  return Promise.resolve({
    data: key,
    once: true,
    direct: true
  });
}
function dirDecryptFN(key) {
  // NOTE: pdata unused
  // NOTE: props unused
  return Promise.resolve(key);
}

// ### Public API
// * [name].encrypt
// * [name].decrypt
var direct = {
  dir: {
    encrypt: dirEncryptFN,
    decrypt: dirDecryptFN
  }
};

module.exports = direct;
