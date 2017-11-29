/*!
 * jwk/index.js - JSON Web Key (JWK) Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var JWKStore = require("./keystore.js");

// Public API -- Key and KeyStore methods
Object.keys(JWKStore.KeyStore).forEach(function(name) {
  exports[name] = JWKStore.KeyStore[name];
});

// Public API -- constants
var CONSTANTS = require("./constants.js");
Object.keys(CONSTANTS).forEach(function(name) {
  exports[name] = CONSTANTS[name];
});

// Registered Key Types
require("./octkey.js");
require("./rsakey.js");
require("./eckey.js");
