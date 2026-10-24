#!/usr/bin/env node
// Generates tests/vectors/*.json - the shared, language-neutral test data used by
// both the JS tests (tests/js) and the Caraya unit tests (tests/caraya).
//
//   node tools/gen-vectors.mjs           write vectors
//   node tools/gen-vectors.mjs --check   exit 1 if committed vectors are stale
//
// Byte strings are lowercase hex. Pixels are 0x00RRGGBB integers, row-major.
// Expected values come from independent oracles where one exists (RFC 6455
// examples); rect, frame and input vectors come from the reference implementation
// in tools/lib.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { dirtyRects } from './lib/rects.mjs';
import { encodeFrame, encodeOverlay, parseInput, mouseLParam } from './lib/protocol.mjs';
import { translateInput, trackModifiers } from './lib/input.mjs';
import { acceptKey, encodeServerFrame } from './lib/websocket.mjs';
import { LIMITS } from './lib/http.mjs';

const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../tests/vectors');
const hex = (u8) => Buffer.from(u8).toString('hex');

function mulberry32(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = seed;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// --- WebSocket ---------------------------------------------------------------------

function maskFrame(opcode, payload, mask, { fin = true, rsv = 0 } = {}) {
  const p = Buffer.from(payload);
  const len = p.length;
  const head = len < 126 ? [len | 0x80] : len < 65536 ? [126 | 0x80, len >> 8, len & 0xff] : null;
  const out = Buffer.from([(fin ? 0x80 : 0) | rsv | opcode, ...head, ...mask]);
  const body = Buffer.alloc(len);
  for (let i = 0; i < len; i++) body[i] = p[i] ^ mask[i & 3];
  return Buffer.concat([out, body]);
}

function websocketVectors() {
  const mask = [0x37, 0xfa, 0x21, 0x3d];
  const long = Buffer.alloc(300, 0x61);
  return {
    description: 'RFC 6455 handshake and framing. frame/payload are hex. error is the close code the server must send.',
    accept: [
      { key: 'dGhlIHNhbXBsZSBub25jZQ==', accept: 's3pPLMBiTxaQ9kYGzzhZRbK+xOo=' }, // RFC 6455 section 1.3
      { key: 'x3JJHMbDL1EzLkh9GBhXDw==', accept: acceptKey('x3JJHMbDL1EzLkh9GBhXDw==') },
    ],
    clientFrames: [
      { name: 'masked text Hello (RFC 6455 5.7)', frame: '818537fa213d7f9f4d5158', fin: true, opcode: 1, payload: hex(Buffer.from('Hello')) },
      { name: 'masked ping', frame: hex(maskFrame(9, 'hi', mask)), fin: true, opcode: 9, payload: hex(Buffer.from('hi')) },
      { name: 'masked close 1000', frame: hex(maskFrame(8, [0x03, 0xe8], mask)), fin: true, opcode: 8, payload: '03e8' },
      { name: '16-bit length', frame: hex(maskFrame(1, long, mask)), fin: true, opcode: 1, payload: hex(long) },
      { name: 'empty text', frame: hex(maskFrame(1, '', mask)), fin: true, opcode: 1, payload: '' },
      { name: 'unmasked (RFC 6455 5.7, client->server forbidden)', frame: '810548656c6c6f', error: 1002 },
      { name: 'RSV1 set', frame: hex(maskFrame(1, 'x', mask, { rsv: 0x40 })), error: 1002 },
      { name: 'reserved opcode 3', frame: hex(maskFrame(3, 'x', mask)), error: 1002 },
      { name: 'fragmented ping', frame: hex(maskFrame(9, 'x', mask, { fin: false })), error: 1002 },
      { name: 'control frame > 125 bytes', frame: hex(maskFrame(9, Buffer.alloc(126), mask)), error: 1002 },
      { name: '64-bit length beyond limit', frame: '81ff' + '0000000100000000' + '00000000', error: 1009 },
    ],
    incompleteClientFrames: ['', '81', '81fe', '81fe01', '8185', '818537fa', '818537fa213d7f9f4d51'],
    serverFrames: [
      { name: 'text Hello (RFC 6455 5.7)', opcode: 1, payload: hex(Buffer.from('Hello')), frame: '810548656c6c6f' },
      { name: 'binary 256 bytes (RFC 6455 5.7)', opcode: 2, payload: hex(Buffer.alloc(256)), frame: hex(encodeServerFrame(2, Buffer.alloc(256))) },
      { name: 'binary 65536 bytes header', opcode: 2, payloadLength: 65536, header: '827f0000000000010000' },
      { name: 'close 1000', opcode: 8, payload: '03e8', frame: '880203e8' },
    ],
  };
}

// --- HTTP -------------------------------------------------------------------------------

function httpVectors() {
  const ok = 'GET /ws HTTP/1.1\r\nHost: 127.0.0.1:8080\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
    + 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n';
  const manyHeaders = 'GET / HTTP/1.1\r\n' + Array.from({ length: LIMITS.maxHeaders + 1 }, (_, i) => `X-H${i}: v`).join('\r\n') + '\r\n\r\n';
  return {
    description: 'Request heads (latin1 text) and the expected parse result or HTTP error status.',
    limits: LIMITS,
    cases: [
      { name: 'websocket upgrade', head: ok, path: '/ws', upgrade: true },
      { name: 'static file with query', head: 'GET /js/client.js?v=1 HTTP/1.1\r\nHost: x\r\n\r\n', path: '/js/client.js', upgrade: false },
      { name: 'POST rejected', head: 'POST / HTTP/1.1\r\nHost: x\r\n\r\n', status: 405 },
      { name: 'HTTP/2 preface rejected', head: 'PRI * HTTP/2.0\r\n\r\n', status: 505 },
      { name: 'absolute-form rejected', head: 'GET http://evil/ HTTP/1.1\r\nHost: x\r\n\r\n', status: 400 },
      { name: 'garbage request line', head: 'GET\r\n\r\n', status: 400 },
      { name: 'header without colon', head: 'GET / HTTP/1.1\r\nHost x\r\n\r\n', status: 400 },
      { name: 'duplicate Host', head: 'GET / HTTP/1.1\r\nHost: a\r\nHost: b\r\n\r\n', status: 400 },
      { name: 'too many headers', head: manyHeaders, status: 431 },
      { name: 'URI too long', head: `GET /${'a'.repeat(LIMITS.maxPathBytes)} HTTP/1.1\r\nHost: x\r\n\r\n`, status: 414 },
      { name: 'path traversal is just an unknown path', head: 'GET /../../etc/passwd HTTP/1.1\r\nHost: x\r\n\r\n', path: '/../../etc/passwd', upgrade: false },
    ],
  };
}

// --- dirty rects / frames / input ------------------------------------------------

function image(w, h, fn) {
  const px = new Uint32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) px[y * w + x] = fn(x, y) & 0xffffff;
  return px;
}

