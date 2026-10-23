// Minimal 24-bit PNG encoder for the reference server. The LabVIEW side uses
// NI's `LV Image to PNG Data.vi`; the browser only needs a valid PNG either way.

import { deflateSync, crc32 } from 'node:zlib';

function chunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, 'latin1');
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}

/** @param {Uint32Array} pixels 0x00RRGGBB, row-major, w*h */
export function encodePng(pixels, w, h) {
  const raw = Buffer.alloc(h * (1 + w * 3));
  for (let y = 0, o = 0; y < h; y++) {
    raw[o++] = 0; // filter: none
    for (let x = 0; x < w; x++) {
      const p = pixels[y * w + x];
      raw[o++] = (p >> 16) & 0xff;
      raw[o++] = (p >> 8) & 0xff;
      raw[o++] = p & 0xff;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;  // bit depth
  ihdr[9] = 2;  // colour type: truecolour
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 1 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}
