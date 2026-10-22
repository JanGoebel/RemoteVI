import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

import { decodeQoi, QoiError } from '../../web/js/qoi.js';
import { decodeFrame, encodeFrame, ProtocolError, ENC_SOLID, ENC_QOI, ENC_RAW_RGB, FRAME_FLAG_KEYFRAME } from '../../web/js/protocol.js';
import { encodeQoi } from '../../tools/lib/qoi-encode.mjs';
import { diffTiles, encodeTile, tileGrid, solidColor } from '../../tools/lib/tiles.mjs';

const vectors = (name) => JSON.parse(fs.readFileSync(new URL(`../vectors/${name}`, import.meta.url)));
const fromHex = (h) => new Uint8Array(Buffer.from(h, 'hex'));

/** Decode RGBA back into 0x00RRGGBB for comparison with source pixels. */
function rgbaToPixels(rgba) {
  const out = new Uint32Array(rgba.length / 4);
  for (let i = 0; i < out.length; i++) out[i] = (rgba[i * 4] << 16) | (rgba[i * 4 + 1] << 8) | rgba[i * 4 + 2];
  return out;
}

function randomImage(w, h, seed, colors = 0) {
  let s = seed;
  const rnd = () => ((s = (Math.imul(s, 1103515245) + 12345) >>> 0) / 2 ** 32);
  const palette = Array.from({ length: colors }, () => Math.floor(rnd() * 0x1000000));
  return Uint32Array.from({ length: w * h }, () => (colors ? palette[Math.floor(rnd() * colors)] : Math.floor(rnd() * 0x1000000)));
}

test('QOI encoder matches committed vectors', () => {
  for (const c of vectors('qoi.json').cases) {
    const out = encodeQoi(Uint32Array.from(c.pixels), c.width, { x: 0, y: 0, w: c.width, h: c.height });
    assert.equal(Buffer.from(out).toString('hex'), c.qoi, c.name);
  }
});

test('QOI decoder reproduces vector pixels', () => {
  for (const c of vectors('qoi.json').cases) {
    const { width, height, channels, rgba } = decodeQoi(fromHex(c.qoi));
    assert.deepEqual([width, height, channels], [c.width, c.height, 3], c.name);
    assert.deepEqual(Array.from(rgbaToPixels(rgba)), c.pixels, c.name);
    for (let i = 3; i < rgba.length; i += 4) assert.equal(rgba[i], 255);
  }
});

test('QOI round-trips random, noisy and palette images, including sub-rectangles', () => {
  const cases = [[64, 64, 1, 0], [64, 64, 2, 6], [33, 17, 3, 2], [1, 200, 4, 3], [200, 1, 5, 0]];
  for (const [w, h, seed, colors] of cases) {
    const px = randomImage(w, h, seed, colors);
    const back = rgbaToPixels(decodeQoi(encodeQoi(px, w, { x: 0, y: 0, w, h })).rgba);
    assert.deepEqual(back, px, `${w}x${h} seed ${seed}`);
  }
  const px = randomImage(50, 40, 9, 4);
  const rect = { x: 7, y: 5, w: 20, h: 11 };
  const back = rgbaToPixels(decodeQoi(encodeQoi(px, 50, rect)).rgba);
  for (let y = 0; y < rect.h; y++) {
    for (let x = 0; x < rect.w; x++) assert.equal(back[y * rect.w + x], px[(rect.y + y) * 50 + rect.x + x]);
  }
});

test('QOI decoder rejects malformed input', () => {
  const good = fromHex(vectors('qoi.json').cases.find((c) => c.name === 'solid 8x8 panel grey').qoi);
  assert.throws(() => decodeQoi(good.subarray(0, 10)), QoiError);
  const badMagic = good.slice(); badMagic[0] = 0x51;
  assert.throws(() => decodeQoi(badMagic), /magic/);
  const badChannels = good.slice(); badChannels[12] = 5;
  assert.throws(() => decodeQoi(badChannels), /channel/);
  const zero = good.slice(); zero.fill(0, 4, 8);
  assert.throws(() => decodeQoi(zero), /dimensions/);
  const huge = good.slice(); huge.set([0, 0, 0x10, 0], 4); // claims 4096 px wide, data runs out
  assert.throws(() => decodeQoi(huge), /ran out of data/);
  assert.throws(() => decodeQoi(good, new Uint8ClampedArray(4)), /too small/);
});

test('tile grid clips edge tiles', () => {
  const v = vectors('tiles.json');
  assert.deepEqual(tileGrid(v.grid.width, v.grid.height, v.tileSize), v.grid.tiles);
  const area = v.grid.tiles.reduce((a, t) => a + t.w * t.h, 0);
  assert.equal(area, v.grid.width * v.grid.height);
});