function rectVectors() {
  // 10x7 panel with 4x4 tiles: tile grid is 3 columns (4,4,2) x 2 rows (4,3).
  const w = 10, h = 7, tile = 4;
  const base = image(w, h, (x, y) => 0x101010 * ((x + y) % 4));
  const change = (pts) => {
    const px = base.slice();
    for (const [x, y] of pts) px[y * w + x] ^= 0xffffff;
    return px;
  };
  const cases = [
    { name: 'no previous capture: whole panel', prev: null, pts: [] },
    { name: 'identical: nothing dirty', prev: base, pts: [] },
    { name: 'one pixel in the first tile', prev: base, pts: [[1, 1]] },
    { name: 'first and last tile of a row merge into one band', prev: base, pts: [[0, 0], [9, 3]] },
    { name: 'clipped bottom-right tile', prev: base, pts: [[9, 6]] },
    { name: 'one band per tile row', prev: base, pts: [[5, 0], [0, 6]] },
  ];
  return {
    description: 'Capture/Dirty Rects.vi. pixels are 0x00RRGGBB row-major; prev null means no previous capture. '
      + 'Dirty tiles of each tile row are merged into one rectangle spanning first to last dirty tile.',
    width: w, height: h, tileSize: tile, prev: Array.from(base),
    cases: cases.map((c) => {
      const cur = change(c.pts);
      return { name: c.name, hasPrev: c.prev !== null, cur: Array.from(cur), rects: dirtyRects(c.prev, cur, w, h, tile) };
    }),
  };
}

