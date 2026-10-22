// Reference QOI encoder. The G implementation (QOI_Encode.vi) must produce
// byte-identical output for the vectors in tests/vectors/qoi.json.
//
// Input pixels are a Uint32Array of 0x00RRGGBB values, row-major, which is exactly
// what LabVIEW's Unflatten Pixmap returns for a 24-bit image. Output is always
// 3-channel (RGB) QOI with sRGB colorspace.

const OP_INDEX = 0x00;
const OP_DIFF = 0x40;
const OP_LUMA = 0x80;
const OP_RUN = 0xc0;
const OP_RGB = 0xfe;

/**
 * @param {Uint32Array} pixels source pixels, 0x00RRGGBB
 * @param {number} stride source row length in pixels
 * @param {{x:number,y:number,w:number,h:number}} rect region to encode
 * @returns {Uint8Array}
 */
export function encodeQoi(pixels, stride, rect) {
  const { x: x0, y: y0, w, h } = rect;
  // Worst case: 4 bytes per pixel (OP_RGB) + header + end marker.
  const out = new Uint8Array(14 + w * h * 4 + 8);
  const view = new DataView(out.buffer);
  out.set([0x71, 0x6f, 0x69, 0x66], 0); // "qoif"
  view.setUint32(4, w);
  view.setUint32(8, h);
  out[12] = 3; // channels
  out[13] = 0; // sRGB with linear alpha
  let p = 14;

  const index = new Int32Array(64).fill(-1);
  let prev = 0x000000; // QOI starts from r=g=b=0, a=255
  let run = 0;
  const last = w * h - 1;
  let n = 0;

  for (let yy = y0; yy < y0 + h; yy++) {
    const row = yy * stride;
    for (let xx = x0; xx < x0 + w; xx++, n++) {
      const px = pixels[row + xx] & 0xffffff;
      if (px === prev) {
        run++;
        if (run === 62 || n === last) {
          out[p++] = OP_RUN | (run - 1);
          run = 0;
        }
        continue;
      }
      if (run > 0) {
        out[p++] = OP_RUN | (run - 1);
        run = 0;
      }
      const r = (px >>> 16) & 0xff;
      const g = (px >>> 8) & 0xff;
      const b = px & 0xff;
      const hash = (r * 3 + g * 5 + b * 7 + 255 * 11) % 64;
      if (index[hash] === px) {
        out[p++] = OP_INDEX | hash;
      } else {
        index[hash] = px;
        const pr = (prev >>> 16) & 0xff;
        const pg = (prev >>> 8) & 0xff;
        const pb = prev & 0xff;
        // Signed 8-bit wraparound differences.
        const vr = ((r - pr + 384) & 0xff) - 128;
        const vg = ((g - pg + 384) & 0xff) - 128;
        const vb = ((b - pb + 384) & 0xff) - 128;
        const vgr = vr - vg;
        const vgb = vb - vg;
        if (vr > -3 && vr < 2 && vg > -3 && vg < 2 && vb > -3 && vb < 2) {
          out[p++] = OP_DIFF | ((vr + 2) << 4) | ((vg + 2) << 2) | (vb + 2);
        } else if (vgr > -9 && vgr < 8 && vg > -33 && vg < 32 && vgb > -9 && vgb < 8) {
          out[p++] = OP_LUMA | (vg + 32);
          out[p++] = ((vgr + 8) << 4) | (vgb + 8);
        } else {
          out[p++] = OP_RGB;
          out[p++] = r;
          out[p++] = g;
          out[p++] = b;
        }
      }
      prev = px;
    }
  }
  out.set([0, 0, 0, 0, 0, 0, 0, 1], p);
  p += 8;
  return out.slice(0, p);
}
