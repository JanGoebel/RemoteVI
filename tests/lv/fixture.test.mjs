// LabVIEW integration tests: the remote panel must behave as if operated on the host.
//
//   1. run tests/fixtures/RemoteVI Fixture.vi in LabVIEW (it serves on port 8089)
//   2. RVI_LV=1 node --test tests/lv/
//
// Skipped unless RVI_LV=1, so `npm test` stays LabVIEW-free.

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';

import {
  enabled, connect, layout, readLog, waitLog, click, move, keyDown, keyUp, typeText, waitOverlay, sleep, VK, highlightedRows, waitWindows,
} from './harness.mjs';

const opts = { skip: !enabled && 'set RVI_LV=1 and run tests/fixtures/RemoteVI Fixture.vi' };
let c;
let L;

before(async () => {
  if (!enabled) return;
  await waitLog(([k]) => k === 'ready', { ms: 10000 });
  c = await connect();
  L = layout(c);
});
after(() => c?.ws.close());

const mark = () => readLog().length;
const at = (label) => {
  const r = L.get(label);
  assert.ok(r, `fixture has no layout line for ${label}`);
  return r;
};

test('fixture reports the layout of every control', opts, () => {
  for (const label of ['Switch', 'Button', 'Number', 'Text', 'Mode', 'Tab', 'Graph', 'List', 'Ask', 'Open', 'Stop']) at(label);
});

test('click toggles a switch: Mouse Down/Up and Value Change fire like a local click', opts, async () => {
  const s = mark();
  const r = at('Switch');
  await click(c, r.cx, r.cy);
  const down = await waitLog(([k, l]) => k === 'mousedown' && l === 'Switch', { since: s });
  assert.equal(down[2].split(' ')[3], '-', 'no modifiers');
  await waitLog(([k, l]) => k === 'mouseup' && l === 'Switch', { since: s });
  await waitLog(([k, l]) => k === 'value' && l === 'Switch', { since: s });
});

test('a latched button fires Value Change once per click', opts, async () => {
  const s = mark();
  const r = at('Button');
  await click(c, r.cx, r.cy, { settle: 400 });
  await waitLog(([k, l, v]) => k === 'value' && l === 'Button' && v === 'TRUE', { since: s });
  const values = readLog().slice(s).filter(([k, l]) => k === 'value' && l === 'Button');
  assert.equal(values.length, 1);
});

test('typing into a numeric and pressing Enter commits the value', opts, async () => {
  const s = mark();
  const r = at('Number');
  await click(c, r.x + 10, r.cy);
  keyDown(c, VK.END, true); keyUp(c, VK.END, true);
  for (let i = 0; i < 12; i++) { keyDown(c, VK.BACK); keyUp(c, VK.BACK); }
  await typeText(c, '42');
  keyDown(c, VK.ENTER); keyUp(c, VK.ENTER);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Number' && v === '42', { since: s });
});

test('typing into a string fires Key Down per character and commits on click elsewhere', opts, async () => {
  const s = mark();
  const r = at('Text');
  await click(c, r.cx, r.cy);
  await typeText(c, 'hi');
  await waitLog(([k, l, key]) => k === 'keydown' && l === 'Text' && key.startsWith('h'), { since: s });
  await waitLog(([k, l, key]) => k === 'keydown' && l === 'Text' && key.startsWith('i'), { since: s });
  const sw = at('Stop');
  await click(c, sw.x + sw.w + 40, sw.cy); // empty panel area next to Stop
  await waitLog(([k, l, v]) => k === 'value' && l === 'Text' && v.endsWith('hi'), { since: s });
});

test('Shift held in the browser reaches LabVIEW as a modifier', opts, async () => {
  const s = mark();
  const r = at('Switch');
  keyDown(c, VK.SHIFT);
  await click(c, r.cx, r.cy, { shift: true });
  keyUp(c, VK.SHIFT);
  const down = await waitLog(([k, l]) => k === 'mousedown' && l === 'Switch', { since: s });
  assert.match(down[2].split(' ')[3], /S/);
});

test('Ctrl held in the browser reaches LabVIEW as a modifier on keys', opts, async () => {
  const s = mark();
  const r = at('Text');
  await click(c, r.cx, r.cy);
  keyDown(c, VK.CONTROL);
  c.ws.send('k 258 1 1'); // Ctrl+A arrives as WM_CHAR 1, like Windows sends it
  keyUp(c, VK.CONTROL);
  const kd = await waitLog(([k, l, key, mods]) => k === 'keydown' && l === 'Text' && /C/.test(mods ?? ''), { since: s });
  assert.ok(kd);
});

