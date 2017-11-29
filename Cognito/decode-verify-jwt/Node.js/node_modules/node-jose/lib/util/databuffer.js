/*!
 * util/databuffer.js - Forge-compatible Buffer based on Node.js Buffers
 *
 * Copyright (c) 2015 Cisco Systems, Inc. See LICENSE file.
 */
"use strict";

var forge = require("../deps/forge.js"),
    base64url = require("./base64url.js");

/**
 *
 */
function DataBuffer(b, options) {
  options = options || {};

  // treat (views of) (Array)Buffers special
  // NOTE: default implementation creates copies, but efficiently
  //       wherever possible
  if (Buffer.isBuffer(b)) {
    this.data = b;
  } else if (forge.util.isArrayBuffer(b)) {
    b = new Uint8Array(b);
    this.data = new Buffer(b);
  } else if (forge.util.isArrayBufferView(b)) {
    b = new Uint8Array(b.buffer, b.byteOffset, b.byteLength);
    this.data = new Buffer(b);
  }

  if (this.data) {
    this.write = this.data.length;
    b = undefined;
  }

  // setup growth rate
  this.growSize = options.growSize || DataBuffer.DEFAULT_GROW_SIZE;

  // initialize pointers and data
  this.write = this.write || 0;
  this.read = this.read || 0;
  if (b) {
    this.putBytes(b);
  } else if (!this.data) {
    this.accommodate(0);
  }

  // massage read/write pointers
  options.readOffset = ("readOffset" in options) ?
                       options.readOffset :
                       this.read;
  this.write = ("writeOffset" in options) ?
               options.writeOffset :
               this.write;
  this.read = Math.min(options.readOffset, this.write);
}
DataBuffer.DEFAULT_GROW_SIZE = 16;

DataBuffer.prototype.length = function() {
  return this.write - this.read;
};
DataBuffer.prototype.available = function() {
  return this.data.length - this.write;
};
DataBuffer.prototype.isEmpty = function() {
  return this.length() <= 0;
};

DataBuffer.prototype.accommodate = function(length) {
  if (!this.data) {
    // initializes a new buffer
    length = Math.max(this.write + length, this.growSize);

    this.data = new Buffer(length);
  } else if (this.available() < length) {
    length = Math.max(length, this.growSize);

    // create a new empty buffer, and copy current one into it
    var src = this.data;
    var dst = new Buffer(src.length + length);
    src.copy(dst, 0);

    // set data as the new buffer
    this.data = dst;
  }
  // ensure the rest is 0
  this.data.fill(0, this.write);

  return this;
};
DataBuffer.prototype.clear = function() {
  this.read = this.write = 0;
  this.data = new Buffer(0);
  return this;
};
DataBuffer.prototype.truncate = function(count) {
  // chop off <count> bytes from the end
  this.write = this.read + Math.max(0, this.length() - count);
  // ensure the remainder is 0
  this.data.fill(0, this.write);
  return this;
};
DataBuffer.prototype.compact = function() {
  if (this.read > 0) {
    if (this.write === this.read) {
      this.read = this.write = 0;
    } else {
      this.data.copy(this.data, 0, this.read, this.write);
      this.write = this.write - this.read;
      this.read = 0;
    }
    // ensure remainder is 0
    this.data.fill(0, this.write);
  }
  return this;
};
DataBuffer.prototype.copy = function() {
  return new DataBuffer(this, {
    readOffset: this.read,
    writeOffset: this.write,
    growSize: this.growSize
  });
};

DataBuffer.prototype.equals = function(test) {
  if (!DataBuffer.isBuffer(test)) {
    return false;
  }

  if (test.length() !== this.length()) {
    return false;
  }

  var rval = true,
      delta = this.read - test.read;
  // constant time
  for (var idx = test.read; test.write > idx; idx++) {
    rval = rval && (this.data[idx + delta] === test.data[idx]);
  }
  return rval;
};
DataBuffer.prototype.at = function(idx) {
  return this.data[this.read + idx];
};
DataBuffer.prototype.setAt = function(idx, b) {
  this.data[this.read + idx] = b;
  return this;
};
DataBuffer.prototype.last = function() {
  return this.data[this.write - 1];
};
DataBuffer.prototype.bytes = function(count) {
  var rval;
  if (undefined === count) {
    count = this.length();
  } else if (count) {
    count = Math.min(count, this.length());
  }

  if (0 === count) {
    rval = "";
  } else {
    var begin = this.read,
        end = begin + count,
        data = this.data.slice(begin, end);
    rval = String.fromCharCode.apply(null, data);
  }

  return rval;
};
DataBuffer.prototype.buffer = function(count) {
  var rval;
  if (undefined === count) {
    count = this.length();
  } else if (count) {
    count = Math.min(count, this.length());
  }

  if (0 === count) {
    rval = new ArrayBuffer(0);
  } else {
    var begin = this.read,
        end = begin + count,
        data = this.data.slice(begin, end);
    rval = new Uint8Array(end - begin);
    rval.set(data);
  }

  return rval;
};
DataBuffer.prototype.native = function(count) {
  var rval;
  if ("undefined" === typeof count) {
    count = this.length();
  } else if (count) {
    count = Math.min(count, this.length());
  }

  if (0 === count) {
    rval = new Buffer(0);
  } else {
    var begin = this.read,
        end = begin + count;
    rval = this.data.slice(begin, end);
  }

  return rval;
};

