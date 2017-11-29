/*!
 * deps/ciphermodes/gcm/index.js - AES-GCM implementation Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
 "use strict";

var Long = require("long"),
    forge = require("../../../deps/forge.js"),
    multipliers = require("./multipliers.js"),
    helpers = require("./helpers.js"),
    pack = require("../pack.js"),
    DataBuffer = require("../../../util/databuffer.js"),
    cipherHelpers = require("../helpers.js");

var BLOCK_SIZE = 16;

// ### GCM Mode
// ### Constructor
function Gcm(options) {
  options = options || {};

  this.name = "GCM";
  this.cipher = options.cipher;
  this.blockSize = this.blockSize || 16;
}

// ### exports
module.exports = {
  createCipher: function(options) {
    var alg = new forge.aes.Algorithm("AES-GCM", Gcm);
    alg.initialize({
      key: new DataBuffer(options.key)
    });
    alg.mode.start(options);

    return alg.mode;
  },
  createDecipher: function(options) {
    var alg = new forge.aes.Algorithm("AES-GCM", Gcm);
    alg.initialize({
      key: new DataBuffer(options.key)
    });
    alg.mode._decrypt = true;
    alg.mode.start(options);

    return alg.mode;
  }
};

// ### Public API
Gcm.prototype.start = function(options) {
  this.tag = null;

  options = options || {};

  if (!("iv" in options)) {
    throw new Error("Gcm needs ParametersWithIV or AEADParameters");
  }
  this.nonce = options.iv;
  if (this.nonce == null || this.nonce.length < 1) {
    throw new Error("IV must be at least 1 byte");
  }

  // TODO: variable tagLength?
  this.tagLength = 16;

  // TODO: validate tag
  if ("tag" in options) {
    this.tag = new Buffer(options.tag);
  }

  var bufLength = !this._decrypt ?
                  this.blockSize :
                  (this.blockSize + this.tagLength);
  this.bufBlock = new Buffer(bufLength);
  this.bufBlock.fill(0);

  var multiplier = options.multiplier;
  if (multiplier == null) {
    multiplier = new (multipliers["8k"])();
  }
  this.multiplier = multiplier;

  this.H = this.zeroBlock();
  cipherHelpers.encrypt(this.cipher, this.H, 0, this.H, 0);

  // GcmMultiplier tables don"t change unless the key changes
  // (and are expensive to init)
  this.multiplier.init(this.H);
  this.exp = null;

  this.J0 = this.zeroBlock();

  if (this.nonce.length === 12) {
    this.nonce.copy(this.J0, 0, 0, this.nonce.length);
    this.J0[this.blockSize - 1] = 0x01;
  } else {
    this.gHASH(this.J0, this.nonce, this.nonce.length);
    var X = this.zeroBlock();
    pack.longToBigEndian(new Long(this.nonce.length).
                         multiply(8), X, 8);
    this.gHASHBlock(this.J0, X);
  }

  this.S = this.zeroBlock();
  this.SAt = this.zeroBlock();
  this.SAtPre = this.zeroBlock();
  this.atBlock = this.zeroBlock();
  this.atBlockPos = 0;
  this.atLength = Long.ZERO;
  this.atLengthPre = Long.ZERO;
  this.counter = new Buffer(this.J0);
  this.bufOff = 0;
  this.totalLength = Long.ZERO;

  if ("additionalData" in options) {
    this.processAADBytes(options.additionalData, 0, options.additionalData.length);
  }
};

Gcm.prototype.update = function(inV, inOff, len, out, outOff) {
  var resultLen = 0;

  while (len > 0) {
    var inLen = Math.min(len, this.bufBlock.length - this.bufOff);
    inV.copy(this.bufBlock, this.bufOff, inOff, inOff + inLen);
    len -= inLen;
    inOff += inLen;
    this.bufOff += inLen;
    if (this.bufOff === this.bufBlock.length) {
      this.outputBlock(out, outOff + resultLen);
      resultLen += this.blockSize;
    }
  }

  return resultLen;
};
Gcm.prototype.finish = function(out, outOff) {
  var resultLen = 0;

  if (this._decrypt) {
    // append tag
    resultLen += this.update(this.tag, 0, this.tag.length, out, outOff);
  }

  if (this.totalLength.isZero()) {
    this.initCipher();
  }

  var extra = this.bufOff;
  if (this._decrypt) {
    if (extra < this.tagLength) {
      throw new Error("data too short");
    }
    extra -= this.tagLength;
  }

  if (extra > 0) {
    this.gCTRPartial(this.bufBlock, 0, extra, out, outOff + resultLen);
    resultLen += extra;
  }

  this.atLength = this.atLength.add(this.atBlockPos);

  // Final gHASH
  var X = this.zeroBlock();
  pack.longToBigEndian(this.atLength.multiply(8),
                       X,
                       0);
  pack.longToBigEndian(this.totalLength.multiply(8),
                       X,
                       8);

  this.gHASHBlock(this.S, X);

  // TODO Fix this if tagLength becomes configurable
  // T = MSBt(GCTRk(J0,S))
  var tag = new Buffer(this.blockSize);
  tag.fill(0);
  cipherHelpers.encrypt(this.cipher, this.J0, 0, tag, 0);
  this.xor(tag, this.S);

  if (this._decrypt) {
    if (!helpers.arrayEqual(this.tag, tag)) {
      throw new Error("mac check in Gcm failed");
    }
  } else {
    // We place into tag our calculated value for T
    this.tag = new Buffer(this.tagLength);
    tag.copy(this.tag, 0, 0, this.tagLength);
  }

  return resultLen;
};

// ### "Internal" Helper Functions
Gcm.prototype.initCipher = function() {
  if (this.atLength.greaterThan(Long.ZERO)) {
    this.SAt.copy(this.SAtPre, 0, 0, this.blockSize);
    this.atLengthPre = this.atLength.add(Long.ZERO);
  }

  // Finish hash for partial AAD block
  if (this.atBlockPos > 0) {
    this.gHASHPartial(this.SAtPre, this.atBlock, 0, this.atBlockPos);
    this.atLengthPre = this.atLengthPre.add(this.atBlockPos);
  }

  if (this.atLengthPre.greaterThan(Long.ZERO)) {
    this.SAtPre.copy(this.S, 0, 0, this.blockSize);
  }
};

Gcm.prototype.outputBlock = function(output, offset) {
  if (this.totalLength.isZero()) {
    this.initCipher();
  }
  this.gCTRBlock(this.bufBlock, output, offset);
  if (!this._decrypt) {
    this.bufOff = 0;
  } else {
    this.bufBlock.copy(this.bufBlock, 0, this.blockSize, this.blockSize + this.tagLength);
    this.bufOff = this.tagLength;
  }
};

Gcm.prototype.processAADBytes = function(inV, inOff, len) {
  for (var i = 0; i < len; ++i) {
    this.atBlock[this.atBlockPos] = inV[inOff + i];
    if (++this.atBlockPos === this.blockSize) {
      // Hash each block as it fills
      this.gHASHBlock(this.SAt, this.atBlock);
      this.atBlockPos = 0;
      this.atLength = this.atLength.add(this.blockSize);
    }
  }
};

Gcm.prototype.getNextCounterBlock = function() {
  for (var i = 15; i >= 12; --i) {
    var b = ((this.counter[i] + 1) & 0xff);
    this.counter[i] = b;

    if (b !== 0) {
      break;
    }
  }

  // encrypt counter
  var outb = new Buffer(this.blockSize);
  outb.fill(0);
  cipherHelpers.encrypt(this.cipher, this.counter, 0, outb, 0);

  return outb;
};

Gcm.prototype.gCTRBlock = function(block, out, outOff) {
  var tmp = this.getNextCounterBlock();

  this.xor(tmp, block);
  tmp.copy(out, outOff, 0, this.blockSize);

  this.gHASHBlock(this.S, !this._decrypt ? tmp : block);

  this.totalLength = this.totalLength.add(this.blockSize);
};
Gcm.prototype.gCTRPartial = function(buf, off, len, out, outOff) {
  var tmp = this.getNextCounterBlock();

  this.xor(tmp, buf, off, len);
  tmp.copy(out, outOff, 0, len);

  this.gHASHPartial(this.S, !this._decrypt ? tmp : buf, 0, len);

  this.totalLength = this.totalLength.add(len);
};

Gcm.prototype.gHASHBlock = function(Y, b) {
  this.xor(Y, b);
  this.multiplier.multiplyH(Y);
};
Gcm.prototype.gHASHPartial = function(Y, b, off, len) {
  this.xor(Y, b, off, len);
  this.multiplier.multiplyH(Y);
};

Gcm.prototype.xor = function(block, val, off, len) {
  switch (arguments.length) {
    case 2:
      for (var i = 15; i >= 0; --i) {
        block[i] ^= val[i];
      }
      break;
    case 4:
      while (len-- > 0) {
        block[len] ^= val[off + len];
      }
      break;
    default:
      throw new TypeError("Expected 2 or 4 arguments.");
  }

  return block;
};

Gcm.prototype.zeroBlock = function() {
  var block = new Buffer(BLOCK_SIZE);
  block.fill(0);
  return block;
};
