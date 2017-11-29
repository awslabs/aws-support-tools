/*!
 * deps/ciphermodes/gcm/multipliers.js - AES-GCM Multipliers
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
 "use strict";

var helpers = require("./helpers.js"),
    pack = require("../pack.js");


// ### 8K Table Multiplier
function Gcm8KMultiplier() {
  this.H = [];
  this.M = null;
}

Gcm8KMultiplier.prototype.init = function(H) {
  var i, j, k;
  if (this.M == null) {
    // sc: I realize this UGLY...
    //M = new int[32][16][4];
    this.M = [];
    for (i = 0; i < 32; ++i) {
      this.M[i] = [];
      for (j = 0; j < 16; ++j) {
        this.M[i][j] = [];
        for (k = 0; k < 4; ++k) {
          this.M[i][j][k] = 0;
        }
      }
    }
  } else if (helpers.arrayEqual(this.H, H)) {
    return;
  }

  this.H = H.slice();

  // M[0][0] is ZEROES;
  // M[1][0] is ZEROES;
  helpers.asInts(H, this.M[1][8]);

  for (j = 4; j >= 1; j >>= 1) {
    helpers.multiplyP(this.M[1][j + j], this.M[1][j]);
  }
  helpers.multiplyP(this.M[1][1], this.M[0][8]);

  for (j = 4; j >= 1; j >>= 1) {
    helpers.multiplyP(this.M[0][j + j], this.M[0][j]);
  }

  i = 0;
  for (;;) {
    for (j = 2; j < 16; j += j) {
      for (k = 1; k < j; ++k) {
        helpers.xor(this.M[i][j], this.M[i][k], this.M[i][j + k]);
      }
    }

    if (++i === 32) {
      return;
    }

    if (i > 1) {
      // M[i][0] is ZEROES;
      for (j = 8; j > 0; j >>= 1) {
        helpers.multiplyP8(this.M[i - 2][j], this.M[i][j]);
      }
    }
  }
};
Gcm8KMultiplier.prototype.multiplyH = function(x) {
  var z = [];
  for (var i = 15; i >= 0; --i) {
    var m = this.M[i + i][x[i] & 0x0f];
    z[0] ^= m[0];
    z[1] ^= m[1];
    z[2] ^= m[2];
    z[3] ^= m[3];
    m = this.M[i + i + 1][(x[i] & 0xf0) >>> 4];
    z[0] ^= m[0];
    z[1] ^= m[1];
    z[2] ^= m[2];
    z[3] ^= m[3];
  }

  pack.intToBigEndian(z, x, 0);
};


module.exports = {
  "8k": Gcm8KMultiplier
};
