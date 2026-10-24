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
// <mods> is a combination of S (shift), C (ctrl), A (alt), or "-" for none.
// Values: booleans TRUE/FALSE, numerics with %g, strings as typed (newlines as \n),
// rings and enums by item text, tab controls by page label.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export const URL_BASE = process.env.RVI_URL ?? 'http://127.0.0.1:8089';
export const LOG_PATH = process.env.RVI_FIXTURE_LOG ?? path.join(os.tmpdir(), 'RemoteVI Fixture.log');
export const enabled = process.env.RVI_LV === '1';

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function readLog() {
  if (!fs.existsSync(LOG_PATH)) return [];
  return fs.readFileSync(LOG_PATH, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => line.split('\t'));
}

/** Control body rectangles from the fixture's layout lines. */
export function layout() {
  const map = new Map();
  for (const [kind, label, rect] of readLog()) {
    if (kind === 'layout') {
      const [x, y, w, h] = rect.split(' ').map(Number);
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

/** A protocol-v2 client like web/index.html: acks frames, keeps the latest overlay. */
export async function connect() {
  const ws = new WebSocket(`${URL_BASE.replace(/^http/, 'ws')}/ws`);
  ws.binaryType = 'arraybuffer';
  const c = { ws, overlay: [], overlays: 0, frames: 0, width: 0, height: 0 };
  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') return;
    const v = new DataView(ev.data);
    if (v.getUint8(1) === 2) {
      const popups = [];
      let o = 4;
      for (let i = 0, n = v.getUint16(2); i < n; i++) {
        const len = v.getUint32(o + 4);
        const png = Buffer.from(ev.data, o + 8, len);
        popups.push({ x: v.getInt16(o), y: v.getInt16(o + 2), w: png.readUInt32BE(16), h: png.readUInt32BE(20) });
        o += 8 + len;
      }
      c.overlay = popups;
      c.overlays++;
    } else {
      c.frames++;
      c.width = v.getUint16(6);
      c.height = v.getUint16(8);
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
  c.ws.send(`m 512 ${x} ${y} ${wParam}`);
}

export async function click(c, x, y, { button = 'left', shift = false, ctrl = false, settle = 250 } = {}) {
  const mods = (shift ? MK.SHIFT : 0) | (ctrl ? MK.CTRL : 0);
  const [down, up, flag] = button === 'right' ? [516, 517, MK.R] : [513, 514, MK.L];
  move(c, x, y, mods);
  c.ws.send(`m ${down} ${x} ${y} ${flag | mods}`);
  c.ws.send(`m ${up} ${x} ${y} ${mods}`);
  await sleep(settle);
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
