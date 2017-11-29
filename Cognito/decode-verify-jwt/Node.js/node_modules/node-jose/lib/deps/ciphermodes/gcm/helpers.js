/*!
 * deps/ciphermodes/gcm/helpers.js - AES-GCM Helper Functions
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var Long = require("long"),
    fill = require("lodash.fill"),
    pack = require("../pack.js");

var E1 = 0xe1000000,
    E1B = 0xe1,
    E1L = new Long(E1 >> 8);

function generateLookup() {
  var lookup = [];

  for (var c = 0; c < 256; ++c) {
    var v = 0;
    for (var i = 7; i >= 0; --i) {
      if ((c & (1 << i)) !== 0) {
        v ^= (E1 >>> (7 - i));
      }
    }
    lookup.push(v);
  }

  return lookup;
}

var helpers = module.exports = {
  // ### Constants
  E1: E1,
  E1B: E1B,
  E1L: E1L,
  LOOKUP: generateLookup(),

  // ### Array Helpers
  arrayCopy: function(src, srcPos, dest, destPos, length) {
    // Start by checking for negatives since arrays in JS auto-expand
    if (srcPos < 0 || destPos < 0 || length < 0) {
      throw new TypeError("Invalid input.");
    }

    if (dest instanceof Uint8Array) {
      // Check for overflow if dest is a typed-array
      if (destPos >= dest.length || (destPos + length) > dest.length) {
        throw new TypeError("Invalid input.");
      }

      if (srcPos !== 0 || length < src.length) {
        if (src instanceof Uint8Array) {
          src = src.subarray(srcPos, srcPos + length);
        } else {
          src = src.slice(srcPos, srcPos + length);
        }
      }

      dest.set(src, destPos);
    } else {
      for (var i = 0; i < length; ++i) {
        dest[destPos + i] = src[srcPos + i];
      }
    }
  },
  arrayEqual: function(a1, a2) {
    a1 = a1 || [];
    a2 = a2 || [];

    var len = Math.min(a1.length, a2.length),
        result = (a1.length === a2.length);

    for (var idx = 0; idx < len; idx++) {
      result = result &&
               ("undefined" !== typeof a1[idx]) &&
               ("undefined" !== typeof a2[idx]) &&
               (a1[idx] === a2[idx]);
    }

    return result;
  },

  // ### Conversions
  asBytes: function(x, z) {
    switch (arguments.length) {
      case 1:
        z = new Buffer(16);
        z.fill(0);
        pack.intToBigEndian(x, z, 0);
        return z;
      case 2:
        pack.intToBigEndian(x, z, 0);
        break;
      default:
        throw new TypeError("Expected 1 or 2 arguments.");
    }
  },
  asInts: function(x, z) {
    switch (arguments.length) {
      case 1:
        z = [];
        fill(z, 0, 0, 4);
        pack.bigEndianToInt(x, 0, z);
        return z;
      case 2:
        pack.bigEndianToInt(x, 0, z);
        break;
      default:
        throw new TypeError("Expected 1 or 2 arguments.");
    }
  },
  oneAsInts: function() {
    var tmp = [];
    for (var c = 0; c < 4; ++c) {
        tmp.push(1 << 31);
    }
    return tmp;
  },

  // ## Bit-wise
  shiftRight: function(x, z) {
    var b, c;
    switch (arguments.length) {
      case 1:
        b = x[0];
        x[0] = b >>> 1;
        c = b << 31;
        b = x[1];
        x[1] = (b >>> 1) | c;
        c = b << 31;
        b = x[2];
        x[2] = (b >>> 1) | c;
        c = b << 31;
        b = x[3];
        x[3] = (b >>> 1) | c;
        return (b << 31) & 0xffffffff;
      case 2:
        b = x[0];
        z[0] = b >>> 1;
        c = b << 31;
        b = x[1];
        z[1] = (b >>> 1) | c;
        c = b << 31;
        b = x[2];
        z[2] = (b >>> 1) | c;
        c = b << 31;
        b = x[3];
        z[3] = (b >>> 1) | c;
        return (b << 31) & 0xffffffff;
      default:
        throw new TypeError("Expected 1 or 2 arguments.");
    }
  },
  shiftRightN: function(x, n, z) {
    var nInv, b, c;
    switch (arguments.length) {
      case 2:
        b = x[0];
        nInv = 32 - n;
        x[0] = b >>> n;
        c = b << nInv;
        b = x[1];
        x[1] = (b >>> n) | c;
        c = b << nInv;
        b = x[2];
        x[2] = (b >>> n) | c;
        c = b << nInv;
        b = x[3];
        x[3] = (b >>> n) | c;
        return b << nInv;
      case 3:
        b = x[0];
        nInv = 32 - n;
        z[0] = b >>> n;
        c = b << nInv;
        b = x[1];
        z[1] = (b >>> n) | c;
        c = b << nInv;
        b = x[2];
        z[2] = (b >>> n) | c;
        c = b << nInv;
        b = x[3];
        z[3] = (b >>> n) | c;
        return b << nInv;
      default:
        throw new TypeError("Expected 2 or 3 arguments.");
    }
  },
  xor: function(x, y, z) {
    switch (arguments.length) {
      case 2:
        x[0] ^= y[0];
        x[1] ^= y[1];
        x[2] ^= y[2];
        x[3] ^= y[3];
        break;
      case 3:
        z[0] = x[0] ^ y[0];
        z[1] = x[1] ^ y[1];
        z[2] = x[2] ^ y[2];
        z[3] = x[3] ^ y[3];
        break;
      default:
        throw new TypeError("Expected 2 or 3 arguments.");
    }
  },

  multiply: function(x, y) {
    var r0 = x.slice();
    var r1 = [];

    for (var i = 0; i < 4; ++i) {
      var bits = y[i];
      for (var j = 31; j >= 0; --j) {
        if ((bits & (1 << j)) !== 0) {
          helpers.xor(r1, r0);
        }

        if (helpers.shiftRight(r0) !== 0) {
          r0[0] ^= helpers.E1;
        }
      }
    }

    helpers.arrayCopy(r1, 0, x, 0, 4);
  },
  multiplyP: function(x, y) {
    switch (arguments.length) {
      case 1:
        if (helpers.shiftRight(x) !== 0) {
          x[0] ^= helpers.E1;
        }
        break;
      case 2:
        if (helpers.shiftRight(x, y) !== 0) {
          y[0] ^= helpers.E1;
        }
        break;
      default:
        throw new TypeError("Expected 1 or 2 arguments.");
    }
  },
  multiplyP8: function(x, y) {
    var c;
    switch (arguments.length) {
      case 1:
        c = helpers.shiftRightN(x, 8);
        x[0] ^= helpers.LOOKUP[c >>> 24];
        break;
      case 2:
        c = helpers.shiftRightN(x, 8, y);
        y[0] ^= helpers.LOOKUP[c >>> 24];
        break;
      default:
        throw new TypeError("Expected 1 or 2 arguments.");
    }
  }
};