test('moving the pointer over a control fires Mouse Enter and Mouse Leave', opts, async () => {
  const s = mark();
  const r = at('Button');
  move(c, r.x - 30, r.cy); await sleep(150);
  move(c, r.cx, r.cy); await sleep(150);
  await waitLog(([k, l]) => k === 'enter' && l === 'Button', { since: s });
  move(c, r.x - 30, r.cy); await sleep(150);
  await waitLog(([k, l]) => k === 'leave' && l === 'Button', { since: s });
});

/** Latest logged value of a control, or `initial` if it never changed. */
const current = (label, initial) => readLog().filter(([k, l]) => k === 'value' && l === label).at(-1)?.[2] ?? initial;

test('a ring opens its menu in the browser and an item can be chosen', opts, async () => {
  const items = ['Off', 'Slow', 'Fast'];
  // Choose an item other than the current one, so Value Change must fire on every run.
  const target = (items.indexOf(current('Mode', 'Off')) + 1) % items.length;
  const s = mark();
  const r = at('Mode');
  await click(c, r.cx, r.cy, { settle: 100 });
  const [menu] = await waitOverlay(c);
  assert.ok(menu.w > 20 && menu.h > 20, 'menu image has a size');
  // The three items are stacked evenly from top to bottom.
  await click(c, menu.x + 20, menu.y + Math.round(menu.h * (2 * target + 1) / 6), { settle: 100 });
  await waitOverlay(c, (o) => o.length === 0);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Mode' && v === items[target], { since: s });
});

test('a right-click menu can be dismissed by clicking outside it', opts, async () => {
  const r = at('Graph');
  await click(c, r.cx, r.cy, { button: 'right', settle: 100 });
  await waitOverlay(c);
  await click(c, 5, 5, { settle: 100 });
  await waitOverlay(c, (o) => o.length === 0);
});

test('clicking a tab switches the page', opts, async () => {
  // The fixture's tabs are a fixed 80 px wide: One at x+0..80, Two at x+80..160.
  const target = current('Tab', 'One') === 'One' ? 'Two' : 'One';
  const s = mark();
  const r = at('Tab');
  await click(c, r.x + (target === 'One' ? 40 : 120), r.y + 10);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Tab' && v === target, { since: s });
});

// --- round 2: wheel, double click, arrows with modifiers, tip strips, submenus -------------

test('the mouse wheel over a control fires Mouse Wheel with the right direction', opts, async () => {
  const s = mark();
  const r = at('Number');
  move(c, r.cx, r.cy);
  c.ws.send(`m 522 ${r.cx} ${r.cy} ${(120 * 0x10000) >>> 0}`); // one notch away from the user
  const ev = await waitLog(([k, l]) => k === 'wheel' && l === 'Number', { since: s });
  assert.ok(Number(ev[2]) > 0, `positive wheel delta, got ${ev[2]}`);
});

test('a double click reaches LabVIEW as a double click', opts, async () => {
  const s = mark();
  const r = at('List');
  const y = r.y + 8; // first row
  move(c, r.x + 20, y);
  c.ws.send(`m 513 ${r.x + 20} ${y} 1`);
  c.ws.send(`m 514 ${r.x + 20} ${y} 0`);
  await sleep(60);
  c.ws.send(`m 515 ${r.x + 20} ${y} 1`); // WM_LBUTTONDBLCLK, as the browser sends the 2nd press
  c.ws.send(`m 514 ${r.x + 20} ${y} 0`);
  await waitLog(([k, l]) => k === 'dblclick' && l === 'List', { since: s });
});

test('Shift+Right arrow arrives with the Shift modifier', opts, async () => {
  const s = mark();
  const r = at('Text');
  await click(c, r.cx, r.cy);
  keyDown(c, VK.SHIFT);
  keyDown(c, VK.RIGHT, true); keyUp(c, VK.RIGHT, true);
  keyUp(c, VK.SHIFT);
  await waitLog(([k, l, key, mods]) => k === 'keydown' && l === 'Text' && /right/i.test(key) && /S/.test(mods ?? ''), { since: s });
});

