// Shared helpers for the LabVIEW integration tests (tests/lv/*.test.mjs).
//
// The tests drive tests/fixtures/RemoteVI Fixture.vi through the real RemoteVI server,
// exactly as the browser does, and check LabVIEW's side through the fixture's event log:
// every event its event structure handles is appended to a text file, one line per event.
//
// Log format (tab separated; the fixture truncates the file when it starts):
//   ready                                      server is up
//   layout   <label>  <x> <y> <w> <h>          control body in panel-image coordinates
//   value    <label>  <new value>              Value Change
//   mousedown|mouseup <label>  <x> <y> <button> <mods>
//   enter|leave       <label>
//   keydown  <label>  <char or VKey name>  <mods>
//   wheel    <label>  <delta>                  Mouse Wheel (positive = away from the user)
//   dblclick <label>  <row>                    Double Click (listbox)
//   menu     <label>  <item tag>               Shortcut Menu Selection (User)
//   menubar  <item tag>                        Menu Selection (User) of the VI's run-time menu bar
//   scroll   <x> <y>                           Front Panel Window:Origin changed (panel scrolled)
//   dialog   <TRUE|FALSE>                      answer of the Two Button Dialog opened by `Ask`
//   file     <path|CANCELLED>                  result of the native File Dialog opened by `Open`
//
// Coordinates: `layout` rectangles are panel coordinates. The stream shows the whole window
// below its title bar (menu bar, toolbar, panel, scrollbars); the server tells the client where
// the panel starts inside that frame with the text message `origin <x> <y>`, and layout(c)
// shifts the rectangles into frame coordinates.
// <mods> is a combination of S (shift), C (ctrl), A (alt), or "-" for none.
// Values: booleans TRUE/FALSE, numerics with %g, strings as typed (newlines as \n),
// rings and enums by item text, tab controls by page label.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { inflateSync } from 'node:zlib';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const URL_BASE = process.env.RVI_URL ?? 'http://127.0.0.1:8089';

/** The share's full link with its access token (docs/security.md): RVI_URL when it carries ?t=, else asked from
 *  the LabVIEW that runs the fixture (tools/lv-share-url.ps1 reads RemoteVI Status.vi over LabVIEW's ActiveX server). */
let shareUrl = null;
export function share() {
  if (shareUrl) return shareUrl;
  const u = new URL(URL_BASE);
  if (!u.searchParams.get('t')) {
    const script = fileURLToPath(new URL('../../tools/lv-share-url.ps1', import.meta.url));
    const out = execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script, '-Port', u.port || '80'],
      { encoding: 'utf8', timeout: 30000 }).trim();
    const found = new URL(out.split(/\r?\n/).at(-1));
    u.search = found.search;
  }
  shareUrl = u;
  return u;
}

/** ws://host:port/ws?t=<token> of the share. */
export function wsUrl() {
  const u = share();
  return `ws://${u.host}/ws?t=${encodeURIComponent(u.searchParams.get('t'))}`;
}
export let LOG_PATH = process.env.RVI_FIXTURE_LOG ?? path.join(os.tmpdir(), 'RemoteVI Fixture.log');
export const enabled = process.env.RVI_LV === '1';