function frameVectors() {
  const png1 = Buffer.from('89504e470d0a1a0a', 'hex'); // stand-ins: the frame layout does not look inside
  const png2 = Buffer.from('0102030405', 'hex');
  const rects = [{ x: 0, y: 0, png: png1 }, { x: 640, y: 64, png: png2 }];
  return {
    description: 'Protocol/Frame Encode.vi and Overlay Encode.vi: complete FRAME and OVERLAY messages (docs/protocol.md). png/message are hex.',
    cases: [
      { name: 'two rects', seq: 7, width: 800, height: 600,
        rects: rects.map((r) => ({ x: r.x, y: r.y, png: hex(r.png) })), message: hex(encodeFrame(7, 800, 600, rects)) },
      { name: 'no rects, large seq', seq: 4294967295, width: 1, height: 1, rects: [], message: hex(encodeFrame(4294967295, 1, 1, [])) },
    ],
    overlays: [
      { name: 'two popups, one partly outside the panel', popups: [{ x: 30, y: 140, png: hex(png1) }, { x: 790, y: -12, png: hex(png2) }],
        message: hex(encodeOverlay([{ x: 30, y: 140, png: png1 }, { x: 790, y: -12, png: png2 }])) },
      { name: 'clear', popups: [], message: hex(encodeOverlay([])) },
    ],
  };
}

function inputVectors() {
  const texts = [
    'm 513 120 45 1', 'm 512 0 0 0', 'm 522 10 20 4287102976', 'k 256 37 16777217', 'k 257 37 3238002689',
    'k 258 65 1', 'a 12', 'a', 'm 513 1 2', 'x 1 2 3', 'm 513 a b c', '', 'm 513 1.5 2 0',
    'a ', 'a  12', 'a 12 ', 'a 4294967295', 'a 4294967296', 'k 256 -2147483648 0', 'k 256 -2147483649 0', 'a 1x', 'a -', 'a 1e3',
  ];
  return {
    description: 'Protocol/Parse Input.vi. result null means: ignore the message. '
      + 'lParam is the mouse lParam for client point (cx, cy).',
    cases: texts.map((text) => ({ text, result: parseInput(text) })),
    mouseLParam: [[0, 0], [120, 45], [-5, 10], [1919, 1079]].map(([cx, cy]) => ({ cx, cy, lParam: mouseLParam(cx, cy) })),
  };
}

