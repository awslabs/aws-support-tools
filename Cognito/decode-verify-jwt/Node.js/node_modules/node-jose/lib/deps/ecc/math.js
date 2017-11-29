/**
 * deps/ecc/math.js - Elliptic Curve Math
 * Original Copyright (c) 2003-2005  Tom Wu.
 * Modifications Copyright (c) 2015 Cisco Systems, Inc.  See LICENSE file.
 *
 * Ported from Tom Wu, which is ported from BouncyCastle
 * Modified to reuse existing external NPM modules, restricted to the
 * NIST//SECG/X9.62 prime curves only, and formatted to match project
 * coding styles.
 */
"use strict";

// Basic Javascript Elliptic Curve implementation
// Ported loosely from BouncyCastle's Java EC code
// Only Fp curves implemented for now

var BigInteger = require("../../deps/forge").jsbn.BigInteger;

// ----------------
// Helpers

function nbi() {
  return new BigInteger(null);
}

// ----------------
// Barrett modular reduction

// constructor
function Barrett(m) {
  // setup Barrett
  this.r2 = nbi();
  this.q3 = nbi();
  BigInteger.ONE.dlShiftTo(2*m.t,this.r2);
  this.mu = this.r2.divide(m);
  this.m = m;
}

function barrettConvert(x) {
  if(x.s < 0 || x.t > 2*this.m.t) return x.mod(this.m);
  else if(x.compareTo(this.m) < 0) return x;
  else { var r = nbi(); x.copyTo(r); this.reduce(r); return r; }
}

function barrettRevert(x) { return x; }

// x = x mod m (HAC 14.42)
function barrettReduce(x) {
  x.drShiftTo(this.m.t-1,this.r2);
  if(x.t > this.m.t+1) { x.t = this.m.t+1; x.clamp(); }
  this.mu.multiplyUpperTo(this.r2,this.m.t+1,this.q3);
  this.m.multiplyLowerTo(this.q3,this.m.t+1,this.r2);
  while(x.compareTo(this.r2) < 0) x.dAddOffset(1,this.m.t+1);
  x.subTo(this.r2,x);
  while(x.compareTo(this.m) >= 0) x.subTo(this.m,x);
}

// r = x^2 mod m; x != r
function barrettSqrTo(x,r) { x.squareTo(r); this.reduce(r); }

// r = x*y mod m; x,y != r
function barrettMulTo(x,y,r) { x.multiplyTo(y,r); this.reduce(r); }

Barrett.prototype.convert = barrettConvert;
Barrett.prototype.revert = barrettRevert;
Barrett.prototype.reduce = barrettReduce;
Barrett.prototype.mulTo = barrettMulTo;
Barrett.prototype.sqrTo = barrettSqrTo;

// ----------------
// ECFieldElementFp

// constructor
function ECFieldElementFp(q, x) {
  this.x = x;
  // TODO if(x.compareTo(q) >= 0) error
  this.p = q;
}

function feFpEquals(other) {
  if (other === this) {
    return true;
  }
  return (this.p.equals(other.p) && this.x.equals(other.x));
}

function feFpToBigInteger() {
  return this.x;
}

function feFpNegate() {
  return new ECFieldElementFp(this.p, this.x.negate().mod(this.p));
}

function feFpAdd(b) {
  return new ECFieldElementFp(this.p, this.x.add(b.toBigInteger()).mod(this.p));
}

function feFpSubtract(b) {
  return new ECFieldElementFp(this.p, this.x.subtract(b.toBigInteger()).mod(this.p));
}

function feFpMultiply(b) {
  return new ECFieldElementFp(this.p, this.x.multiply(b.toBigInteger()).mod(this.p));
}

function feFpSquare() {
  return new ECFieldElementFp(this.p, this.x.pow(2).mod(this.p));
}

function feFpDivide(b) {
  return new ECFieldElementFp(this.p, this.x.multiply(b.toBigInteger().modInverse(this.p)).mod(this.p));
}