/** Read another fixture's log from now on (the complex fixture writes RemoteVI Complex Fixture.log). */
export function useLog(p) {
  LOG_PATH = p;
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function readLog() {
  if (!fs.existsSync(LOG_PATH)) return [];
  return fs.readFileSync(LOG_PATH, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => line.split('\t'));
}

/** Control body rectangles from the fixture's layout lines (the latest line per label wins). */
export function layout(c, kinds = ['layout']) {
  const ox = c?.origin.x ?? 0, oy = c?.origin.y ?? 0;
  const map = new Map();
  for (const [kind, label, rect] of readLog()) {
    if (kinds.includes(kind) && rect) {
      let [x, y, w, h] = rect.split(' ').map(Number);
      x += ox; y += oy;
      map.set(label, { x, y, w, h, cx: Math.round(x + w / 2), cy: Math.round(y + h / 2) });
    }
  }
  return map;
}

/** Wait until a log line after `since` matches. Returns the line's fields. */
export async function waitLog(pred, { since = 0, ms = 3000 } = {}) {
  const end = Date.now() + ms;
  for (;;) {
    const hit = readLog().slice(since).find(pred);
    if (hit) return hit;
    if (Date.now() > end) throw new Error(`no matching log line within ${ms} ms; log tail:\n${readLog().slice(-8).map((l) => l.join(' | ')).join('\n')}`);
    await sleep(50);
  }
}

/** Paint the PNG rects of a FRAME or WINDOW FRAME message (rects at offset o) into the 0xRRGGBB buffer fb of width w. */
function paintRects(data, o, n, fb, w) {
  const v = new DataView(data);
  for (let i = 0; i < n; i++) {
    const x = v.getInt16(o), y = v.getInt16(o + 2), len = v.getUint32(o + 4);
    const img = decodePng(Buffer.from(data, o + 8, len));
    for (let yy = 0; yy < img.h; yy++) for (let xx = 0; xx < img.w; xx++) fb[(y + yy) * w + x + xx] = img.rgb(xx, yy);
    o += 8 + len;
  }
}

/** A protocol-v2 client like web/index.html: acks frames, keeps the latest overlay. With { fb: true } it also
 *  keeps the picture: c.fb (frame, 0xRRGGBB per pixel, c.width wide) and c.wfb (window id -> {w, h, fb}). */
export async function connect({ fb = false } = {}) {
  const ws = new WebSocket(wsUrl());
  ws.binaryType = 'arraybuffer';
  const c = { ws, overlay: [], overlays: 0, frames: 0, width: 0, height: 0, origin: { x: 0, y: 0 }, originSeen: false,
    windows: [], windowFrames: new Map(), tips: null, bars: null, fb: null, wfb: new Map() };
  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') {
      const m = /^origin (-?\d+) (-?\d+)$/.exec(ev.data);
      if (m) { c.origin = { x: Number(m[1]), y: Number(m[2]) }; c.originSeen = true; }
      // A window target (RemoteVI Start Window.vi) knows no panel origin (no VI Server): RVI_ORIGIN=x,y gives it.
      if (m && process.env.RVI_ORIGIN) { const [ox, oy] = process.env.RVI_ORIGIN.split(',').map(Number); c.origin = { x: ox, y: oy }; }
      if (ev.data.startsWith('windows ')) {
        try { c.windows = JSON.parse(ev.data.slice(8)); } catch { /* ignore */ }
      }
      if (ev.data.startsWith('tips ')) {
        try { c.tips = JSON.parse(ev.data.slice(5)); } catch { /* ignore */ }
      }
      if (ev.data.startsWith('splitters ')) {
        try { c.bars = JSON.parse(ev.data.slice(10)); } catch { /* ignore */ }
      }
      return;
    }
    if (new DataView(ev.data).getUint8(1) === 3) {
      const v = new DataView(ev.data);
      const id = v.getUint32(2);
      c.windowFrames.set(id, (c.windowFrames.get(id) ?? 0) + 1);
      if (fb) {
        const w = v.getUint16(10), h = v.getUint16(12);
        let pic = c.wfb.get(id);
        if (!pic || pic.w !== w || pic.h !== h) c.wfb.set(id, pic = { w, h, fb: new Uint32Array(w * h) });
        paintRects(ev.data, 16, v.getUint16(14), pic.fb, w);
      }
      ws.send(`a ${v.getUint32(6)}`);
      return;
    }
    const v = new DataView(ev.data);
    if (v.getUint8(1) === 2) {
      const popups = [];
      let o = 4;
      for (let i = 0, n = v.getUint16(2); i < n; i++) {
        const len = v.getUint32(o + 4);
        const png = Buffer.from(ev.data, o + 8, len);
        popups.push({ x: v.getInt16(o), y: v.getInt16(o + 2), w: png.readUInt32BE(16), h: png.readUInt32BE(20), png: Buffer.from(png) });
        o += 8 + len;
      }
      c.overlay = popups;
      c.overlays++;
    } else {
      c.frames++;
      const w = v.getUint16(6), h = v.getUint16(8);
      if (fb && (!c.fb || w !== c.width || h !== c.height)) c.fb = new Uint32Array(w * h);
      c.width = w;
      c.height = h;
      if (fb) paintRects(ev.data, 12, v.getUint16(10), c.fb, w);
      ws.send(`a ${v.getUint32(2)}`);
    }
  };
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = () => reject(new Error(`cannot connect to ${URL_BASE} - is the fixture running?`));
  });
  await sleep(300);
  return c;
}

