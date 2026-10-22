// Reference implementation of the server side of RFC 6455.
// Mirrors Transport/WS_AcceptKey.vi, WS_DecodeFrame.vi and WS_EncodeFrame.vi.

import { createHash } from 'node:crypto';

export const WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';

export const OP_CONTINUATION = 0x0;
export const OP_TEXT = 0x1;
export const OP_BINARY = 0x2;
export const OP_CLOSE = 0x8;
export const OP_PING = 0x9;
export const OP_PONG = 0xa;

export const CLOSE_NORMAL = 1000;
export const CLOSE_PROTOCOL_ERROR = 1002;
export const CLOSE_TOO_BIG = 1009;
export const CLOSE_POLICY = 1008;

/** Client -> server messages are small JSON; anything larger is hostile. */
export const MAX_CLIENT_PAYLOAD = 64 * 1024;

export class WsError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'WsError';
    this.code = code;
  }
}

/** Sec-WebSocket-Accept value for a given Sec-WebSocket-Key. */
export function acceptKey(key) {
  return createHash('sha1').update(key + WS_GUID).digest('base64');
}

/**
 * Try to decode one client frame from the start of buf.
 * Returns null if more bytes are needed, otherwise {fin, opcode, payload, size}.
 * Enforces: masking required, no RSV bits, control frames <=125 bytes and unfragmented,
 * payload <= maxPayload.
 */
export function decodeClientFrame(buf, maxPayload = MAX_CLIENT_PAYLOAD) {
  if (buf.length < 2) return null;
  const b0 = buf[0];
  const b1 = buf[1];
  const fin = (b0 & 0x80) !== 0;
  if (b0 & 0x70) throw new WsError(CLOSE_PROTOCOL_ERROR, 'RSV bits set');
  const opcode = b0 & 0x0f;
  if (![OP_CONTINUATION, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG].includes(opcode)) {
    throw new WsError(CLOSE_PROTOCOL_ERROR, `unknown opcode ${opcode}`);
  }
  if (!(b1 & 0x80)) throw new WsError(CLOSE_PROTOCOL_ERROR, 'client frame not masked');
  let len = b1 & 0x7f;
  let p = 2;
  if (len === 126) {
    if (buf.length < 4) return null;
    len = (buf[2] << 8) | buf[3];
    p = 4;
  } else if (len === 127) {
    if (buf.length < 10) return null;
    // Anything that needs the upper 32 bits is far beyond maxPayload.
    if (buf[2] | buf[3] | buf[4] | buf[5]) throw new WsError(CLOSE_TOO_BIG, 'payload too large');
    len = ((buf[6] << 24) >>> 0) + (buf[7] << 16) + (buf[8] << 8) + buf[9];
    p = 10;
  }
  const isControl = (opcode & 0x8) !== 0;
  if (isControl && (len > 125 || !fin)) throw new WsError(CLOSE_PROTOCOL_ERROR, 'invalid control frame');
  if (len > maxPayload) throw new WsError(CLOSE_TOO_BIG, 'payload too large');
  if (buf.length < p + 4 + len) return null;
  const mask = buf.subarray(p, p + 4);
  p += 4;
  const payload = Buffer.alloc(len);
  for (let i = 0; i < len; i++) payload[i] = buf[p + i] ^ mask[i & 3];
  return { fin, opcode, payload, size: p + len };
}

/** Encode an unmasked server frame (FIN always set; the server never fragments). */
export function encodeServerFrame(opcode, payload) {
  const data = Buffer.isBuffer(payload) ? payload : Buffer.from(payload);
  const len = data.length;
  let head;
  if (len < 126) {
    head = Buffer.from([0x80 | opcode, len]);
  } else if (len < 0x10000) {
    head = Buffer.from([0x80 | opcode, 126, len >> 8, len & 0xff]);
  } else {
    head = Buffer.alloc(10);
    head[0] = 0x80 | opcode;
    head[1] = 127;
    head.writeUInt32BE(Math.floor(len / 0x100000000), 2);
    head.writeUInt32BE(len >>> 0, 6);
  }
  return Buffer.concat([head, data]);
}

export function closePayload(code, reason = '') {
  const r = Buffer.from(reason, 'utf8').subarray(0, 123);
  const b = Buffer.alloc(2 + r.length);
  b.writeUInt16BE(code, 0);
  r.copy(b, 2);
  return b;
}
