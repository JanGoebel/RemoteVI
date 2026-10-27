#!/usr/bin/env node
// RemoteVI performance check: measures a running server the way a browser uses it.
//
//   node tools/perf.mjs [--url http://127.0.0.1:8088] [--seconds 5]
//                       [--click x,y --roi x,y,w,h] [--repeat 10]
//                       [--type x,y --type-roi x,y,w,h] [--hover x,y,w,h] [--ack-delay ms] [--json]
//
// stream  (always)   frames per second, gaps between frames, bytes and rects per frame,
//                    with a client that acks each frame right after decoding it
// click   (--click)  input-to-photon: a click (move, down, up) at x,y in frame
//                    coordinates, until a FRAME changes a pixel inside --roi; repeated
//                    --repeat times, 700 ms apart (use a toggle such as a boolean switch)
// type    (--type)   the same for a key: clicks x,y once (a string control), then types
//                    one character per round and waits for --type-roi to change
// hover   (--hover)  sends a mouse move every 16 ms (one per browser animation frame)
//                    across the rectangle for --seconds and reports the frame gaps while
//                    it does, against the idle gaps of the stream phase
//
// --ack-delay delays each ack, as a slow browser would. All coordinates are frame
// coordinates (docs/protocol.md). Numbers: docs/testing.md, Performance.

import { parseArgs } from 'node:util';
import { inflateSync } from 'node:zlib';

const { values: opt } = parseArgs({
  options: {
    url: { type: 'string', default: 'http://127.0.0.1:8088' },
    seconds: { type: 'string', default: '5' },
    click: { type: 'string' }, type: { type: 'string' }, roi: { type: 'string' }, 'type-roi': { type: 'string' },
    repeat: { type: 'string', default: '10' }, hover: { type: 'string' },
    'ack-delay': { type: 'string', default: '0' }, json: { type: 'boolean', default: false },
  },
});
const nums = (s) => (s ? s.split(',').map(Number) : null);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => performance.now();

/** Decode an 8-bit RGB/RGBA PNG (any filter) into 0xRRGGBB pixels. */
function decodePng(png) {
  let o = 8, w = 0, h = 0, colorType = 0;
  const idat = [];
  while (o < png.length) {
    const len = png.readUInt32BE(o);
    const type = png.toString('latin1', o + 4, o + 8);
    if (type === 'IHDR') { w = png.readUInt32BE(o + 8); h = png.readUInt32BE(o + 12); colorType = png[o + 17]; }
    if (type === 'IDAT') idat.push(png.subarray(o + 8, o + 8 + len));
    o += 12 + len;
  }
  const bpp = colorType === 6 ? 4 : 3, stride = w * bpp;
  const raw = inflateSync(Buffer.concat(idat));
  const out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)], ri = y * (stride + 1) + 1, oi = y * stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[oi + x - bpp] : 0, b = y ? out[oi - stride + x] : 0;
      const c = x >= bpp && y ? out[oi - stride + x - bpp] : 0;
      let p = 0;
      if (f === 1) p = a; else if (f === 2) p = b; else if (f === 3) p = (a + b) >> 1;
      else if (f === 4) { const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c); p = pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      out[oi + x] = (raw[ri + x] + p) & 0xff;
    }
  }
  const px = new Uint32Array(w * h);
  for (let i = 0; i < w * h; i++) px[i] = (out[i * bpp] << 16) | (out[i * bpp + 1] << 8) | out[i * bpp + 2];
  return { w, h, px };
}

const stats = (a) => {
  if (!a.length) return { n: 0 };
  const s = [...a].sort((x, y) => x - y), q = (f) => Math.round(s[Math.min(s.length - 1, Math.floor(s.length * f))]);
  return { n: s.length, min: Math.round(s[0]), median: q(0.5), p90: q(0.9), max: Math.round(s.at(-1)) };
};

// --- client ----------------------------------------------------------------------

const ws = new WebSocket(`${opt.url.replace(/^http/, 'ws')}/ws`);
ws.binaryType = 'arraybuffer';
const st = { width: 0, height: 0, img: null, frames: [], waiters: [], log: false };
ws.onmessage = (ev) => {
  if (typeof ev.data === 'string') return;
  const t = now(), v = new DataView(ev.data), type = v.getUint8(1);
  if (type === 3) { setTimeout(() => ws.send(`a ${v.getUint32(6)}`), Number(opt['ack-delay'])); return; }
  if (type !== 1) return;
  const w = v.getUint16(6), h = v.getUint16(8);
  if (w !== st.width || h !== st.height) { st.width = w; st.height = h; st.img = new Uint32Array(w * h); }
  let o = 12, area = 0;
  const rects = [];
  for (let i = 0, n = v.getUint16(10); i < n; i++) {
    const x = v.getInt16(o), y = v.getInt16(o + 2), len = v.getUint32(o + 4);
    const d = decodePng(Buffer.from(ev.data, o + 8, len));
    for (let r = 0; r < d.h; r++) st.img.set(d.px.subarray(r * d.w, (r + 1) * d.w), (y + r) * w + x);
    rects.push({ x, y, w: d.w, h: d.h });
    area += d.w * d.h;
    o += 8 + len;
  }
  const f = { t, seq: v.getUint32(2), bytes: ev.data.byteLength, rects, area };
  st.frames.push(f);
  setTimeout(() => ws.send(`a ${f.seq}`), Number(opt['ack-delay']));
  for (const wt of [...st.waiters]) wt(f);
};
await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = () => reject(new Error(`cannot connect to ${opt.url}`));
});

