/*!
 * util/utf8.js - Implementation of UTF-8 Encoder/Decoder
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var partialRight = require("lodash.partialright"),
    merge = require("lodash.merge");

var typedArrayCtors = (function() {
  var ctors = [];
  if ("undefined" !== typeof Uint8ClampedArray) {
    ctors.push(Uint8ClampedArray);
  }
  if ("undefined" !== typeof Uint8Array) {
    ctors.push(Uint8Array);
  }
  if ("undefined" !== typeof Uint16Array) {
    ctors.push(Uint16Array);
  }
  if ("undefined" !== typeof Uint32Array) {
    ctors.push(Uint32Array);
  }
  if ("undefined" !== typeof Float32Array) {
    ctors.push(Float32Array);
  }
  if ("undefined" !== typeof Float64Array) {
    ctors.push(Float64Array);
  }
  return ctors;
})();

function findTypedArrayFor(ta) {
  var ctor;
  for (var idx = 0; !ctor && typedArrayCtors.length > idx; idx++) {
    if (ta instanceof typedArrayCtors[idx]) {
      ctor = typedArrayCtors[idx];
    }
  }
  return ctor;
}

function mergeBuffer(a, b) {
  // TODO: should this be a copy, or the reference itself?
  if (Buffer.isBuffer(b)) {
    b = new Buffer(b);
  } else {
    var Ctor = findTypedArrayFor(b);
    b = Ctor ?
        new Ctor(b, b.byteOffset, b.byteLength) :
        undefined;
  }

  // TODO: QUESTION: create a merged <whatever-a-is>??
  // for now, a is b
  a = b;

  return b;
}

module.exports = partialRight(merge, mergeBuffer);
