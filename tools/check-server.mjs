#!/usr/bin/env node
// Black-box acceptance check for a running RemoteVI server (the LabVIEW toolkit
// or the reference server): HTTP surface, first frame, flow control, input.
//
//   node tools/check-server.mjs [--url http://127.0.0.1:8080] [--png first.png]
//        [--click x,y]   also click at panel pixel (x,y) and expect a changed frame
//
// Exit code 0 when every check passes. Prints one line per check.

import net from 'node:net';
import fs from 'node:fs';
import { inflateSync } from 'node:zlib';
import { parseArgs } from 'node:util';

const { values } = parseArgs({
  options: {
    url: { type: 'string', default: 'http://127.0.0.1:8080' },
    png: { type: 'string' },
    click: { type: 'string' },
  },
});
const base = new URL(values.url);
const host = base.hostname;
const port = Number(base.port || 80);
let failures = 0;

function check(ok, what, detail = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${what}${detail ? `  (${detail})` : ''}`);
  if (!ok) failures++;
}

function raw(text, ms = 3000) {
  return new Promise((resolve) => {
    const s = net.connect(port, host, () => s.write(text));
    const chunks = [];
    const done = () => resolve(Buffer.concat(chunks).toString('latin1'));
    s.setTimeout(ms, () => { s.destroy(); done(); });
    s.on('data', (d) => chunks.push(d));
    s.on('end', done);
    s.on('error', done);
  });
}

// --- PNG decoding (all five filter types; 8-bit RGB or RGBA) --------------------

function decodePng(png) {
  if (png.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG');
  let o = 8, w = 0, h = 0, colorType = 0, depth = 0;
  const idat = [];
  while (o < png.length) {
    const len = png.readUInt32BE(o);
    const type = png.subarray(o + 4, o + 8).toString('latin1');
    const data = png.subarray(o + 8, o + 8 + len);
    if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); depth = data[8]; colorType = data[9]; }
    if (type === 'IDAT') idat.push(data);
    o += 12 + len;
  }
  if (depth !== 8 || (colorType !== 2 && colorType !== 6)) throw new Error(`unsupported PNG depth ${depth} type ${colorType}`);
  const bpp = colorType === 6 ? 4 : 3;
  const raw = inflateSync(Buffer.concat(idat));
  const stride = w * bpp;
  const out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    const line = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[y * stride + x - bpp] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = x >= bpp && y > 0 ? out[(y - 1) * stride + x - bpp] : 0;
      let p;
      switch (f) {
        case 0: p = 0; break;
        case 1: p = a; break;
        case 2: p = b; break;
        case 3: p = (a + b) >> 1; break;
        case 4: { const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c);
          p = pa <= pb && pa <= pc ? a : pb <= pc ? b : c; break; }
        default: throw new Error(`bad filter ${f}`);
      }
      out[y * stride + x] = (line[x] + p) & 0xff;
    }
  }
  return { w, h };
}

function decodeFrame(buf) {
  const b = Buffer.from(buf);
  if (b[0] !== 0x52 || b[1] !== 1) throw new Error('bad frame magic/type');
  const f = { seq: b.readUInt32BE(2), width: b.readUInt16BE(6), height: b.readUInt16BE(8), rects: [], bytes: b.length };
  let o = 12;
  for (let i = 0, n = b.readUInt16BE(10); i < n; i++) {
    const len = b.readUInt32BE(o + 4);
    const png = b.subarray(o + 8, o + 8 + len);
    f.rects.push({ x: b.readInt16BE(o), y: b.readInt16BE(o + 2), png, ...decodePng(png) });
    o += 8 + len;
  }
  if (o !== b.length) throw new Error('trailing bytes in frame');
  return f;
}

// --- checks ------------------------------------------------------------------

const index = await raw(`GET / HTTP/1.1\r\nHost: ${host}:${port}\r\n\r\n`);
check(/^HTTP\/1\.[01] 200/.test(index), 'GET / -> 200', index.split('\r\n')[0]);
check(/<canvas id="panel"/.test(index), 'GET / serves the web client');
check(/content-security-policy:/i.test(index) && /x-content-type-options: nosniff/i.test(index), 'security headers present');

const notFound = await raw(`GET /nope HTTP/1.1\r\nHost: ${host}:${port}\r\n\r\n`);
check(/^HTTP\/1\.[01] 404/.test(notFound), 'GET /nope -> 404', notFound.split('\r\n')[0]);

const cross = await raw(`GET /ws HTTP/1.1\r\nHost: ${host}:${port}\r\nOrigin: http://evil.example\r\nUpgrade: websocket\r\n`
  + 'Connection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n');