DataBuffer.prototype.toHex = function() {
  return this.toString("hex");
};
DataBuffer.prototype.toString = function(encoding) {
  // short circuit empty string
  if (0 === this.length()) {
    return "";
  }

  var view = this.data.slice(this.read, this.write);
  encoding = encoding || "utf8";
  // special cases, then built-in support
  switch (encoding) {
    case "raw":
      return view.toString("binary");
    case "base64url":
      return base64url.encode(view);
    case "utf16":
      return view.toString("ucs2");
    default:
      return view.toString(encoding);
  }
};

DataBuffer.prototype.fillWithByte = function(b, n) {
  if (!n) {
    n = this.available();
  }
  this.accommodate(n);
  this.data.fill(b, this.write, this.write + n);
  this.write += n;

  return this;
};

DataBuffer.prototype.getBuffer = function(count) {
  var rval = this.buffer(count);
  this.read += rval.byteLength;

  return rval;
};
DataBuffer.prototype.putBuffer = function(bytes) {
  return this.putBytes(bytes);
};

DataBuffer.prototype.getBytes = function(count) {
  var rval = this.bytes(count);
  this.read += rval.length;
  return rval;
};
DataBuffer.prototype.putBytes = function(bytes, encoding) {
  if ("string" === typeof bytes) {
    // fixup encoding
    encoding = encoding || "binary";
    switch (encoding) {
      case "utf16":
        // treat as UCS-2/UTF-16BE
        encoding = "ucs-2";
        break;
      case "raw":
        encoding = "binary";
        break;
      case "base64url":
        // NOTE: this returns a Buffer
        bytes = base64url.decode(bytes);
        break;
    }

    // replace bytes with decoded Buffer (if not already)
    if (!Buffer.isBuffer(bytes)) {
      bytes = new Buffer(bytes, encoding);
    }
  }

  var src, dst;
  if (bytes instanceof DataBuffer) {
    // be slightly more efficient
    var orig = bytes;
    bytes = orig.data.slice(orig.read, orig.write);
    orig.read = orig.write;
  } else if (bytes instanceof forge.util.ByteStringBuffer) {
    bytes = bytes.getBytes();
  }

  // process array
  if (Buffer.isBuffer(bytes)) {
    src = bytes;
  } else if (Array.isArray(bytes)) {
    src = new Buffer(bytes);
  } else if (forge.util.isArrayBuffer(bytes)) {
    src = new Uint8Array(bytes);
    src = new Buffer(src);
  } else if (forge.util.isArrayBufferView(bytes)) {
    src = (bytes instanceof Uint8Array) ?
              bytes :
              new Uint8Array(bytes.buffer,
                             bytes.byteOffset,
                             bytes.byteLength);
    src = new Buffer(src);
  } else {
    throw new TypeError("invalid source type");
  }

  this.accommodate(src.length);
  dst = this.data;
  src.copy(dst, this.write);
  this.write += src.length;

  return this;
};

DataBuffer.prototype.getNative = function(count) {
  var rval = this.native(count);
  this.read += rval.length;
  return rval;
};
DataBuffer.prototype.putNative = DataBuffer.prototype.putBuffer;

DataBuffer.prototype.getByte = function() {
  var b = this.data[this.read];
  this.read = Math.min(this.read + 1, this.write);
  return b;
};
DataBuffer.prototype.putByte = function(b) {
  this.accommodate(1);
  this.data[this.write] = b & 0xff;
  this.write++;

  return this;
};