test('tile diff finds exactly the changed tiles; null prev means keyframe', () => {
  const { diff, tileSize, grid } = vectors('tiles.json');
  const before = Uint32Array.from(diff.before);
  const after = Uint32Array.from(diff.after);
  assert.deepEqual(diffTiles(before, after, diff.width, diff.height, tileSize), diff.dirty);
  assert.deepEqual(diffTiles(before, before, diff.width, diff.height, tileSize), []);
  assert.equal(diffTiles(null, after, diff.width, diff.height, tileSize).length, grid.tiles.length);
});

test('tile encoding picks SOLID / QOI / RAW and matches vectors', () => {
  const { diff, encodeTile: expected } = vectors('tiles.json');
  const px = Uint32Array.from(diff.before);
  for (const e of expected) {
    const t = encodeTile(px, diff.width, e);
    assert.equal(t.encoding, e.encoding, `tile ${e.x},${e.y}`);
    assert.equal(Buffer.from(t.data).toString('hex'), e.data, `tile ${e.x},${e.y}`);
    if (t.encoding === ENC_RAW_RGB) assert.equal(t.data.byteLength, e.w * e.h * 3);
  }
  assert.ok(new Set(expected.map((e) => e.encoding)).size === 3, 'vectors cover all encodings');
  assert.equal(solidColor(Uint32Array.of(1, 1, 1, 2), 2, { x: 0, y: 0, w: 2, h: 2 }), -1);
});

test('FRAME encode matches vector and decodes back', () => {
  for (const c of vectors('frame.json').cases) {
    const tiles = c.tiles.map((t) => ({ ...t, data: fromHex(t.data) }));
    const msg = encodeFrame({ flags: c.flags, seq: c.seq, width: c.width, height: c.height, tiles });
    assert.equal(Buffer.from(msg).toString('hex'), c.message);
    const f = decodeFrame(fromHex(c.message));
    assert.equal(f.keyframe, true);
    assert.deepEqual([f.seq, f.width, f.height, f.tiles.length], [c.seq, c.width, c.height, c.tiles.length]);
    assert.deepEqual(f.tiles.map((t) => t.encoding), [ENC_SOLID, ENC_QOI, ENC_RAW_RGB]);
  }
});

test('FRAME decoder rejects truncated, oversized and trailing data', () => {
  const tile = { x: 0, y: 0, w: 2, h: 2, encoding: ENC_SOLID, data: Uint8Array.of(0, 1, 2, 3) };
  const msg = encodeFrame({ flags: FRAME_FLAG_KEYFRAME, seq: 1, width: 2, height: 2, tiles: [tile] });
  assert.throws(() => decodeFrame(msg.subarray(0, 5)), ProtocolError);
  assert.throws(() => decodeFrame(msg.subarray(0, 20)), /truncated header/);
  assert.throws(() => decodeFrame(msg.subarray(0, msg.length - 1)), /truncated payload/);
  assert.throws(() => decodeFrame(Uint8Array.of(...msg, 0)), /trailing/);
  const outside = encodeFrame({ seq: 1, width: 2, height: 2, tiles: [{ ...tile, x: 1 }] });
  assert.throws(() => decodeFrame(outside), /outside panel/);
  const wrongType = msg.slice(); wrongType[0] = 0x11;
  assert.throws(() => decodeFrame(wrongType), /message type/);
});

test('full pipeline: diff + encode + frame + decode reconstructs the panel exactly', () => {
  const w = 300, h = 170;
  const a = randomImage(w, h, 11, 5);
  const b = a.slice();
  for (let i = 0; i < 400; i++) b[(i * 7919) % b.length] = 0x123456;
  const canvas = new Uint32Array(w * h);
  let prev = null;
  for (const [seq, cur] of [[1, a], [2, b]]) {
    const tiles = diffTiles(prev, cur, w, h).map((t) => encodeTile(cur, w, t));
    const frame = decodeFrame(encodeFrame({ flags: prev ? 0 : FRAME_FLAG_KEYFRAME, seq, width: w, height: h, tiles }));
    for (const t of frame.tiles) {
      const tilePx = t.encoding === ENC_QOI ? rgbaToPixels(decodeQoi(t.data).rgba)
        : t.encoding === ENC_SOLID ? new Uint32Array(t.w * t.h).fill((t.data[1] << 16) | (t.data[2] << 8) | t.data[3])
          : Uint32Array.from({ length: t.w * t.h }, (_, i) => (t.data[i * 3] << 16) | (t.data[i * 3 + 1] << 8) | t.data[i * 3 + 2]);
      for (let y = 0; y < t.h; y++) canvas.set(tilePx.subarray(y * t.w, (y + 1) * t.w), (t.y + y) * w + t.x);
    }
    assert.deepEqual(canvas, cur, `after frame ${seq}`);
    prev = cur;
  }
});
