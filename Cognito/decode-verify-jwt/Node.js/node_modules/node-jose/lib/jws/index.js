/*!
 * jws/index.js - JSON Web Signature (JWS) Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var JWS = {
  createSign: require("./sign").createSign,
  createVerify: require("./verify").createVerify
};

module.exports = JWS;