check(/^HTTP\/1\.[01] 403/.test(cross), 'cross-origin upgrade -> 403', cross.split('\r\n')[0]);

const ws = new WebSocket(`ws://${host}:${port}/ws`);
ws.binaryType = 'arraybuffer';
const inbox = [];
let wake = null;
ws.onmessage = (ev) => { inbox.push(ev.data); wake?.(); };
const opened = await new Promise((r) => { ws.onopen = () => r(true); ws.onerror = () => r(false); setTimeout(() => r(false), 3000); });
check(opened, 'WebSocket upgrade on /ws');
if (!opened) process.exit(1);

async function nextMessage(pred, ms) {
  const end = Date.now() + ms;
  for (;;) {
    const i = inbox.findIndex(pred);
    if (i >= 0) return inbox.splice(i, 1)[0];
    const left = end - Date.now();
    if (left <= 0) return null;
    await new Promise((r) => { wake = r; setTimeout(r, left); });
  }
}
const isFrame = (m) => typeof m !== 'string';

const title = await nextMessage((m) => typeof m === 'string' && m.startsWith('title '), 3000);
check(title !== null, 'title message', title ?? 'none');

const t0 = Date.now();
const firstRaw = await nextMessage(isFrame, 5000);
check(firstRaw !== null, 'first frame arrives', firstRaw ? `${Date.now() - t0} ms` : 'timeout');
if (!firstRaw) process.exit(1);
let first;
try {
  first = decodeFrame(firstRaw);
  check(true, 'first frame decodes', `seq ${first.seq}, ${first.width}x${first.height}, ${first.rects.length} rect(s), ${first.bytes} bytes`);
} catch (err) {
  check(false, 'first frame decodes', err.message);
  process.exit(1);
}
check(first.seq === 1, 'first frame has seq 1', String(first.seq));
const covered = first.rects.reduce((n, r) => n + r.w * r.h, 0);
check(covered === first.width * first.height && first.rects[0].x === 0 && first.rects[0].y === 0,
  'first frame covers the whole panel', `${covered} of ${first.width * first.height} px`);
if (values.png && first.rects.length === 1) fs.writeFileSync(values.png, first.rects[0].png);

// Flow control: without acks, at most 2 frames may be outstanding.
await new Promise((r) => setTimeout(r, 1500));
const unacked = inbox.filter(isFrame).length + 1;
check(unacked <= 2, 'flow control: <= 2 frames without ack', `${unacked} received`);

// Ack everything and keep the stream going.
let lastSeq = first.seq;
for (const m of inbox.splice(0).filter(isFrame)) lastSeq = Math.max(lastSeq, decodeFrame(m).seq);
ws.send(`a ${lastSeq}`);

// Malformed input must not kill the session.
ws.send('this is not a command');
ws.send('m 16 1 1 0');

if (values.click) {
  const [x, y] = values.click.split(',').map(Number);
  ws.send(`m 512 ${x} ${y} 0`);
  ws.send(`m 513 ${x} ${y} 1`);
  ws.send(`m 514 ${x} ${y} 0`);
  const changed = await nextMessage(isFrame, 3000);
  check(changed !== null, `click at ${x},${y} produces a new frame`,
    changed ? `${decodeFrame(changed).rects.length} rect(s), ${changed.byteLength} bytes` : 'no frame within 3 s');
}

await new Promise((r) => setTimeout(r, 300));
check(ws.readyState === WebSocket.OPEN, 'session survives malformed and disallowed input');
ws.close();

console.log(failures ? `${failures} check(s) failed` : 'all checks passed');
process.exit(failures ? 1 : 0);