ECFieldElementFp.prototype.equals = feFpEquals;
ECFieldElementFp.prototype.toBigInteger = feFpToBigInteger;
ECFieldElementFp.prototype.negate = feFpNegate;
ECFieldElementFp.prototype.add = feFpAdd;
ECFieldElementFp.prototype.subtract = feFpSubtract;
ECFieldElementFp.prototype.multiply = feFpMultiply;
ECFieldElementFp.prototype.square = feFpSquare;
ECFieldElementFp.prototype.divide = feFpDivide;

// ----------------
// ECPointFp

// constructor
function ECPointFp(curve, x, y, z) {
  this.curve = curve;
  this.x = x;
  this.y = y;
  // Projective coordinates: either zinv == null or z * zinv == 1
  // z and zinv are just BigIntegers, not fieldElements
  if (!z) {
    this.z = BigInteger.ONE;
  } else {
    this.z = z;
  }
  this.zinv = null;
  //TODO: compression flag
}

function pointFpGetX() {
  if(!this.zinv) {
    this.zinv = this.z.modInverse(this.curve.p);
  }
  var r = this.x.toBigInteger().multiply(this.zinv);
  this.curve.reduce(r);
  return this.curve.fromBigInteger(r);
}

function pointFpGetY() {
  if(!this.zinv) {
    this.zinv = this.z.modInverse(this.curve.p);
  }
  var r = this.y.toBigInteger().multiply(this.zinv);
  this.curve.reduce(r);
  return this.curve.fromBigInteger(r);
}

function pointFpEquals(other) {
  if (other === this) {
    return true;
  }
  if (this.isInfinity()) {
    return other.isInfinity();
  }
  if (other.isInfinity()) {
    return this.isInfinity();
  }
  var u, v;
  // u = Y2 * Z1 - Y1 * Z2
  u = other.y.toBigInteger().multiply(this.z).subtract(this.y.toBigInteger().multiply(other.z)).mod(this.curve.p);
  if (!u.equals(BigInteger.ZERO)) {
    return false;
  }
  // v = X2 * Z1 - X1 * Z2
  v = other.x.toBigInteger().multiply(this.z).subtract(this.x.toBigInteger().multiply(other.z)).mod(this.curve.p);
  return v.equals(BigInteger.ZERO);
}

function pointFpIsInfinity() {
  if ((this.x == null) && (this.y == null)) {
    return true;
  }
  return (this.z.equals(BigInteger.ZERO) && !this.y.toBigInteger().equals(BigInteger.ZERO));
}

function pointFpNegate() {
    return new ECPointFp(this.curve, this.x, this.y.negate(), this.z);
}

function pointFpAdd(b) {
  if (this.isInfinity()) {
    return b;
  }
  if (b.isInfinity()) {
    return this;
  }

  // u = Y2 * Z1 - Y1 * Z2
  var u = b.y.toBigInteger().multiply(this.z).subtract(this.y.toBigInteger().multiply(b.z)).mod(this.curve.p);
  // v = X2 * Z1 - X1 * Z2
  var v = b.x.toBigInteger().multiply(this.z).subtract(this.x.toBigInteger().multiply(b.z)).mod(this.curve.p);

  if (BigInteger.ZERO.equals(v)) {
    if (BigInteger.ZERO.equals(u)) {
      return this.twice(); // this == b, so double
    }
    return this.curve.getInfinity(); // this = -b, so infinity
  }

  var THREE = new BigInteger("3");
  var x1 = this.x.toBigInteger();
  var y1 = this.y.toBigInteger();

  var v2 = v.pow(2);
  var v3 = v2.multiply(v);
  var x1v2 = x1.multiply(v2);
  var zu2 = u.pow(2).multiply(this.z);

  // x3 = v * (z2 * (z1 * u^2 - 2 * x1 * v^2) - v^3)
  var x3 = zu2.subtract(x1v2.shiftLeft(1)).multiply(b.z).subtract(v3).multiply(v).mod(this.curve.p);
  // y3 = z2 * (3 * x1 * u * v^2 - y1 * v^3 - z1 * u^3) + u * v^3
  var y3 = x1v2.multiply(THREE).multiply(u).subtract(y1.multiply(v3)).subtract(zu2.multiply(u)).multiply(b.z).add(u.multiply(v3)).mod(this.curve.p);
  // z3 = v^3 * z1 * z2
  var z3 = v3.multiply(this.z).multiply(b.z).mod(this.curve.p);

  return new ECPointFp(this.curve, this.curve.fromBigInteger(x3), this.curve.fromBigInteger(y3), z3);
}