const MK = { L: 1, R: 2, SHIFT: 4, CTRL: 8 };

export function move(c, x, y, wParam = 0) {
  c.ws.send(`m 512 ${Math.round(x)} ${Math.round(y)} ${wParam}`); // the server takes integers only
}

export async function click(c, x, y, { button = 'left', shift = false, ctrl = false, settle = 250 } = {}) {
  const mods = (shift ? MK.SHIFT : 0) | (ctrl ? MK.CTRL : 0);
  const [down, up, flag] = button === 'right' ? [516, 517, MK.R] : [513, 514, MK.L];
  x = Math.round(x); y = Math.round(y);
  move(c, x, y, mods);
  c.ws.send(`m ${down} ${x} ${y} ${flag | mods}`);
  c.ws.send(`m ${up} ${x} ${y} ${mods}`);
  await sleep(settle);
}

/** Press at (x0, y0), move in steps to (x1, y1) with the button held, release there. */
export async function drag(c, x0, y0, x1, y1, { steps = 8, stepMs = 30, settle = 400 } = {}) {
  [x0, y0, x1, y1] = [x0, y0, x1, y1].map(Math.round);
  move(c, x0, y0);
  await sleep(stepMs);
  c.ws.send(`m 513 ${x0} ${y0} ${MK.L}`);
  await sleep(stepMs * 2);
  for (let i = 1; i <= steps; i++) {
    const x = Math.round(x0 + ((x1 - x0) * i) / steps), y = Math.round(y0 + ((y1 - y0) * i) / steps);
    c.ws.send(`m 512 ${x} ${y} ${MK.L}`);
    await sleep(stepMs);
  }
  c.ws.send(`m 514 ${x1} ${y1} 0`);
  await sleep(settle);
}

/** The frame pixel at (x, y) as 0xRRGGBB (needs connect({ fb: true })). */
export const pixel = (c, x, y) => c.fb[y * c.width + x];

const gray = (p) => { const r = p >> 16, g = (p >> 8) & 255, b = p & 255; return r === g && g === b ? r : -1; };

/** LabVIEW's splitter bar as the frame shows it: a run of light grays fading to a dark gray edge
 *  (0xF8 .. 0xB5 then 0x87, 9 px wide). Returns the coordinate of the dark edge along the line
 *  given by at(i) for i in [from, to), or -1. */
function findBar(at, from, to) {
  for (let i = from + 8; i < to; i++) {
    const d = gray(at(i));
    if (d < 0x70 || d > 0x9a) continue;
    const l = gray(at(i - 7));
    if (l >= 0xf0) return i;
  }
  return -1;
}

/** The splitter bars on the frame: vertical ones crossing the row y, horizontal ones crossing the column x. */
export function splitters(c, { y, x }) {
  const vs = [], hs = [];
  for (let s = 0; s < c.width;) {
    const i = findBar((k) => pixel(c, k, y), s, c.width);
    if (i < 0) break;
    vs.push(i); s = i + 1;
  }
  for (let s = 0; s < c.height;) {
    const i = findBar((k) => pixel(c, x, k), s, c.height);
    if (i < 0) break;
    hs.push(i); s = i + 1;
  }
  return { vertical: vs, horizontal: hs };
}

