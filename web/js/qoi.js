// QOI ("Quite OK Image") decoder. Spec: https://qoiformat.org/qoi-specification.pdf
// QOI is used for tile payloads because it is lossless (pixel-accurate), fast,
// and simple enough to encode in pure G on every LabVIEW target.

const OP_INDEX = 0x00;
const OP_DIFF = 0x40;
const OP_LUMA = 0x80;
const OP_RUN = 0xc0;
const OP_RGB = 0xfe;
const OP_RGBA = 0xff;
const MASK_2 = 0xc0;

export const QOI_HEADER_SIZE = 14;
export const QOI_END_MARKER = Uint8Array.of(0, 0, 0, 0, 0, 0, 0, 1);

export class QoiError extends Error {
  constructor(message) {
    super(message);
    this.name = 'QoiError';
  }
}

/**
 * Decode a QOI image into RGBA bytes (suitable for ImageData).
 * @param {Uint8Array} bytes
 * @param {Uint8ClampedArray} [target] optional output buffer of width*height*4 bytes
 * @returns {{width:number, height:number, channels:number, rgba:Uint8ClampedArray}}
 */
export function decodeQoi(bytes, target) {
  if (bytes.byteLength < QOI_HEADER_SIZE + QOI_END_MARKER.length) throw new QoiError('data too short');
  if (bytes[0] !== 0x71 || bytes[1] !== 0x6f || bytes[2] !== 0x69 || bytes[3] !== 0x66) {
    throw new QoiError('bad magic');
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const width = view.getUint32(4);
  const height = view.getUint32(8);
  const channels = bytes[12];
  if (width === 0 || height === 0 || width > 0xffff || height > 0xffff) throw new QoiError('bad dimensions');
  if (channels !== 3 && channels !== 4) throw new QoiError('bad channel count');

  const pxLen = width * height * 4;
  const rgba = target ?? new Uint8ClampedArray(pxLen);
  if (rgba.length < pxLen) throw new QoiError('target buffer too small');

  const index = new Uint8Array(64 * 4);
  const chunksEnd = bytes.byteLength - QOI_END_MARKER.length;
  let r = 0, g = 0, b = 0, a = 255;
  let run = 0;
  let p = QOI_HEADER_SIZE;

  for (let o = 0; o < pxLen; o += 4) {
    if (run > 0) {
      run--;
    } else if (p < chunksEnd) {
      const b1 = bytes[p++];
      if (b1 === OP_RGB) {
        r = bytes[p++]; g = bytes[p++]; b = bytes[p++];
      } else if (b1 === OP_RGBA) {
        r = bytes[p++]; g = bytes[p++]; b = bytes[p++]; a = bytes[p++];
      } else {
        switch (b1 & MASK_2) {
          case OP_INDEX: {
            const i = (b1 & 0x3f) * 4;
            r = index[i]; g = index[i + 1]; b = index[i + 2]; a = index[i + 3];
            break;
          }
          case OP_DIFF:
            r = (r + ((b1 >> 4) & 0x03) - 2) & 0xff;
            g = (g + ((b1 >> 2) & 0x03) - 2) & 0xff;
            b = (b + (b1 & 0x03) - 2) & 0xff;
            break;
          case OP_LUMA: {
            const b2 = bytes[p++];
            const vg = (b1 & 0x3f) - 32;
            r = (r + vg - 8 + ((b2 >> 4) & 0x0f)) & 0xff;
            g = (g + vg) & 0xff;
            b = (b + vg - 8 + (b2 & 0x0f)) & 0xff;
            break;
          }
          case OP_RUN:
            run = b1 & 0x3f;
            break;
        }
      }
      const h = ((r * 3 + g * 5 + b * 7 + a * 11) % 64) * 4;
      index[h] = r; index[h + 1] = g; index[h + 2] = b; index[h + 3] = a;
    } else {
      throw new QoiError('ran out of data');
    }
    rgba[o] = r; rgba[o + 1] = g; rgba[o + 2] = b; rgba[o + 3] = a;
  }
  return { width, height, channels, rgba };
}
