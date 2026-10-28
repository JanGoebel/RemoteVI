// LabVIEW integration tests on a complex application UI: tests/fixtures/RemoteVI Complex Fixture.vi
// (splitter panes, tab pages, a cluster, a subpanel showing one of two running VIs, a separate inspector
// window, tree, table, array of clusters, slide, knob, a graph with cursors, a path with browse button).
//
//   1. run tests/fixtures/RemoteVI Complex Fixture.vi (port 8089, one RemoteVI server per LabVIEW instance)
//   2. RVI_LV_COMPLEX=1 node --test tests/lv/complex.test.mjs
//
// The fixture logs to RemoteVI Complex Fixture.log in the temp directory (format of harness.mjs, plus:
// `pane <index> x y w h` for the visible part of each pane, `vlayout` for the controls of the VI in the
// subpanel, `ilayout` for the inspector window's controls relative to its panel area and `iorigin x y`
// for where that area starts in the inspector window's client area). Its layout and
// pane lines are written again whenever they change, so the latest line of a label wins.

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';

import {
  connect, layout, readLog, waitLog, click, move, drag, keyDown, keyUp, typeText, waitOverlay, sleep, VK, waitWindows,
  splitters, pixel, useLog,
} from './harness.mjs';

const enabled = process.env.RVI_LV_COMPLEX === '1';
const opts = { skip: !enabled && 'set RVI_LV_COMPLEX=1 and run tests/fixtures/RemoteVI Complex Fixture.vi' };
useLog(process.env.RVI_COMPLEX_LOG ?? path.join(os.tmpdir(), 'RemoteVI Complex Fixture.log'));
let c;

before(async () => {
  if (!enabled) return;
  await waitLog(([k]) => k === 'ready', { ms: 15000 });
  c = await connect({ fb: true });
  await sleep(500);
});
after(() => c?.ws.close());

const mark = () => readLog().length;
const L = () => layout(c);
const at = (label, kinds = ['layout']) => {
  const r = layout(c, kinds).get(label);
  assert.ok(r, `fixture has no ${kinds.join('/')} line for ${label}`);
  return r;
};
const panes = () => layout(c, ['pane']);
/** Latest logged value of a control, or `initial`. */
const current = (label, initial) => readLog().filter(([k, l]) => k === 'value' && l === label).at(-1)?.[2] ?? initial;
const TAB_W = 110, TAB_H = 23;

/** Select page i of the tab control Settings (Acquisition 0, Display 1, Viewer 2) and wait for its layout. */
async function page(i) {
  if (current('Settings', '0') !== String(i)) {
    const s = mark();
    const r = at('Settings');
    await click(c, r.x + TAB_W / 2 + TAB_W * i, r.y + TAB_H / 2);
    await waitLog(([k, l, v]) => k === 'value' && l === 'Settings' && v === String(i), { since: s });
  }
  await sleep(700); // the fixture writes the layout of the new page within 500 ms
}

test('the fixture reports panes, nested controls and the subpanel', opts, () => {
  for (const label of ['Nav', 'Results', 'Steps', 'Inspector', 'Stop', 'View', 'Status', 'Settings']) at(label);
  for (const i of ['0', '1', '2']) assert.ok(panes().get(i), `pane ${i}`);
});

test('the splitter bars are on the frame where the panes meet', opts, () => {
  const st = at('Settings');
  const sp = splitters(c, { y: st.y + 200, x: st.x + 300 });
  assert.ok(sp.vertical.some((x) => x < st.x), `vertical bars ${sp.vertical}`);
  assert.ok(sp.horizontal.some((y) => y < st.y), `horizontal bars ${sp.horizontal}`);
});

test('the tab control scales with its pane (Scale Single Object)', opts, () => {
  const s = at('Settings');
  assert.ok(s.x + s.w >= c.width - 20, `Settings ends at ${s.x + s.w} in a ${c.width} px frame`);
});

test('tab pages switch like a local click', opts, async () => {
  await page(1);
  await page(2);
  await page(0);
  assert.equal(current('Settings'), '0');
});

test('typing into a cluster element on a tab page changes the cluster', opts, async () => {
  await page(0);
  const s = mark();
  const r = at('Name');
  await click(c, r.cx, r.cy);
  keyDown(c, VK.END, true); keyUp(c, VK.END, true);
  for (let i = 0; i < 8; i++) { keyDown(c, VK.BACK); keyUp(c, VK.BACK); }
  await typeText(c, 'abc');
  keyDown(c, VK.TAB); keyUp(c, VK.TAB);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Channel' && v.startsWith('abc|'), { since: s });
});

