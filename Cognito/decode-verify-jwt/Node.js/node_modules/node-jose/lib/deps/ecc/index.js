/**
 * deps/ecc/index.js - Elliptic Curve Entry Point
 *
 * Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 */
"use strict";

var forge = require("../../deps/forge"),
    BigInteger = forge.jsbn.BigInteger,
    ec = require("./math.js"),
    CURVES = require("./curves.js");

// ### Helpers
function hex2bn(s) {
  return new BigInteger(s, 16);
}

function bn2bin(bn, len) {
  if (!len) {
    len = Math.ceil(bn.bitLength() / 8);
  }
  len = len * 2;

  var hex = bn.toString(16);
  // truncate-left if too large
  hex = hex.substring(Math.max(hex.length - len, 0));
  // pad-left if too small
  while (len > hex.length) {
    hex = "0" + hex;
  }

  return new Buffer(hex, "hex");
}
function bin2bn(s) {
  if ("string" === typeof s) {
    s = new Buffer(s, "binary");
  }
  return hex2bn(s.toString("hex"));
}

function keySizeBytes(params) {
  return Math.ceil(params.getN().bitLength() / 8);
}

function namedCurve(curve) {
  var params = CURVES[curve];
  if (!params) {
    throw new TypeError("unsupported named curve: " + curve);
  }

  return params;
}

function normalizeEcdsa(params, md) {
  var log2n = params.getN().bitLength(),
      mdLen = md.length * 8;

  var e = bin2bn(md);
  if (log2n < mdLen) {
    e = e.shiftRight(mdLen - log2n);
  }

  return e;
}

// ### EC Public Key

/**
 *
 * @param {String} curve The named curve
 * @param {BigInteger} x The X coordinate
 * @param {BigInteger} y The Y coordinate
 */
function ECPublicKey(curve, x, y) {
  var params = namedCurve(curve),
      c = params.getCurve();
  var key = new ec.ECPointFp(c,
                             c.fromBigInteger(x),
                             c.fromBigInteger(y));

  this.curve = curve;
  this.params = params;
  this.point = key;

  var size = keySizeBytes(params);
  this.x = bn2bin(x, size);
  this.y = bn2bin(y, size);
}

// basics
ECPublicKey.prototype.isValid = function() {
  return this.params.curve.contains(this.point);
}

// ECDSA
ECPublicKey.prototype.verify = function(md, sig) {
  var N = this.params.getN(),
      G = this.params.getG();

  // prepare and validate (r, s)
  var r = bin2bn(sig.r),
      s = bin2bn(sig.s);
  if (r.compareTo(BigInteger.ONE) < 0 || r.compareTo(N) >= 0) {
    return false;
  }
  if (s.compareTo(BigInteger.ONE) < 0 || r.compareTo(N) >= 0) {
    return false;
  }

  // normalize input
  var e = normalizeEcdsa(this.params, md);
  // verify (r, s)
  var w = s.modInverse(N),
      u1 = e.multiply(w).mod(N),
      u2 = r.multiply(w).mod(N);

  var v = G.multiplyTwo(u1, this.point, u2).getX().toBigInteger();
  v = v.mod(N);

  return v.equals(r);
};

// ### EC Private Key

/**
 * @param {String} curve The named curve
 * @param {Buffer} key The private key value
 */
function ECPrivateKey(curve, key) {
  var params = namedCurve(curve);
  this.curve = curve;
  this.params = params;

  var size = keySizeBytes(params);
  this.d = bn2bin(key, size);
}

ECPrivateKey.prototype.toPublicKey = function() {
  var d = bin2bn(this.d);
  var P = this.params.getG().multiply(d);
  return new ECPublicKey(this.curve,
                         P.getX().toBigInteger(),
                         P.getY().toBigInteger());
};

// ECDSA
ECPrivateKey.prototype.sign = function(md) {
  var keysize = keySizeBytes(this.params),
      N = this.params.getN(),
      G = this.params.getG(),
      e = normalizeEcdsa(this.params, md),
      d = bin2bn(this.d);

  var r, s;
  var k, x1, z;
  do {
    do {
      // determine random nonce
      do {
        k = bin2bn(forge.random.getBytes(keysize));
      } while (k.equals(BigInteger.ZERO) || k.compareTo(N) >= 0);
      // (x1, y1) = k * G
      x1 = G.multiply(k).getX().toBigInteger();
      // r = x1 mod N
      r = x1.mod(N);
    } while (r.equals(BigInteger.ZERO));
    // s = (k^-1 * (e + r * d)) mod N
    z = d.multiply(r);
    z = e.add(z);
    s = k.modInverse(N).multiply(z).mod(N);
  } while (s.equals(BigInteger.ONE));

  // convert (r, s) to bytes
  var len = keySizeBytes(this.params);
  r = bn2bin(r, len);
  s = bn2bin(s, len);

  return {
    r: r,
    s: s
  };
};

// basics
ECPrivateKey.prototype.isValid = function() {
  var d = bin2bn(this.d),
      n1 = params.getN().subtract(BigIneger.ONE);

  return (d.compareTo(BigInteger.ONE) >= 0) &&
         (d.compareTo(n1) < 0);
}

// ECDH
ECPrivateKey.prototype.computeSecret = function(pubkey) {
  var d = bin2bn(this.d);
  var S = pubkey.point.multiply(d).getX().toBigInteger();
  S = bn2bin(S, keySizeBytes(this.params));
  return S;
};

// ### Public API
exports.generateKeyPair = function(curve) {
  var params = namedCurve(curve),
      n = params.getN();

  // generate random within range [1, N-1)
  var r = forge.random.getBytes(keySizeBytes(params));
  r = bin2bn(r);

  var n1 = n.subtract(BigInteger.ONE);
  var d = r.mod(n1).add(BigInteger.ONE);

  var privkey = new ECPrivateKey(curve, d),
      pubkey = privkey.toPublicKey();

  return {
    "private": privkey,
    "public": pubkey
  };
};

exports.asPublicKey = function(curve, x, y) {
  if ("string" === typeof x) {
    x = hex2bn(x);
  } else if (Buffer.isBuffer(x)) {
    x = bin2bn(x);
  }

  if ("string" === typeof y) {
    y = hex2bn(y);
  } else if (Buffer.isBuffer(y)) {
    y = bin2bn(y);
  }

  var pubkey = new ECPublicKey(curve, x, y);
  return pubkey;
};
exports.asPrivateKey = function(curve, d) {
  // Elaborate way to get to a Buffer from a (String|Buffer|BigInteger)
  if ("string" === typeof d) {
    d = hex2bn(d);
  } else if (Buffer.isBuffer(d)) {
    d = bin2bn(d);
  }

  var privkey = new ECPrivateKey(curve, d);
  return privkey;
};