const roiKey = ([x, y, w, h]) => {
  let k = '';
  for (let r = y; r < y + h; r++) k += Buffer.from(st.img.buffer, (r * st.width + x) * 4, w * 4).toString('hex');
  return k;
};
/** Resolves with the time of the first frame after `since` that changes the roi, or null. */
function waitRoiChange(roi, ms = 3000) {
  const before = roiKey(roi);
  return new Promise((resolve) => {
    const timer = setTimeout(() => { st.waiters.splice(st.waiters.indexOf(on), 1); resolve(null); }, ms);
    const on = (f) => {
      if (roiKey(roi) === before) return;
      clearTimeout(timer);
      st.waiters.splice(st.waiters.indexOf(on), 1);
      resolve(f.t);
    };
    st.waiters.push(on);
  });
}

const report = { url: opt.url };
await sleep(1000); // first full frame and the greeting

// --- stream -------------------------------------------------------------------------
{
  const from = st.frames.length, t0 = now();
  await sleep(Number(opt.seconds) * 1000);
  const fs = st.frames.slice(from);
  const gaps = fs.slice(1).map((f, i) => f.t - fs[i].t);
  report.stream = {
    frame: `${st.width}x${st.height}`, fps: +(fs.length / ((now() - t0) / 1000)).toFixed(1), gaps: stats(gaps),
    bytesPerFrame: stats(fs.map((f) => f.bytes)), rectsPerFrame: stats(fs.map((f) => f.rects.length)),
    pixelsPerFrame: stats(fs.map((f) => f.area)),
  };
}

// --- click / type: input-to-photon ----------------------------------------------------
async function rounds(name, roi, act) {
  const lat = [], first = [];
  let missed = 0;
  for (let i = 0; i < Number(opt.repeat); i++) {
    const wait = waitRoiChange(roi);
    const n0 = st.frames.length;
    const t0 = now();
    act(i);
    const t = await wait;
    if (t === null) missed++; else lat.push(t - t0);
    if (st.frames.length > n0) first.push(st.frames[n0].t - t0);
    await sleep(700);
  }
  report[name] = { ...stats(lat), missed };
  report[`${name} (first frame after input)`] = stats(first);
}
if (opt.click) {
  const [x, y] = nums(opt.click);
  await rounds('click', nums(opt.roi), () => {
    ws.send(`m 512 ${x} ${y} 0`);
    ws.send(`m 513 ${x} ${y} 1`);
    ws.send(`m 514 ${x} ${y} 0`);
  });
}
if (opt.type) {
  const [x, y] = nums(opt.type);
  ws.send(`m 512 ${x} ${y} 0`); ws.send(`m 513 ${x} ${y} 1`); ws.send(`m 514 ${x} ${y} 0`);
  await sleep(700);
  await rounds('type', nums(opt['type-roi']), (i) => ws.send(`k 258 ${'abcdefghij'.charCodeAt(i % 10)} 1`));
  for (let i = 0; i < Number(opt.repeat); i++) { ws.send('k 256 8 1'); ws.send('k 257 8 3221225473'); }
}

// --- hover: frame gaps under a move flood ---------------------------------------------
if (opt.hover) {
  const [x, y, w, h] = nums(opt.hover);
  const from = st.frames.length, t0 = now();
  let i = 0;
  while (now() - t0 < Number(opt.seconds) * 1000) {
    const k = i++ % 120, f = k < 60 ? k / 60 : (120 - k) / 60;
    ws.send(`m 512 ${Math.round(x + f * w)} ${Math.round(y + (i % 7) / 6 * h)} 0`);
    while (now() < t0 + i * 16) await sleep(1);
  }
  const fs = st.frames.slice(from);
  report.hover = { moves: i, fps: +(fs.length / ((now() - t0) / 1000)).toFixed(1), gaps: stats(fs.slice(1).map((f, j) => f.t - fs[j].t)) };
  ws.send(`m 512 ${x + w + 5} ${y + h + 5} 0`);
}

ws.close();
if (opt.json) console.log(JSON.stringify(report));
else {
  const line = (k, v) => console.log(`${k.padEnd(18)} ${typeof v === 'object' ? Object.entries(v).map(([a, b]) => `${a} ${typeof b === 'object' ? JSON.stringify(b) : b}`).join(', ') : v}`);
  for (const [k, v] of Object.entries(report)) {
    if (k === 'stream') for (const [a, b] of Object.entries(v)) line(`stream ${a}`, b);
    else line(k, v);
  }
}
process.exit(0);
