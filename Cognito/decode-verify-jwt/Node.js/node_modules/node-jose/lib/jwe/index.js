/*!
 * jwe/index.js - JSON Web Encryption (JWE) Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var JWE = {
  createEncrypt: require("./encrypt").createEncrypt,
  createDecrypt: require("./decrypt").createDecrypt
};

module.exports = JWE;
