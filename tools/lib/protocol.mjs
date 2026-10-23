// Protocol v2 reference (docs/protocol.md): the binary FRAME message the server
// sends and the text input messages the client sends. Mirrors
// Protocol/Frame Encode.vi and Protocol/Parse Input.vi.

export const FRAME_MAGIC = 0x52;
export const MSG_FRAME = 1;
export const FRAME_HEADER = 12;
export const RECT_HEADER = 8;
export const FRAMES_IN_FLIGHT = 2;

/**
 * @param {number} seq
 * @param {number} width
 * @param {number} height
 * @param {{x:number,y:number,png:Buffer}[]} rects
 */
export function encodeFrame(seq, width, height, rects) {
  const size = FRAME_HEADER + rects.reduce((n, r) => n + RECT_HEADER + r.png.length, 0);
  const out = Buffer.alloc(size);
  out[0] = FRAME_MAGIC;
  out[1] = MSG_FRAME;
  out.writeUInt32BE(seq >>> 0, 2);
  out.writeUInt16BE(width, 6);
  out.writeUInt16BE(height, 8);
  out.writeUInt16BE(rects.length, 10);
  let o = FRAME_HEADER;
  for (const r of rects) {
    out.writeInt16BE(r.x, o);
    out.writeInt16BE(r.y, o + 2);
    out.writeUInt32BE(r.png.length, o + 4);
    r.png.copy(out, o + RECT_HEADER);
    o += RECT_HEADER + r.png.length;
  }
  return out;
}

/**
 * Parse one client text message.
 *   "m <msg> <x> <y> <wParam>"   mouse message at panel coordinates
 *   "k <msg> <wParam> <lParam>"  keyboard message
 *   "a <seq>"                    frame acknowledged
 * Returns null for anything malformed; the server ignores those.
 */
export function parseInput(text) {
  const parts = text.split(' ');
  // Tokens are strictly decimal integers: no empty tokens (double or trailing spaces), no '+', '.', 'e'.
  if (!parts.slice(1).every((t) => /^-?[0-9]{1,10}$/.test(t))) return null;
  const nums = parts.slice(1).map(Number);
  if (nums.some((n) => n < -0x80000000 || n > 0xffffffff)) return null;
  switch (parts[0]) {
    case 'm':
      return nums.length === 4 ? { kind: 'mouse', msg: nums[0], x: nums[1], y: nums[2], wParam: nums[3] } : null;
    case 'k':
      return nums.length === 3 ? { kind: 'key', msg: nums[0], wParam: nums[1], lParam: nums[2] } : null;
    case 'a':
      return nums.length === 1 ? { kind: 'ack', seq: nums[0] } : null;
    default:
      return null;
  }
}

/** Only these messages are forwarded to the panel window; anything else is dropped. */
export const ALLOWED_MESSAGES = new Set([
  0x0100, 0x0101, 0x0102,                 // WM_KEYDOWN, WM_KEYUP, WM_CHAR
  0x0200, 0x0201, 0x0202, 0x0203,         // WM_MOUSEMOVE, WM_LBUTTON*
  0x0204, 0x0205, 0x0206,                 // WM_RBUTTON*
  0x0207, 0x0208, 0x0209,                 // WM_MBUTTON*
  0x020a,                                 // WM_MOUSEWHEEL
]);

/** lParam for a mouse message: client coordinates packed as two signed 16-bit words. */
export function mouseLParam(cx, cy) {
  return ((cy & 0xffff) * 0x10000 + (cx & 0xffff)) >>> 0;
}