test('the tip strips of the controls reach the browser as text, also with LabVIEW in the background', opts, async () => {
  // LabVIEW shows its own tip strips only while it is the foreground application; the
  // server sends the texts (tips message) and the client shows them itself.
  const r = at('Button');
  const end = Date.now() + 2000;
  while (!c.tips && Date.now() < end) await sleep(50);
  assert.ok(Array.isArray(c.tips), 'a tips message arrives on connect');
  const hit = c.tips.find((t) => r.cx >= t.x && r.cx < t.x + t.w && r.cy >= t.y && r.cy < t.y + t.h);
  assert.equal(hit?.text, 'Press me');
  assert.ok(c.tips.every((t) => t.text !== ''), 'controls without a tip strip are left out');
  // A hover no longer brings a LabVIEW tip strip into the OVERLAY.
  move(c, r.x - 30, r.cy); await sleep(300);
  move(c, r.cx, r.cy); await sleep(1200);
  assert.equal(c.overlay.length, 0);
  move(c, r.x - 30, r.cy);
});

test('an item in a submenu of a run-time shortcut menu can be chosen', opts, async () => {
  const s = mark();
  const r = at('Text');
  await click(c, r.cx, r.cy, { button: 'right', settle: 100 });
  const [menu] = await waitOverlay(c);
  // The fixture's menu is: "Top" (first row), "More" (second row, opens a submenu with "Deep").
  const rowH = Math.round(menu.h / 2);
  await click(c, menu.x + 20, menu.y + Math.round(rowH * 1.5), { settle: 100 });
  const popups = await waitOverlay(c, (o) => o.length >= 2, 3000);
  const sub = popups.at(-1);
  await click(c, sub.x + 20, sub.y + Math.round(sub.h / 2), { settle: 100 });
  await waitOverlay(c, (o) => o.length === 0);
  await waitLog(([k, l, tag]) => k === 'menu' && l === 'Text' && tag === 'Deep', { since: s });
});

// --- round 3: menus behave like local menus ------------------------------------------------

test('hovering over a menu item highlights that item, like locally', opts, async () => {
  const r = at('Mode');
  await click(c, r.cx, r.cy, { settle: 100 });
  const [menu] = await waitOverlay(c);
  for (const target of [2, 0]) {
    const y = menu.y + Math.round(menu.h * (2 * target + 1) / 6);
    move(c, menu.x + 20, y);
    const end = Date.now() + 2000;
    let rows = [];
    while (Date.now() < end) {
      rows = c.overlay[0] ? highlightedRows(c.overlay[0]) : [];
      // The highlight is one band across the item; the item's text crosses the middle column,
      // so test the band's extent, not the single pixel at the pointer's row.
      if (rows.length && rows[0] <= y - menu.y && y - menu.y <= rows.at(-1)) break;
      await sleep(50);
    }
    assert.ok(rows.length && rows[0] <= y - menu.y && y - menu.y <= rows.at(-1), `row under the pointer (y=${y - menu.y}) is highlighted; highlighted rows: ${rows[0]}..${rows.at(-1)}`);
  }
  await click(c, 5, 5, { settle: 100 }); // close without choosing
  await waitOverlay(c, (o) => o.length === 0);
});

test('a submenu opens beside its parent, not on top of it', opts, async () => {
  const r = at('Text');
  await click(c, r.cx, r.cy, { button: 'right', settle: 100 });
  const [menu] = await waitOverlay(c);
  const rowH = Math.round(menu.h / 2);
  await click(c, menu.x + 20, menu.y + Math.round(rowH * 1.5), { settle: 100 });
  const popups = await waitOverlay(c, (o) => o.length >= 2, 3000);
  const [parent, sub] = [popups[0], popups.at(-1)];
  const overlapX = Math.min(parent.x + parent.w, sub.x + sub.w) - Math.max(parent.x, sub.x);
  assert.ok(overlapX <= 6, `submenu x ${sub.x}..${sub.x + sub.w} must not cover parent x ${parent.x}..${parent.x + parent.w}`);
  await click(c, 5, 5, { settle: 100 });
  await waitOverlay(c, (o) => o.length === 0);
});

// --- round 4: the whole window - menu bar, toolbar, scrollbars ----------------------------

