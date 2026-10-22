// RemoteVI wire protocol, version 1. See docs/protocol.md for the normative spec.
//
// Binary messages (server -> client) are big-endian, which matches LabVIEW's
// native Flatten To String byte order, so the G side needs no byte swapping.

export const PROTOCOL_VERSION = 1;

export const MSG_FRAME = 0x10;

export const ENC_SOLID = 0x00;
export const ENC_QOI = 0x01;
export const ENC_RAW_RGB = 0x02;

export const FRAME_FLAG_KEYFRAME = 0x01;

// type u8, flags u8, seq u32, width u16, height u16, tileCount u16
export const FRAME_HEADER_SIZE = 12;
// x u16, y u16, w u16, h u16, encoding u8, length u32
export const TILE_HEADER_SIZE = 13;

export class ProtocolError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ProtocolError';
  }
}

/**
 * Parse a FRAME message.
 * @param {ArrayBuffer|Uint8Array} input
 * @returns {{keyframe: boolean, flags: number, seq: number, width: number,
 *            height: number, tiles: Array<{x:number,y:number,w:number,h:number,
 *            encoding:number,data:Uint8Array}>}}
 */
export function decodeFrame(input) {
  const bytes = input instanceof Uint8Array ? input : new Uint8Array(input);
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (bytes.byteLength < FRAME_HEADER_SIZE) throw new ProtocolError('frame too short');
  if (bytes[0] !== MSG_FRAME) throw new ProtocolError(`unexpected message type 0x${bytes[0].toString(16)}`);

  const flags = bytes[1];
  const seq = view.getUint32(2);
  const width = view.getUint16(6);
  const height = view.getUint16(8);
  const tileCount = view.getUint16(10);

  const tiles = new Array(tileCount);
  let p = FRAME_HEADER_SIZE;
  for (let i = 0; i < tileCount; i++) {
    if (p + TILE_HEADER_SIZE > bytes.byteLength) throw new ProtocolError(`tile ${i}: truncated header`);
    const x = view.getUint16(p);
    const y = view.getUint16(p + 2);
    const w = view.getUint16(p + 4);
    const h = view.getUint16(p + 6);
    const encoding = bytes[p + 8];
    const length = view.getUint32(p + 9);
    p += TILE_HEADER_SIZE;
    if (p + length > bytes.byteLength) throw new ProtocolError(`tile ${i}: truncated payload`);
    if (x + w > width || y + h > height) throw new ProtocolError(`tile ${i}: outside panel`);
    tiles[i] = { x, y, w, h, encoding, data: bytes.subarray(p, p + length) };
    p += length;
  }
  if (p !== bytes.byteLength) throw new ProtocolError('trailing bytes after last tile');

  return { keyframe: (flags & FRAME_FLAG_KEYFRAME) !== 0, flags, seq, width, height, tiles };
}

/** Build a FRAME message. Used by the reference server and the tests. */
export function encodeFrame({ flags = 0, seq, width, height, tiles }) {
  let size = FRAME_HEADER_SIZE;
  for (const t of tiles) size += TILE_HEADER_SIZE + t.data.byteLength;
  const out = new Uint8Array(size);
  const view = new DataView(out.buffer);
  out[0] = MSG_FRAME;
  out[1] = flags;
  view.setUint32(2, seq >>> 0);
  view.setUint16(6, width);
  view.setUint16(8, height);
  view.setUint16(10, tiles.length);
  let p = FRAME_HEADER_SIZE;
  for (const t of tiles) {
    view.setUint16(p, t.x);
    view.setUint16(p + 2, t.y);
    view.setUint16(p + 4, t.w);
    view.setUint16(p + 6, t.h);
    out[p + 8] = t.encoding;
    view.setUint32(p + 9, t.data.byteLength);
    p += TILE_HEADER_SIZE;
    out.set(t.data, p);
    p += t.data.byteLength;
  }
  return out;
}

/** Parse a JSON text message; returns null for anything that is not a typed object. */
export function parseTextMessage(text) {
  let msg;
  try {
    msg = JSON.parse(text);
  } catch {
    return null;
  }
  if (msg === null || typeof msg !== 'object' || typeof msg.t !== 'string') return null;
  return msg;
}