test('a numeric and a boolean inside the cluster', opts, async () => {
  await page(0);
  let s = mark();
  const g = at('Gain');
  await click(c, g.x + g.w - 12, g.cy);
  keyDown(c, VK.END, true); keyUp(c, VK.END, true);
  for (let i = 0; i < 8; i++) { keyDown(c, VK.BACK); keyUp(c, VK.BACK); }
  await typeText(c, '5');
  keyDown(c, VK.ENTER); keyUp(c, VK.ENTER);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Channel' && /^[^|]*\|5(\.0*)?\|/.test(v), { since: s });
  const before = current('Channel', '|0|0').split('|')[2];
  s = mark();
  const e = at('Enabled');
  await click(c, e.cx, e.cy);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Channel' && v.split('|')[2] !== before, { since: s });
});

test('a table cell is edited by double click and typing', opts, async () => {
  const s = mark();
  const r = at('Results');
  const x = r.x + 22, y = r.y + 30; // first column, first data row below the header
  await click(c, x, y, { settle: 60 });
  c.ws.send(`m 515 ${x} ${y} 1`);
  c.ws.send(`m 514 ${x} ${y} 0`);
  await sleep(300);
  const text = `Q${Date.now() % 1000}`; // new each run, so the value changes
  await typeText(c, text);
  keyDown(c, VK.ENTER); keyUp(c, VK.ENTER);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Results' && v.includes(text), { since: s });
});

test('a tree item is selected by a click', opts, async () => {
  const s = mark();
  const r = at('Nav');
  const rows = [r.y + 36, r.y + 20]; // second item, then the first (a click on the selected one changes nothing)
  const before = current('Nav', '');
  for (const y of rows) {
    await click(c, r.x + 90, y, { settle: 400 });
    if (current('Nav', '') !== before) break;
  }
  await waitLog(([k, l]) => k === 'value' && l === 'Nav', { since: s });
});

test('the slide follows a drag of its thumb', opts, async () => {
  await page(0);
  const s = mark();
  const r = at('Rate');
  let tx = -1, ty = -1;
  for (let y = r.y; y < r.y + 40; y++) {
    for (let x = r.x; x < r.x + r.w; x++) {
      // the fill is a long blue run (anti-aliased scale text has single blue pixels)
      let run = true;
      for (let k = 0; k < 10 && run; k++) {
        const p = pixel(c, x - k, y), red = p >> 16, green = (p >> 8) & 255, blue = p & 255;
        run = blue > 160 && red < 90 && green < 140;
      }
      if (run && x > tx) { tx = x; ty = y; }
    }
  }
  assert.ok(tx > 0, 'the blue fill of the slide');
  while (ty > r.y) { const p = pixel(c, tx, ty - 1); if ((p & 255) > 160 && (p >> 16) < 90) ty--; else break; }
  const gy = ty - 6; // the triangular thumb sits on top of the fill's right end
  const to = tx - r.x > r.w / 2 ? tx - 50 : tx + 50;
  await drag(c, tx, gy, to, gy);
  const values = readLog().slice(s).filter(([k, l]) => k === 'value' && l === 'Rate');
  assert.ok(values.length >= 2, `Rate changed ${values.length} times during the drag`);
});

test('the knob follows a drag', opts, async () => {
  await page(0);
  const s = mark();
  const r = at('Level');
  const before = current('Level', '');
  const dx = Number(before || 0) > 50000 ? -30 : 30; // turn away from the end the knob is nearer to
  await drag(c, r.cx, r.cy - 20, r.cx + dx, r.cy + 25);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Level' && v !== before, { since: s });
});

/** Columns of the frame inside r with at least `min` yellow pixels: the line of Cursor 0 (plots and the
 *  cursor's own marker cross it, so the pixels are counted, not one run). */
function cursorColumns(r, min = 80) {
  const cols = [];
  for (let x = r.x; x < r.x + r.w; x++) {
    let n = 0;
    for (let y = r.y; y < r.y + r.h; y++) {
      const p = pixel(c, x, y), red = p >> 16, green = (p >> 8) & 255, blue = p & 255;
      if (red > 200 && green > 200 && blue < 90) n++;
    }
    if (n >= min) cols.push(x);
  }
  return cols;
}

