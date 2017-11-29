/*!
 * jws/helpers.js - JWS Internal Helper Functions
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

module.exports = {
  slice: function(input, start) {
    return Array.prototype.slice.call(input, start || 0);
  }
};