function pointFpTwice() {
  if(this.isInfinity()) {
    return this;
  }
  if (this.y.toBigInteger().signum() === 0) {
    return this.curve.getInfinity();
  }

  // TODO: optimized handling of constants
  var THREE = new BigInteger("3");
  var x1 = this.x.toBigInteger();
  var y1 = this.y.toBigInteger();

  var y1z1 = y1.multiply(this.z);
  var y1sqz1 = y1z1.multiply(y1).mod(this.curve.p);
  var a = this.curve.a.toBigInteger();

  // w = 3 * x1^2 + a * z1^2
  var w = x1.pow(2).multiply(THREE);
  if (!BigInteger.ZERO.equals(a)) {
    w = w.add(this.z.pow(2).multiply(a));
  }
  w = w.mod(this.curve.p);
  //this.curve.reduce(w);
  // x3 = 2 * y1 * z1 * (w^2 - 8 * x1 * y1^2 * z1)
  var x3 = w.pow(2).subtract(x1.shiftLeft(3).multiply(y1sqz1)).shiftLeft(1).multiply(y1z1).mod(this.curve.p);
  // y3 = 4 * y1^2 * z1 * (3 * w * x1 - 2 * y1^2 * z1) - w^3
  var y3 = w.multiply(THREE).multiply(x1).subtract(y1sqz1.shiftLeft(1)).shiftLeft(2).multiply(y1sqz1).subtract(w.pow(2).multiply(w)).mod(this.curve.p);
  // z3 = 8 * (y1 * z1)^3
  var z3 = y1z1.pow(2).multiply(y1z1).shiftLeft(3).mod(this.curve.p);

  return new ECPointFp(this.curve, this.curve.fromBigInteger(x3), this.curve.fromBigInteger(y3), z3);
}

// Simple NAF (Non-Adjacent Form) multiplication algorithm
// TODO: modularize the multiplication algorithm
function pointFpMultiply(k) {
  if (this.isInfinity()) {
    return this;
  }
  if (k.signum() === 0) {
    return this.curve.getInfinity();
  }

  var e = k;
  var h = e.multiply(new BigInteger("3"));

  var neg = this.negate();
  var R = this;

  var i;
  for(i = h.bitLength() - 2; i > 0; --i) {
    R = R.twice();

    var hBit = h.testBit(i);
    var eBit = e.testBit(i);

    if (hBit !== eBit) {
      R = R.add(hBit ? this : neg);
    }
  }

  return R;
}

// Compute this*j + x*k (simultaneous multiplication)
function pointFpMultiplyTwo(j, x, k) {
  var i;
  if (j.bitLength() > k.bitLength()) {
    i = j.bitLength() - 1;
  } else {
    i = k.bitLength() - 1;
  }

  var R = this.curve.getInfinity();
  var both = this.add(x);
  while (i >= 0) {
    R = R.twice();
    if (j.testBit(i)) {
      if (k.testBit(i)) {
        R = R.add(both);
      }
      else {
        R = R.add(this);
      }
    }
    else {
      if (k.testBit(i)) {
        R = R.add(x);
      }
    }
    --i;
  }

  return R;
}