test('a graph cursor follows a drag', opts, async () => {
  await page(1);
  const r = at('Scope');
  const cols = cursorColumns(r);
  assert.ok(cols.length, 'a cursor line on the graph');
  const x0 = cols[0], y = Math.round(r.y + r.h * 0.6);
  const s = mark();
  await drag(c, x0, y, x0 + 120, y, { settle: 800 });
  await waitLog(([k, l]) => k === 'mouseup' && l === 'Scope', { since: s });
  const moved = cursorColumns(r);
  try {
    assert.ok(moved.some((x) => Math.abs(x - (x0 + 120)) < 12), `cursor lines at ${moved.join(',')} after dragging from ${x0}`);
  } finally {
    const back = moved.find((x) => Math.abs(x - (x0 + 120)) < 12);
    if (back) await drag(c, back, y, x0, y, { settle: 600 });
  }
});

test('the browse button of a path control opens the native file dialog; Escape cancels it', opts, async () => {
  await page(0);
  const r = at('Data File');
  await click(c, r.x + r.w - 10, r.cy, { settle: 100 });
  const [dlg] = await waitWindows(c, (w) => w.length > 0, 8000);
  assert.equal(dlg.modal, true);
  await sleep(800);
  keyDown(c, VK.ESCAPE); keyUp(c, VK.ESCAPE);
  await waitWindows(c, (w) => w.length === 0, 5000);
});

test('the VI in the subpanel takes clicks and typing', opts, async () => {
  await page(2);
  if (current('View', 'View A') !== 'View A') await selectView(0);
  let s = mark();
  const a = at('A Apply', ['vlayout']);
  await click(c, a.cx, a.cy);
  await waitLog(([k, l, v]) => k === 'value' && l === 'A Apply' && v === 'TRUE', { since: s });
  s = mark();
  const t = at('A Text', ['vlayout']);
  await click(c, t.cx, t.cy);
  await typeText(c, 'hi');
  keyDown(c, VK.TAB); keyUp(c, VK.TAB);
  await waitLog(([k, l, key]) => k === 'keydown' && l === 'A Text' && key.startsWith('h'), { since: s });
  await waitLog(([k, l, v]) => k === 'value' && l === 'A Text' && v.endsWith('hi'), { since: s });
});

/** Choose item i of the ring View through its popup menu (keys, as the server drives menus). */
async function selectView(i) {
  const s = mark();
  const r = at('View');
  await click(c, r.cx, r.cy, { settle: 100 });
  const [menu] = await waitOverlay(c);
  const rowH = (menu.h - 4) / 2;
  const y = Math.round(menu.y + 2 + rowH * i + rowH / 2);
  move(c, menu.x + 20, y);
  await sleep(300);
  await click(c, menu.x + 20, y, { settle: 300 });
  await waitLog(([k, l, v]) => k === 'value' && l === 'View' && v === ['View A', 'View B'][i], { since: s });
  await sleep(800); // the vlayout lines of the VI now shown
}

test('the subpanel swaps its VI and the new one is operable', opts, async () => {
  await page(2);
  await selectView(1);
  const s = mark();
  const b = at('B Run', ['vlayout']);
  await click(c, b.cx, b.cy);
  await waitLog(([k, l, v]) => k === 'value' && l === 'B Run' && v === 'TRUE', { since: s });
  await selectView(0);
});

test('tip strips of nested controls and of the subpanel VI reach the browser', opts, async () => {
  await page(0);
  await sleep(700);
  const texts = () => (c.tips ?? []).map((t) => t.text);
  assert.ok(texts().includes('Channel gain'), `tips ${JSON.stringify(texts())}`); // an element of a cluster on a tab page
  assert.ok(texts().includes('Sample rate'), `tips ${JSON.stringify(texts())}`); // a slide on a tab page
  const gain = c.tips.find((t) => t.text === 'Channel gain'), g = at('Gain');
  assert.ok(Math.abs(gain.x - g.x) <= 2 && gain.y <= g.y && gain.y + gain.h >= g.y + g.h, 'the tip covers the element');
  await page(2);
  await sleep(700);
  assert.ok(texts().includes('Apply view A'), `tips ${JSON.stringify(texts())}`); // a control of the subpanel VI
  assert.ok(!texts().includes('Sample rate'), 'controls of a hidden page have no tip');
});