test('the stream shows the whole window: menu bar and toolbar above the panel', opts, async () => {
  assert.ok(c.originSeen, 'server sends `origin x y`');
  assert.ok(c.origin.y >= 20, `panel starts below menu bar and toolbar (origin y = ${c.origin.y})`);
  const stop = at('Stop');
  assert.ok(c.height > stop.y + stop.h && c.width > 0, 'frame covers the panel');
});

test('an item of the run-time menu bar can be chosen, also from a submenu', opts, async () => {
  for (const [path, tag] of [[['Say Hello'], 'Hello'], [['More', 'Deep Bar'], 'DeepBar']]) {
    const s = mark();
    await click(c, 15, 8, { settle: 100 }); // first menu bar item, "Fixture"
    let popups = await waitOverlay(c);
    for (const [i, item] of path.entries()) {
      const menu = popups.at(-1);
      // "Fixture" menu: row 0 "Say Hello", row 1 "More"; "More" submenu: row 0 "Deep Bar".
      const row = item === 'More' ? 1 : 0;
      const rows = item === 'More' || item === 'Say Hello' ? 2 : 1;
      await click(c, menu.x + 20, menu.y + Math.round(menu.h * (2 * row + 1) / (2 * rows)), { settle: 100 });
      if (i < path.length - 1) popups = await waitOverlay(c, (o) => o.length > popups.length, 3000);
    }
    await waitOverlay(c, (o) => o.length === 0);
    await waitLog(([k, t]) => k === 'menubar' && t === tag, { since: s });
  }
});

test('the panel scrollbar is visible in the stream and can be operated', opts, async () => {
  const s = mark();
  // Vertical scrollbar along the right edge of the frame; its down arrow sits just above the
  // horizontal scrollbar at the bottom.
  for (let i = 0; i < 3; i++) await click(c, c.width - 8, c.height - 26, { settle: 150 });
  await waitLog(([k]) => k === 'scroll', { since: s });
});

// --- round 5: dialogs and other windows ---------------------------------------------------

test('a LabVIEW dialog appears as a modal window with its own picture; Enter answers it', opts, async () => {
  const s = mark();
  const r = at('Ask');
  await click(c, r.cx, r.cy, { settle: 100 });
  const [dlg] = await waitWindows(c, (w) => w.some((x) => x.modal));
  assert.ok(dlg.w > 50 && dlg.h > 30, `dialog has a size: ${dlg.w}x${dlg.h}`);
  assert.ok(dlg.title.length > 0, 'dialog has a title');
  const end = Date.now() + 3000;
  while (!(c.windowFrames.get(dlg.id) > 0) && Date.now() < end) await sleep(50);
  assert.ok(c.windowFrames.get(dlg.id) > 0, 'a WINDOW FRAME of the dialog arrived');
  keyDown(c, VK.ENTER); keyUp(c, VK.ENTER); // default button
  await waitWindows(c, (w) => w.length === 0);
  await waitLog(([k, v]) => k === 'dialog' && v === 'TRUE', { since: s });
});

test('the panel behind a modal dialog takes no input, like on the host', opts, async () => {
  const s = mark();
  await click(c, at('Ask').cx, at('Ask').cy, { settle: 100 });
  const [dlg] = await waitWindows(c, (w) => w.some((x) => x.modal));
  const sw = at('Switch');
  await click(c, sw.cx, sw.cy, { settle: 300 });
  assert.equal(readLog().slice(s).filter(([k, l]) => k === 'value' && l === 'Switch').length, 0, 'Switch must not change');
  // The dialog's right-hand button is "No": click it with the mouse, in the dialog's own area.
  await click(c, dlg.x + Math.round(dlg.w * 0.72), dlg.y + dlg.h - 22, { settle: 100 });
  await waitWindows(c, (w) => w.length === 0);
  await waitLog(([k, v]) => k === 'dialog' && v === 'FALSE', { since: s });
});

test('the native file dialog appears as a window and Escape cancels it', opts, async () => {
  const s = mark();
  const r = at('Open');
  await click(c, r.cx, r.cy, { settle: 100 });
  await waitWindows(c, (w) => w.length > 0, 8000);
  keyDown(c, VK.ESCAPE); keyUp(c, VK.ESCAPE);
  await waitWindows(c, (w) => w.length === 0, 8000);
  await waitLog(([k, v]) => k === 'file' && v === 'CANCELLED', { since: s });
});