DataBuffer.prototype.getInt16 = function() {
  var n = (this.data[this.read] << 8) ^
          (this.data[this.read + 1]);
  this.read = Math.min(this.read + 2, this.write);
  return n;
};
DataBuffer.prototype.putInt16 = function(n) {
  this.accommodate(2);
  this.data[this.write] = (n >>> 8) & 0xff;
  this.data[this.write + 1] = n & 0xff;
  this.write += 2;
  return this;
};

DataBuffer.prototype.getInt24 = function() {
  var n = (this.data[this.read] << 16) ^
          (this.data[this.read + 1] << 8) ^
          this.data[this.read + 2];
  this.read = Math.min(this.read + 3, this.write);
  return n;
};
DataBuffer.prototype.putInt24 = function(n) {
  this.accommodate(3);
  this.data[this.write] = (n >>> 16) & 0xff;
  this.data[this.write + 1] = (n >>> 8) & 0xff;
  this.data[this.write + 2] = n & 0xff;
  this.write += 3;
  return this;
};

DataBuffer.prototype.getInt32 = function() {
  var n = (this.data[this.read] << 24) ^
          (this.data[this.read + 1] << 16) ^
          (this.data[this.read + 2] << 8) ^
          this.data[this.read + 3];
  this.read = Math.min(this.read + 4, this.write);
  return n;
};
DataBuffer.prototype.putInt32 = function(n) {
  this.accommodate(4);
  this.data[this.write] = (n >>> 24) & 0xff;
  this.data[this.write + 1] = (n >>> 16) & 0xff;
  this.data[this.write + 2] = (n >>> 8) & 0xff;
  this.data[this.write + 3] = n & 0xff;
  this.write += 4;
  return this;
};

DataBuffer.prototype.getInt16Le = function() {
  var n = (this.data[this.read + 1] << 8) ^
          this.data[this.read];
  this.read = Math.min(this.read + 2, this.write);
  return n;
};
DataBuffer.prototype.putInt16Le = function(n) {
  this.accommodate(2);
  this.data[this.write + 1] = (n >>> 8) & 0xff;
  this.data[this.write] = n & 0xff;
  this.write += 2;
  return this;
};

DataBuffer.prototype.getInt24Le = function() {
  var n = (this.data[this.read + 2] << 16) ^
          (this.data[this.read + 1] << 8) ^
          this.data[this.read];
  this.read = Math.min(this.read + 3, this.write);
  return n;
};
DataBuffer.prototype.putInt24Le = function(n) {
  this.accommodate(3);
  this.data[this.write + 2] = (n >>> 16) & 0xff;
  this.data[this.write + 1] = (n >>> 8) & 0xff;
  this.data[this.write] = n & 0xff;
  this.write += 3;
  return this;
};
DataBuffer.prototype.getInt32Le = function() {
  var n = (this.data[this.read + 3] << 24) ^
          (this.data[this.read + 2] << 16) ^
          (this.data[this.read + 1] << 8) ^
          this.data[this.read];
  this.read = Math.min(this.read + 4, this.write);
  return n;
};
DataBuffer.prototype.putInt32Le = function(n) {
  this.accommodate(4);
  this.data[this.write + 3] = (n >>> 24) & 0xff;
  this.data[this.write + 2] = (n >>> 16) & 0xff;
  this.data[this.write + 1] = (n >>> 8) & 0xff;
  this.data[this.write] = n & 0xff;
  this.write += 4;
  return this;
};

DataBuffer.prototype.getInt = function(bits) {
  var rval = 0;
  do {
    rval = (rval << 8) | this.getByte();
    bits -= 8;
  } while (bits > 0);
  return rval;
};
DataBuffer.prototype.putInt = function(n, bits) {
  this.accommodate(Math.ceil(bits / 8));
  do {
    bits -= 8;
    this.putByte((n >> bits) & 0xff);
  } while (bits > 0);
  return this;
};

DataBuffer.prototype.putSignedInt = function(n, bits) {
  if (n < 0) {
    n += 2 << (bits - 1);
  }
  return this.putInt(n, bits);
};

DataBuffer.prototype.putString = function(str) {
  return this.putBytes(str, "utf16");
};

DataBuffer.isBuffer = function(test) {
  return (test instanceof DataBuffer);
};
DataBuffer.asBuffer = function(orig) {
  return DataBuffer.isBuffer(orig) ?
         orig :
         orig ?
         new DataBuffer(orig) :
         new DataBuffer();
};

module.exports = forge.util.ByteBuffer = DataBuffer;
