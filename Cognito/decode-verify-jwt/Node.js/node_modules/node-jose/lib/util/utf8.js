/*!
 * util/utf8.js - Implementation of UTF-8 Encoder/Decoder
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var utf8 = exports;

utf8.encode = function(input) {
  var output = encodeURIComponent(input || "");
  output = output.replace(/\%([0-9a-fA-F]{2})/g, function(m, code) {
    code = parseInt(code, 16);
    return String.fromCharCode(code);
  });

  return output;
};
utf8.decode = function(input) {
  var output = (input || "").replace(/[\u0080-\u00ff]/g, function(m) {
    var code = (0x100 | m.charCodeAt(0)).toString(16).substring(1);
    return "%" + code;
  });
  output = decodeURIComponent(output);

  return output;
};