test('the left pane scrolls with the mouse wheel', opts, async () => {
  const st = at('Steps');
  const wx = st.x + st.w + 40, wy = st.cy; // empty pane area right of Steps (over Steps the array would take the wheel)
  const wheel = async (delta) => {
    move(c, wx, wy);
    await sleep(200);
    for (let i = 0; i < 3; i++) c.ws.send(`m 522 ${wx} ${wy} ${((delta & 0xffff) * 0x10000) >>> 0}`);
    await sleep(1200);
    return at('Steps').y;
  };
  // towards the user (down); a pane already scrolled to its end moves the other way
  let delta = -120, y1 = await wheel(delta);
  if (y1 === st.y) { delta = 120; y1 = await wheel(delta); }
  try {
    assert.notEqual(y1, st.y, 'Steps moved when the pane scrolled');
  } finally {
    if (y1 !== st.y) await wheel(-delta);
  }
});

test('the inspector, a separate non-modal window, is listed and operable', opts, async () => {
  await page(0);
  let s = mark();
  const r = at('Inspector');
  await click(c, r.cx, r.cy);
  await waitLog(([k, l]) => k === 'value' && l === 'Inspector', { since: s });
  const [w] = await waitWindows(c, (list) => list.some((x) => x.title === 'RemoteVI Complex Inspector.vi'), 5000);
  assert.equal(w.modal, false);
  await waitLog(([k]) => k === 'iorigin', { since: s });
  await sleep(400);
  const I = (label) => at(label, ['ilayout']);
  const win = c.windows.find((x) => x.title === 'RemoteVI Complex Inspector.vi');
  // ilayout is relative to the inspector's panel area, iorigin is where that starts in its window's client area
  const io = readLog().filter(([k]) => k === 'iorigin').at(-1)[1].split(' ').map(Number);
  const inWin = (p) => ({ x: win.x + io[0] + p.cx - c.origin.x, y: win.y + io[1] + p.cy - c.origin.y });
  s = mark();
  let p = inWin(I('Apply'));
  await click(c, p.x, p.y);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Apply' && v === 'TRUE', { since: s });
  p = inWin(I('Note'));
  await click(c, p.x, p.y);
  await typeText(c, 'ok');
  keyDown(c, VK.TAB); keyUp(c, VK.TAB);
  await waitLog(([k, l, v]) => k === 'value' && l === 'Note' && v.endsWith('ok'), { since: s });
  p = inWin(I('Close'));
  await click(c, p.x, p.y);
  await waitWindows(c, (list) => !list.some((x) => x.title === 'RemoteVI Complex Inspector.vi'), 5000);
});

after(async () => {
  // never leave the inspector over the panel: it would take the clicks of a later run
  for (const w of c?.windows ?? []) if (w.title === 'RemoteVI Complex Inspector.vi') c.ws.send(`x ${w.id}`);
  await sleep(500);
});

// Last: a press on a splitter bar can leave LabVIEW in its own tracking loop, which takes the next presses.
const LIMIT = 'LabVIEW does not move a splitter bar for posted mouse messages (README, Known limits)';

test('the vertical splitter bar can be dragged', { ...opts, todo: LIMIT }, async () => {
  const st = at('Settings');
  const y = st.y + 200;
  const bar = splitters(c, { y, x: st.x + 100 }).vertical.filter((x) => x < st.x).at(-1);
  assert.ok(bar, 'vertical splitter bar left of the main pane');
  await drag(c, bar - 4, y, bar + 56, y, { settle: 1200 });
  const moved = at('Settings').x - st.x;
  try {
    assert.ok(Math.abs(moved - 60) < 15, `main pane content moved by ${moved}, expected 60`);
  } finally {
    if (moved) await drag(c, bar + 56, y, bar - 4, y, { settle: 1200 });
  }
});

test('the horizontal splitter bar can be dragged', { ...opts, todo: LIMIT }, async () => {
  const st = at('Settings');
  const x = st.x + 300;
  const bar = splitters(c, { y: st.y + 100, x }).horizontal.filter((y) => y < st.y).at(-1);
  assert.ok(bar, 'horizontal splitter bar above the main pane');
  await drag(c, x, bar - 4, x, bar + 36, { settle: 1200 });
  const moved = at('Settings').y - st.y;
  try {
    assert.ok(Math.abs(moved - 40) < 12, `main pane content moved by ${moved}, expected 40`);
  } finally {
    if (moved) await drag(c, x, bar + 36, x, bar - 4, { settle: 1200 });
  }
});

test('a .NET or ActiveX container (child window) is operable', { ...opts, skip: opts.skip || 'the fixture has no .NET/ActiveX container: no donor control in LabVIEW 2025 that can be pasted, and the composer\'s container part is untested (README, Known limits)' }, () => {});