ECPointFp.prototype.getX = pointFpGetX;
ECPointFp.prototype.getY = pointFpGetY;
ECPointFp.prototype.equals = pointFpEquals;
ECPointFp.prototype.isInfinity = pointFpIsInfinity;
ECPointFp.prototype.negate = pointFpNegate;
ECPointFp.prototype.add = pointFpAdd;
ECPointFp.prototype.twice = pointFpTwice;
ECPointFp.prototype.multiply = pointFpMultiply;
ECPointFp.prototype.multiplyTwo = pointFpMultiplyTwo;

// ----------------
// ECCurveFp

// constructor
function ECCurveFp(p, a, b) {
  this.p = p;
  this.a = this.fromBigInteger(a);
  this.b = this.fromBigInteger(b);
  this.infinity = new ECPointFp(this, null, null);
  this.reducer = new Barrett(this.p);
}

function curveFpgetP() {
  return this.p;
}

function curveFpGetA() {
  return this.a;
}

function curveFpGetB() {
  return this.b;
}

function curveFpEquals(other) {
  if (other === this) {
    return true;
  }
  return (this.p.equals(other.p) && this.a.equals(other.a) && this.b.equals(other.b));
}

function curveFpContains(pt) {
  // y^2 = x^3 + a*x + b mod p
  var x = pt.getX().toBigInteger(),
      y = pt.getY().toBigInteger(),
      a = this.a.toBigInteger(),
      b = this.b.toBigInteger(),
      p = this.p;

  var left = y.pow(2).mod(p),
      right = x.pow(3).add(a.multiply(x)).add(b).mod(p)

  return left.equals(right);
}

function curveFpGetInfinity() {
  return this.infinity;
}

function curveFpFromBigInteger(x) {
  return new ECFieldElementFp(this.p, x);
}

function curveReduce(x) {
  this.reducer.reduce(x);
}

// for now, work with hex strings because they're easier in JS
function curveFpDecodePointHex(s) {
  switch (parseInt(s.substring(0, 2), 16)) {
    // first byte
    case 0:
      return this.infinity;
    case 2:
    case 3:
      // point compression not supported yet
      return null;
    case 4:
    case 6:
    case 7:
      var len = (s.length - 2) / 2;
      var xHex = s.substr(2, len);
      var yHex = s.substr(len + 2, len);

      return new ECPointFp(this,
                           this.fromBigInteger(new BigInteger(xHex, 16)),
                           this.fromBigInteger(new BigInteger(yHex, 16)));

    default: // unsupported
      return null;
    }
}

function curveFpEncodePointHex(p) {
  if (p.isInfinity()) {
    return "00";
  }
  var xHex = p.getX().toBigInteger().toString(16);
  var yHex = p.getY().toBigInteger().toString(16);
  var oLen = this.getP().toString(16).length;
  if ((oLen % 2) !== 0) {
    oLen++;
  }
  while (xHex.length < oLen) {
    xHex = "0" + xHex;
  }
  while (yHex.length < oLen) {
    yHex = "0" + yHex;
  }
  return "04" + xHex + yHex;
}

ECCurveFp.prototype.getP = curveFpgetP;
ECCurveFp.prototype.getA = curveFpGetA;
ECCurveFp.prototype.getB = curveFpGetB;
ECCurveFp.prototype.equals = curveFpEquals;
ECCurveFp.prototype.contains = curveFpContains;
ECCurveFp.prototype.getInfinity = curveFpGetInfinity;
ECCurveFp.prototype.fromBigInteger = curveFpFromBigInteger;
ECCurveFp.prototype.reduce = curveReduce;
ECCurveFp.prototype.decodePointHex = curveFpDecodePointHex;
ECCurveFp.prototype.encodePointHex = curveFpEncodePointHex;

// Exports
module.exports = {
  ECFieldElementFp: ECFieldElementFp,
  ECPointFp: ECPointFp,
  ECCurveFp: ECCurveFp
};
