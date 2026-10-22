// Applies FRAME messages to a canvas. The canvas is always the panel's native
// size; scaling for display is done with CSS so the bitmap stays pixel-exact.

import { ENC_SOLID, ENC_QOI, ENC_RAW_RGB, ProtocolError } from './protocol.js';
import { decodeQoi } from './qoi.js';

export class PanelRenderer {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', { alpha: false });
    this.width = 0;
    this.height = 0;
    this.scratch = new Map(); // "w x h" -> ImageData, reused to avoid GC churn
  }

  /** @param {ReturnType<import('./protocol.js').decodeFrame>} frame */
  apply(frame) {
    if (frame.width !== this.width || frame.height !== this.height) {
      if (!frame.keyframe) throw new ProtocolError('panel size changed without keyframe');
      this.width = this.canvas.width = frame.width;
      this.height = this.canvas.height = frame.height;
      this.scratch.clear();
    }
    for (const tile of frame.tiles) this.applyTile(tile);
  }

  applyTile(t) {
    switch (t.encoding) {
      case ENC_SOLID: {
        const [, r, g, b] = t.data;
        this.ctx.fillStyle = `rgb(${r},${g},${b})`;
        this.ctx.fillRect(t.x, t.y, t.w, t.h);
        return;
      }
      case ENC_QOI: {
        const img = this.imageData(t.w, t.h);
        const { width, height } = decodeQoi(t.data, img.data);
        if (width !== t.w || height !== t.h) throw new ProtocolError('QOI size does not match tile');
        this.ctx.putImageData(img, t.x, t.y);
        return;
      }
      case ENC_RAW_RGB: {
        if (t.data.byteLength !== t.w * t.h * 3) throw new ProtocolError('RAW tile has wrong length');
        const img = this.imageData(t.w, t.h);
        const d = img.data;
        for (let i = 0, o = 0; i < t.data.byteLength; i += 3, o += 4) {
          d[o] = t.data[i];
          d[o + 1] = t.data[i + 1];
          d[o + 2] = t.data[i + 2];
          d[o + 3] = 255;
        }
        this.ctx.putImageData(img, t.x, t.y);
        return;
      }
      default:
        throw new ProtocolError(`unknown tile encoding ${t.encoding}`);
    }
  }

  imageData(w, h) {
    const key = `${w}x${h}`;
    let img = this.scratch.get(key);
    if (!img) {
      img = this.ctx.createImageData(w, h);
      this.scratch.set(key, img);
    }
    return img;
  }
}
