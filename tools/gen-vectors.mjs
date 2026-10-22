#!/usr/bin/env node
// Generates tests/vectors/*.json - the shared, language-neutral test data used by
// both the JS tests (tests/js) and the Caraya unit tests (tests/caraya).
//
//   node tools/gen-vectors.mjs           write vectors
//   node tools/gen-vectors.mjs --check   exit 1 if committed vectors are stale
//
// Byte strings are lowercase hex. Pixels are 0x00RRGGBB integers, row-major.
// Expected values come from independent oracles where one exists (node:crypto
// for SHA-1/Base64, RFC 6455 / RFC 4648 examples); QOI and tile vectors come
// from the reference implementation and are cross-checked by the round-trip tests.

import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

import { encodeQoi } from './lib/qoi-encode.mjs';
import { diffTiles, encodeTile, tileGrid } from './lib/tiles.mjs';
import { encodeFrame, FRAME_FLAG_KEYFRAME } from '../web/js/protocol.js';
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

// --- SHA-1 / Base64 (WebSocket handshake building blocks) ----------------------

function sha1Vectors() {
  // Lengths 55/56/63/64/65 straddle the SHA-1 padding boundaries - the classic bug spot.
  const inputs = ['', 'abc', 'The quick brown fox jumps over the lazy dog',
    'a'.repeat(55), 'a'.repeat(56), 'a'.repeat(63), 'a'.repeat(64), 'a'.repeat(65), 'a'.repeat(1000),
    'dGhlIHNhbXBsZSBub25jZQ==258EAFA5-E914-47DA-95CA-C5AB0DC85B11'];
  return {
    description: 'SHA-1 digests. input is ASCII; digest is hex.',
    cases: inputs.map((input) => ({ input, digest: createHash('sha1').update(input, 'latin1').digest('hex') })),
  };
}

function base64Vectors() {
  const strings = ['', 'f', 'fo', 'foo', 'foob', 'fooba', 'foobar']; // RFC 4648 section 10
  const binary = [[0], [0xff, 0xfe], [0xfb, 0xff, 0xbf], Array.from({ length: 20 }, (_, i) => i * 13)];
  return {
    description: 'Standard Base64 with padding. bytes is hex.',
    cases: [
      ...strings.map((s) => ({ bytes: hex(Buffer.from(s, 'latin1')), base64: Buffer.from(s, 'latin1').toString('base64') })),
      ...binary.map((b) => ({ bytes: hex(b), base64: Buffer.from(b).toString('base64') })),
    ],
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

// --- QOI / tiles / frames ---------------------------------------------------------

function image(w, h, fn) {
  const px = new Uint32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) px[y * w + x] = fn(x, y) & 0xffffff;
  return px;
}

function qoiVectors() {
  const rnd = mulberry32(42);
  const palette = [0xe6e6e6, 0x000000, 0xffffff, 0x2ecc40, 0x1f6feb];
  const images = [
    { name: '1x1 black (initial pixel run)', w: 1, h: 1, px: image(1, 1, () => 0) },
    { name: '1x1 white (wraparound OP_DIFF)', w: 1, h: 1, px: image(1, 1, () => 0xffffff) },
    { name: '1x1 mid grey (OP_RGB)', w: 1, h: 1, px: image(1, 1, () => 0x808080) },
    { name: 'solid 8x8 panel grey', w: 8, h: 8, px: image(8, 8, () => 0xe6e6e6) },
    { name: 'run longer than 62', w: 100, h: 1, px: image(100, 1, (x) => (x === 0 ? 0x123456 : 0xabcdef)) },
    { name: 'small diffs (OP_DIFF)', w: 16, h: 1, px: image(16, 1, (x) => ((100 + (x % 2)) << 16) | ((100 - (x % 3 === 0 ? 1 : 0)) << 8) | (100 + (x & 1))) },
    { name: 'gradient (OP_LUMA)', w: 16, h: 4, px: image(16, 4, (x, y) => ((x * 12) << 16) | ((y * 40 + x * 10) << 8) | (x * 11)) },
    { name: 'palette alternation (OP_INDEX)', w: 12, h: 3, px: image(12, 3, (x, y) => palette[(x + y) % palette.length]) },
    { name: 'wraparound diffs', w: 4, h: 1, px: image(4, 1, (x) => [0x000000, 0xffffff, 0x000000, 0x010101][x]) },
    { name: 'random 13x7', w: 13, h: 7, px: image(13, 7, () => Math.floor(rnd() * 0x1000000)) },
  ];
  return {
    description: 'QOI encodings (3 channels, sRGB) of 0x00RRGGBB pixel arrays. The G encoder must be byte-identical.',
    cases: images.map(({ name, w, h, px }) => ({ name, width: w, height: h, pixels: Array.from(px), qoi: hex(encodeQoi(px, w, { x: 0, y: 0, w, h })) })),
  };
}

function tileVectors() {
  // 100x40 with 32 px tiles: a 4x2 grid whose right column and bottom row are clipped.
  const w = 100, h = 40, size = 32;
  const base = image(w, h, (x, y) => (x < 50 ? 0xe6e6e6 : ((x * 3) << 16) | (y << 8)));
  const changed = base.slice();
  changed[5 * w + 98] = 0xff0000; // tile (96,0), the clipped 4x32 one
  changed[39 * w + 0] = 0x00ff00; // tile (0,32), the clipped 32x8 one
  return {
    description: 'Tile grid / diff / per-tile encoding. encoding: 0 SOLID, 1 QOI, 2 RAW_RGB.',
    tileSize: size,
    grid: { width: w, height: h, tiles: tileGrid(w, h, size) },
    diff: {
      width: w, height: h, before: Array.from(base), after: Array.from(changed),
      dirty: diffTiles(base, changed, w, h, size).map(({ x, y, w: tw, h: th }) => ({ x, y, w: tw, h: th })),
    },
    // Each tile of diff.before, encoded.
    encodeTile: tileGrid(w, h, size).map((t) => {
      const e = encodeTile(base, w, t);
      return { ...t, encoding: e.encoding, data: hex(e.data) };
    }),
  };
}

function frameVectors() {
  // 12x4 panel, three 4x4 tiles: flat colour (SOLID), smooth gradient (QOI), noise (RAW).
  const rnd = mulberry32(7);
  const px = image(12, 4, (x, y) => (x < 4 ? 0x336699 : x < 8 ? (x << 8) | y : Math.floor(rnd() * 0x1000000)));
  const tiles = [0, 4, 8].map((x) => encodeTile(px, 12, { x, y: 0, w: 4, h: 4 }));
  return {
    description: 'Complete FRAME messages (docs/protocol.md section 3).',
    cases: [{
      name: 'keyframe with one SOLID, one QOI and one RAW_RGB tile',
      flags: FRAME_FLAG_KEYFRAME, seq: 7, width: 12, height: 4,
      pixels: Array.from(px),
      tiles: tiles.map((t) => ({ x: t.x, y: t.y, w: t.w, h: t.h, encoding: t.encoding, data: hex(t.data) })),
      message: hex(encodeFrame({ flags: FRAME_FLAG_KEYFRAME, seq: 7, width: 12, height: 4, tiles })),
    }],
  };
}

export function buildVectors() {
  return {
    'sha1.json': sha1Vectors(),
    'base64.json': base64Vectors(),
    'websocket.json': websocketVectors(),
    'http.json': httpVectors(),
    'qoi.json': qoiVectors(),
    'tiles.json': tileVectors(),
    'frame.json': frameVectors(),
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