/** Drag splitter bar `bar` (an entry of the splitters message) as web/index.html does: the client moves
 *  the bar itself and sends `s <id> <pos>` with the new left (vertical) or top (horizontal) edge. */
export async function dragSplitter(c, bar, delta, { settle = 1200 } = {}) {
  const pos = Math.max(bar.min, Math.min(bar.max, (bar.vertical ? bar.x : bar.y) + delta));
  c.ws.send(`s ${bar.id} ${pos}`);
  await sleep(settle);
  return pos;
}

export function keyDown(c, vk, extended = false) {
  c.ws.send(`k 256 ${vk} ${extended ? 0x01000001 : 1}`);
}

export function keyUp(c, vk, extended = false) {
  c.ws.send(`k 257 ${vk} ${(extended ? 0x01000001 : 1) + 0xc0000000}`);
}

export async function typeText(c, text) {
  for (const ch of text) {
    c.ws.send(`k 258 ${ch.charCodeAt(0)} 1`);
    await sleep(30);
  }
}

export async function waitOverlay(c, pred = (o) => o.length > 0, ms = 3000) {
  const end = Date.now() + ms;
  while (!pred(c.overlay)) {
    if (Date.now() > end) throw new Error(`overlay condition not met within ${ms} ms (have ${c.overlay.length} popup(s))`);
    await sleep(25);
  }
  return c.overlay;
}

export const VK = { BACK: 0x08, TAB: 0x09, ENTER: 0x0d, SHIFT: 0x10, CONTROL: 0x11, ESCAPE: 0x1b, END: 0x23, HOME: 0x24, LEFT: 0x25, RIGHT: 0x27 };

/** Decode an 8-bit RGB/RGBA PNG (all filter types) to {w, h, rgb(x, y) -> 0xRRGGBB}. */
export function decodePng(png) {
  let o = 8, w = 0, h = 0, colorType = 0;
  const idat = [];
  while (o < png.length) {
    const len = png.readUInt32BE(o);
    const type = png.subarray(o + 4, o + 8).toString('latin1');
    const data = png.subarray(o + 8, o + 8 + len);
    if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); colorType = data[9]; }
    if (type === 'IDAT') idat.push(data);
    o += 12 + len;
  }
  const bpp = colorType === 6 ? 4 : 3;
  const raw = inflateSync(Buffer.concat(idat));
  const stride = w * bpp;
  const out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const v = raw[y * (stride + 1) + 1 + x];
      const a = x >= bpp ? out[y * stride + x - bpp] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = x >= bpp && y > 0 ? out[(y - 1) * stride + x - bpp] : 0;
      let p = 0;
      if (f === 1) p = a; else if (f === 2) p = b; else if (f === 3) p = (a + b) >> 1;
      else if (f === 4) { const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c); p = pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      out[y * stride + x] = (v + p) & 0xff;
    }
  }
  return { w, h, rgb: (x, y) => { const i = y * stride + x * bpp; return (out[i] << 16) | (out[i + 1] << 8) | out[i + 2]; } };
}

/** Rows (menu-local y) whose middle pixel is a Windows highlight blue: the highlighted menu item. */
export function highlightedRows(popup) {
  const img = decodePng(popup.png);
  const rows = [];
  for (let y = 0; y < img.h; y++) {
    const p = img.rgb(Math.round(img.w / 2), y);
    const r = p >> 16, g = (p >> 8) & 0xff, b = p & 0xff;
    if (b > 150 && r < 80 && g > 60 && g < 200) rows.push(y);
  }
  return rows;
}

/** Wait until the server's window list satisfies pred; returns the list. */
export async function waitWindows(c, pred, ms = 5000) {
  const end = Date.now() + ms;
  while (!pred(c.windows)) {
    if (Date.now() > end) throw new Error(`window list condition not met within ${ms} ms: ${JSON.stringify(c.windows)}`);
    await sleep(50);
  }
  return c.windows;
}
