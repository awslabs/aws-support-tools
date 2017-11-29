/*!
 * deps/ciphermodes/pack.js - Pack/Unpack Functions
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var Long = require("long");

var pack = module.exports = {
  intToBigEndian: function(n, bs, off) {
    if (typeof n === "number") {
      switch (arguments.length) {
        case 1:
          bs = new Buffer(4);
          bs.fill(0);
          pack.intToBigEndian(n, bs, 0);
          break;
        case 3:
          bs[off] = 0xff & (n >>> 24);
          bs[++off] = 0xff & (n >>> 16);
          bs[++off] = 0xff & (n >>> 8);
          bs[++off] = 0xff & (n);
          break;
        default:
          throw new TypeError("Expected 1 or 3 arguments.");
      }
    } else {
      switch (arguments.length) {
        case 1:
          bs = new Buffer(4 * n.length);
          bs.fill(0);
          pack.intToBigEndian(n, bs, 0);
          break;
        case 3:
          for (var i = 0; i < n.length; ++i) {
            pack.intToBigEndian(n[i], bs, off);
            off += 4;
          }
          break;
        default:
          throw new TypeError("Expected 1 or 3 arguments.");
      }
    }

    return bs;
  },
  longToBigEndian: function(n, bs, off) {
    if (!Array.isArray(n)) {
      // Single
      switch (arguments.length) {
        case 1:
          bs = new Buffer(8);
          bs.fill(0);
          pack.longToBigEndian(n, bs, 0);
          break;
        case 3:
          var lo = n.low,
              hi = n.high;
          pack.intToBigEndian(hi, bs, off);
          pack.intToBigEndian(lo, bs, off + 4);
          break;
        default:
          throw new TypeError("Expected 1 or 3 arguments.");
      }
    } else {
      // Array
      switch (arguments.length) {
        case 1:
          bs = new Buffer(8 * n.length);
          bs.fill(0);
          pack.longToBigEndian(n, bs, 0);
          break;
        case 3:
          for (var i = 0; i < n.length; ++i) {
            pack.longToBigEndian(n[i], bs, off);
            off += 8;
          }
          break;
        default:
          throw new TypeError("Expected 1 or 3 arguments.");
      }
    }

    return bs;
  },

  bigEndianToInt: function(bs, off, ns) {
    switch (arguments.length) {
      case 2:
        var n = bs[off] << 24;
        n |= (bs[++off] & 0xff) << 16;
        n |= (bs[++off] & 0xff) << 8;
        n |= (bs[++off] & 0xff);
        return n;
      case 3:
        for (var i = 0; i < ns.length; ++i) {
          ns[i] = pack.bigEndianToInt(bs, off);
          off += 4;
        }
        break;
      default:
        throw new TypeError("Expected 2 or 3 arguments.");
    }
  },
  bigEndianToLong: function(bs, off, ns) {
    switch (arguments.length) {
      case 2:
        var hi = pack.bigEndianToInt(bs, off);
        var lo = pack.bigEndianToInt(bs, off + 4);
        var num = new Long(lo, hi);
        return num;
      case 3:
        for (var i = 0; i < ns.length; ++i) {
          ns[i] = pack.bigEndianToLong(bs, off);
          off += 8;
        }
        break;
      default:
        throw new TypeError("Expected 2 or 3 arguments.");
    }
  }
};
