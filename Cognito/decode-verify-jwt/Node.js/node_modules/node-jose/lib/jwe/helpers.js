/*!
 * jwe/helpers.js - JWE Internal Helper Functions
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var CONSTANTS = require("../algorithms/constants"),
    JWK = require("../jwk");

module.exports = {
  slice: function(input, start) {
    return Array.prototype.slice.call(input, start || 0);
  },
  generateCEK: function(enc) {
    var ks = JWK.createKeyStore();
    var len = CONSTANTS.KEYLENGTH[enc];

    if (len) {
        return ks.generate("oct", len);
    }

    throw new Error("unsupported encryption algorithm");
  }
};
