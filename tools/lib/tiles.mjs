// Reference implementation of the capture pipeline's tile stage:
// diff two captures, pick the cheapest lossless encoding per dirty tile.
// Mirrors Capture/TileDiff.vi and Capture/EncodeTile.vi.

import { ENC_SOLID, ENC_QOI, ENC_RAW_RGB } from '../../web/js/protocol.js';
import { encodeQoi } from './qoi-encode.mjs';

export const DEFAULT_TILE_SIZE = 64;

/** Tile grid covering a width x height panel; edge tiles are clipped. */
export function tileGrid(width, height, tileSize = DEFAULT_TILE_SIZE) {
  const tiles = [];
  for (let y = 0; y < height; y += tileSize) {
    for (let x = 0; x < width; x += tileSize) {
      tiles.push({ x, y, w: Math.min(tileSize, width - x), h: Math.min(tileSize, height - y) });
    }
  }
  return tiles;
}

function tileEqual(a, b, stride, t) {
  for (let y = t.y; y < t.y + t.h; y++) {
    const row = y * stride;
    for (let x = t.x; x < t.x + t.w; x++) {
      if (a[row + x] !== b[row + x]) return false;
    }
  }
  return true;
}

/**
 * Tiles that differ between prev and cur. If prev is null or the panel size
 * changed, every tile is dirty (keyframe).
 */
export function diffTiles(prev, cur, width, height, tileSize = DEFAULT_TILE_SIZE) {
  const grid = tileGrid(width, height, tileSize);
  if (!prev || prev.length !== cur.length) return grid;
  return grid.filter((t) => !tileEqual(prev, cur, width, t));
}

/** Returns the colour if every pixel in the tile is identical, else -1. */
export function solidColor(pixels, stride, t) {
  const c = pixels[t.y * stride + t.x] & 0xffffff;
  for (let y = t.y; y < t.y + t.h; y++) {
    const row = y * stride;
    for (let x = t.x; x < t.x + t.w; x++) {
      if ((pixels[row + x] & 0xffffff) !== c) return -1;
    }
  }
  return c;
}

function encodeRaw(pixels, stride, t) {
  const out = new Uint8Array(t.w * t.h * 3);
  let p = 0;
  for (let y = t.y; y < t.y + t.h; y++) {
    const row = y * stride;
    for (let x = t.x; x < t.x + t.w; x++) {
      const px = pixels[row + x];
      out[p++] = (px >>> 16) & 0xff;
      out[p++] = (px >>> 8) & 0xff;
      out[p++] = px & 0xff;
    }
  }
  return out;
}

/** Encode one tile: SOLID if uniform, otherwise QOI, falling back to RAW if QOI is larger. */
export function encodeTile(pixels, stride, t) {
  const c = solidColor(pixels, stride, t);
  if (c >= 0) {
    return { ...t, encoding: ENC_SOLID, data: Uint8Array.of(0, (c >>> 16) & 0xff, (c >>> 8) & 0xff, c & 0xff) };
  }
  const qoi = encodeQoi(pixels, stride, t);
  if (qoi.byteLength < t.w * t.h * 3) return { ...t, encoding: ENC_QOI, data: qoi };
  return { ...t, encoding: ENC_RAW_RGB, data: encodeRaw(pixels, stride, t) };
}
