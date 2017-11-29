/*!
 * jwe/defaults.js - Defaults for JWEs
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

/**
 * @description
 * The default options for {@link JWE.createEncrypt}.
 *
 * @property {Boolean|String} zip Determines the compression algorithm to
 *           apply to the plaintext (if any) before it is encrypted. This can
 *           also be `true` (which is equivalent to `"DEF"`) or **`false`**
 *           (the default, which is equivalent to no compression).
 * @property {String} format Determines the serialization format of the
 *           output.  Expected to be `"general"` for general JSON
 *           Serialization, `"flattened"` for flattened JSON Serialization,
 *           or `"compact"` for Compact Serialization (default is
 *           **`"general"`**).
 * @property {Boolean} compact Determines if the output is the Compact
 *           serialization (`true`) or the JSON serialization (**`false`**,
 *           the default).
 * @property {String} contentAlg The algorithm used to encrypt the plaintext
 *           (default is **`"A128CBC-HS256"`**).
 * @property {String|String[]} protect The names of the headers to integrity
 *           protect.  The value `""` means that none of the header parameters
 *           are integrity protected, while `"*"` (the default) means that all
 *           header parameters are integrity protected.
 */
var JWEDefaults = {
  zip: false,
  format: "general",
  contentAlg: "A128CBC-HS256",
  protect: "*"
};

module.exports = JWEDefaults;
