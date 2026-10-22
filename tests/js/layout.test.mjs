import { test } from 'node:test';
import assert from 'node:assert/strict';

import { hitTest, wantsOverlay, overlayRect, parseOverlayValue, toPanelCoords, modifiers } from '../../web/js/layout.js';

const controls = [
  { id: 'bg', kind: 'decoration', bounds: [0, 0, 100, 100] },
  { id: 'num', kind: 'numeric', bounds: [10, 10, 50, 20], edit: [10, 10, 40, 20] },
  { id: 'hidden', kind: 'string', bounds: [10, 10, 50, 20], visible: false },
  { id: 'ro', kind: 'string', bounds: [10, 50, 50, 20], readonly: true },
  { id: 'enum', kind: 'enum', bounds: [10, 80, 50, 15], items: ['A', 'B'] },
];

test('hit test returns the topmost visible control', () => {
  assert.equal(hitTest(controls, 15, 15).id, 'num'); // 'hidden' is above but invisible
  assert.equal(hitTest(controls, 59, 29).id, 'num');
  assert.equal(hitTest(controls, 60, 30).id, 'bg'); // bounds are half-open
  assert.equal(hitTest(controls, 200, 200), null);
});

test('overlay only for writable text-like controls', () => {
  assert.equal(wantsOverlay(controls[1]), true);
  assert.equal(wantsOverlay(controls[3]), false);
  assert.equal(wantsOverlay(controls[0]), false);
  assert.equal(wantsOverlay({ kind: 'numeric', bounds: [0, 0, 1, 1], disabled: true }), false);
  assert.equal(wantsOverlay(null), false);
  assert.deepEqual(overlayRect(controls[1]), [10, 10, 40, 20]);
  assert.deepEqual(overlayRect(controls[4]), [10, 80, 50, 15]);
});

test('overlay values are parsed per control kind', () => {
  assert.equal(parseOverlayValue(controls[1], ' 3,5 '), 3.5);
  assert.equal(parseOverlayValue(controls[1], '-1e3'), -1000);
  assert.throws(() => parseOverlayValue(controls[1], ''), RangeError);
  assert.throws(() => parseOverlayValue(controls[1], 'abc'), RangeError);
  assert.equal(parseOverlayValue(controls[4], '1'), 1);
  assert.throws(() => parseOverlayValue(controls[4], '2'), RangeError);
  assert.equal(parseOverlayValue({ kind: 'string' }, ' keep spaces '), ' keep spaces ');
});

test('client coordinates map to panel pixels at any CSS scale', () => {
  const rect = { left: 100, top: 50, width: 400, height: 200 };
  assert.deepEqual(toPanelCoords(rect, 800, 400, 100, 50), { x: 0, y: 0 });
  assert.deepEqual(toPanelCoords(rect, 800, 400, 300, 150), { x: 400, y: 200 });
  assert.deepEqual(toPanelCoords(rect, 800, 400, 9999, -5), { x: 799, y: 0 });
});

test('modifier bitmask', () => {
  assert.equal(modifiers({ shiftKey: true, ctrlKey: false, altKey: true, metaKey: false }), 5);
  assert.equal(modifiers({}), 0);
});
