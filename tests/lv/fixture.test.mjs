// LabVIEW integration tests: the remote panel must behave as if operated on the host.
//
//   1. run tests/fixtures/RemoteVI Fixture.vi in LabVIEW (it serves on port 8089)
//   2. RVI_LV=1 node --test tests/lv/
//
// Skipped unless RVI_LV=1, so `npm test` stays LabVIEW-free.

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';

import {
  enabled, connect, layout, readLog, waitLog, click, move, keyDown, keyUp, typeText, waitOverlay, sleep, VK,
} from './harness.mjs';

const opts = { skip: !enabled && 'set RVI_LV=1 and run tests/fixtures/RemoteVI Fixture.vi' };
let c;
let L;

before(async () => {
  if (!enabled) return;
  await waitLog(([k]) => k === 'ready', { ms: 10000 });
  c = await connect();
  L = layout();
});
after(() => c?.ws.close());

const mark = () => readLog().length;
const at = (label) => {
  const r = L.get(label);
  assert.ok(r, `fixture has no layout line for ${label}`);
  return r;
};

test('fixture reports the layout of every control', opts, () => {
  for (const label of ['Switch', 'Button', 'Number', 'Text', 'Mode', 'Tab', 'Graph', 'Stop']) at(label);
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