function translateVectors() {
  // Panel origin (100,200) on screen; client area origin (100,154): a 46 px toolbar.
  const geo = { panelX: 100, panelY: 200, clientX: 100, clientY: 154 };
  const steps = [
    ['hover', 'm 512 10 20 0', false],
    ['left down: client coords, starts tracking', 'm 513 10 20 1', false],
    ['drag move while LabVIEW tracks (mouse captured): screen coords', 'm 512 50 20 1', true],
    ['left up while LabVIEW tracks (mouse captured): screen coords, ends tracking', 'm 514 50 20 0', true],
    ['up without capture (e.g. a switch): client coords', 'm 514 50 20 0', false],
    ['double click down: client, tracking', 'm 515 10 20 1', false],
    ['right down', 'm 516 5 5 2', false],
    ['wheel: always screen coords', 'm 522 10 20 7864320', false],
    ['wheel while tracking', 'm 522 10 20 7864320', true],
    ['negative client y (toolbar area)', 'm 512 0 0 0', false],
    ['char is wrapped in VK 0xE8 down/up', 'k 258 65 1', false],
    ['special key passes through', 'k 256 13 1', false],
    ['key up passes through', 'k 257 37 3238002689', false],
    ['not allowed: WM_CLOSE', 'm 16 1 1 0', false],
    ['not allowed: WM_SYSKEYDOWN', 'k 260 18 1', false],
    ['ack: nothing to post', 'a 5', false],
    ['popup open: moves are dropped (host cursor stays put)', 'm 512 10 20 0', false, true],
    ['popup open: wheel is dropped', 'm 522 10 20 7864320', false, true],
    ['popup open: click outside the panel (negative coords) still maps', 'm 513 -30 600 1', false, true],
    ['popup open: down uses screen coords, cursor, tracking', 'm 513 10 20 1', false, true],
    ['popup open: up uses screen coords, cursor, ends tracking', 'm 514 10 20 0', true, true],
    ['popup open: char still wrapped, no cursor move', 'k 258 65 1', false, true],
  ];
  return {
    description: 'Input/Translate Input.vi. geo = panel and client-area origins in screen coordinates. '
      + 'input is a client message (see input.json); trackingBefore: LabVIEW tracks a press, i.e. its UI thread '
      + 'holds the mouse capture (the server reads it before translating); trackingAfter: button-down until button-up; '
      + 'popup: a LabVIEW popup is open; cursor: screen point to move the host cursor to first (null = do not move). '
      + 'lParam is unsigned 32-bit.',
    geo,
    cases: steps.map(([name, text, tracking, popup = false]) => {
      const r = translateInput(parseInput(text), geo, tracking, popup);
      return { name, input: text, popup, trackingBefore: tracking, trackingAfter: r.tracking, cursor: r.cursor, posts: r.posts };
    }),
    modifiersDescription: 'Input/RemoteVI Track Modifiers.vi: modifier keys held after the message (1 Shift, 2 Ctrl, 4 Alt).',
    modifiers: [
      ['Shift key down', 'k 256 16 1', 0],
      ['Shift key up', 'k 257 16 3221225473', 1],
      ['left Shift (VK_LSHIFT) down keeps Ctrl', 'k 256 160 1', 2],
      ['right Ctrl up', 'k 257 163 3238002689', 3],
      ['Alt down', 'k 256 18 1', 0],
      ['other key leaves mods', 'k 256 13 1', 5],
      ['char leaves mods', 'k 258 1 1', 2],
      ['mouse with MK_SHIFT', 'm 513 10 20 5', 0],
      ['mouse with MK_CONTROL keeps Alt, drops Shift', 'm 512 10 20 8', 5],
      ['mouse without flags clears Shift and Ctrl', 'm 514 10 20 0', 3],
      ['not allowed mouse message leaves mods', 'm 16 1 1 0', 3],
      ['ack leaves mods', 'a 5', 1],
    ].map(([name, text, before]) => ({ name, input: text, modsBefore: before, modsAfter: trackModifiers(parseInput(text), before) })),
  };
}

export function buildVectors() {
  return {
    'websocket.json': websocketVectors(),
    'http.json': httpVectors(),
    'rects.json': rectVectors(),
    'frame.json': frameVectors(),
    'input.json': inputVectors(),
    'translate.json': translateVectors(),
  };
}

/** Pretty JSON, but arrays of numbers stay on one line so pixel data remains compact. */
export function serialize(obj) {
  const walk = (v, indent) => {
    if (Array.isArray(v)) {
      if (v.every((e) => typeof e === 'number')) return `[${v.join(',')}]`;
      if (!v.length) return '[]';
      const pad = ' '.repeat(indent + 1);
      return `[\n${v.map((e) => pad + walk(e, indent + 1)).join(',\n')}\n${' '.repeat(indent)}]`;
    }
    if (v && typeof v === 'object') {
      const keys = Object.keys(v);
      if (!keys.length) return '{}';
      const pad = ' '.repeat(indent + 1);
      return `{\n${keys.map((k) => `${pad}${JSON.stringify(k)}: ${walk(v[k], indent + 1)}`).join(',\n')}\n${' '.repeat(indent)}}`;
    }
    return JSON.stringify(v);
  };
  return walk(obj, 0) + '\n';
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const check = process.argv.includes('--check');
  let stale = false;
  fs.mkdirSync(OUT, { recursive: true });
  for (const [name, data] of Object.entries(buildVectors())) {
    const file = path.join(OUT, name);
    const text = serialize(data);
    if (check) {
      if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== text) {
        console.error(`stale: tests/vectors/${name}`);
        stale = true;
      }
    } else {
      fs.writeFileSync(file, text);
      console.log(`wrote tests/vectors/${name}`);
    }
  }
  process.exit(stale ? 1 : 0);
}
