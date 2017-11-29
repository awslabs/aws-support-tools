/*!
 * jws/defaults.js - Defaults for JWSs
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

/**
 * @description
 * The default options for {@link JWS.createSign}.
 *
 * @property {Boolean} compact Determines if the output is the Compact
 *           serialization (`true`) or the JSON serialization (**`false`**,
 *           the default).
 * @property {String|String[]} protect The names of the headers to integrity
 *           protect.  The value `""` means that none of header parameters
 *           are integrity protected, while `"*"` (the default) means that all
 *           headers parameter sare integrity protected.
 */
var JWSDefaults = {
    compact: false,
    protect: "*"
};

module.exports = JWSDefaults;
