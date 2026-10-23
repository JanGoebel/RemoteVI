// Reference implementation of the capture pipeline's diff stage. Mirrors
// Capture/Dirty Rects.vi: compare two captures in a grid of tiles, then merge
// the dirty tiles of each tile row into one rectangle (a "band"). One PNG per
// band keeps the number of encoder calls low while still sending only the parts
// of the panel that changed.

export const DEFAULT_TILE_SIZE = 64;

function tileEqual(a, b, stride, x0, y0, w, h) {
  for (let y = y0; y < y0 + h; y++) {
    const row = y * stride;
    for (let x = x0; x < x0 + w; x++) {
      if (a[row + x] !== b[row + x]) return false;
    }
  }
  return true;
}

/**
 * Dirty rectangles between prev and cur (Uint32Array, 0x00RRGGBB, row-major).
 * If prev is null or the size changed, the whole panel is one rectangle.
 * @returns {{x:number,y:number,w:number,h:number}[]}
 */
export function dirtyRects(prev, cur, width, height, tileSize = DEFAULT_TILE_SIZE) {
  if (!prev || prev.length !== cur.length) return [{ x: 0, y: 0, w: width, h: height }];
  const rects = [];
  for (let y = 0; y < height; y += tileSize) {
    const h = Math.min(tileSize, height - y);
    let first = -1;
    let last = -1;
    for (let x = 0; x < width; x += tileSize) {
      const w = Math.min(tileSize, width - x);
      if (!tileEqual(prev, cur, width, x, y, w, h)) {
        if (first < 0) first = x;
        last = x + w;
      }
    }
    if (first >= 0) rects.push({ x: first, y, w: last - first, h });
  }
  return rects;
}

/** Copy a rectangle out of a pixel buffer. */
export function crop(pixels, stride, { x, y, w, h }) {
  const out = new Uint32Array(w * h);
  for (let r = 0; r < h; r++) out.set(pixels.subarray((y + r) * stride + x, (y + r) * stride + x + w), r * w);
  return out;
}
