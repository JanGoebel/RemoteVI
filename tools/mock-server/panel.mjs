// A simulated LabVIEW front panel for the reference server: a software-rendered
// bitmap that reacts to the same Win32 mouse and keyboard messages the LabVIEW
// toolkit posts to a real panel window.

import { drawText } from './font5x7.mjs';

const PANEL_BG = 0xe6e6e6;
const CTRL_BG = 0xffffff;
const FRAME = 0x8c8c8c;
const TEXT = 0x000000;
const LED_ON = 0x2ecc40;
const LED_OFF = 0x1f4d24;
const CHART_BG = 0x101418;
const CHART_FG = 0xf0c419;
const POPUP_W = 110;
const POPUP_ITEM_H = 16;

export class SimulatedPanel {
  constructor() {
    this.width = 520;
    this.height = 300;
    this.pixels = new Uint32Array(this.width * this.height);
    this.t0 = Date.now();
    this.dragging = null;
    this.focus = null;
    /** Simulated popup menu {x, y, items} in panel coordinates, or null. */
    this.popup = null;
    this.state = { pump: false, setpoint: 2.5, gain: 4, mode: 1, operator: 'JANE', history: [] };
    this.controls = [
      { id: 'c1', label: 'Pump On', kind: 'boolean', mech: 'switch-when-pressed', bounds: [24, 40, 96, 30] },
      { id: 'c2', label: 'Setpoint', kind: 'numeric', bounds: [24, 104, 120, 22], edit: [24, 104, 104, 22], min: -10, max: 10 },
      { id: 'c3', label: 'Gain', kind: 'slider', bounds: [24, 160, 220, 22], min: 0, max: 10 },
      { id: 'c4', label: 'Mode', kind: 'enum', bounds: [24, 216, 120, 22], items: ['IDLE', 'RUN', 'CALIBRATE'] },
      { id: 'c5', label: 'Operator', kind: 'string', bounds: [24, 264, 160, 22] },
      { id: 'c6', label: 'Signal', kind: 'chart', readonly: true, bounds: [280, 40, 216, 146] },
      { id: 'c7', label: 'Status', kind: 'string', readonly: true, bounds: [280, 216, 216, 22] },
    ];
  }

  byId(id) {
    return this.controls.find((c) => c.id === id);
  }

  /**
   * Apply one Win32 mouse message at panel coordinates - the same messages the
   * LabVIEW toolkit posts to the real panel window. Reference behaviour only:
   * LabVIEW itself decides what a click does on a real panel.
   */
  post(msg, x, y, wParam) {
    if (this.popup) {
      // A real LabVIEW popup grabs all clicks: inside selects, outside closes.
      if (msg === 0x0201 || msg === 0x0204) {
        const i = Math.floor((y - this.popup.y - 2) / POPUP_ITEM_H);
        const inside = x >= this.popup.x && x < this.popup.x + POPUP_W && i >= 0 && i < this.popup.items.length;
        if (inside) this.state.mode = i;
        this.popup = null;
      }
      return;
    }
    if (msg === 0x0204) { // WM_RBUTTONDOWN: context menu at the pointer, may overflow the panel
      this.popup = { x, y, items: this.controls[3].items };
      return;
    }
    const hit = this.hit(x, y);
    switch (msg) {
      case 0x0201: // WM_LBUTTONDOWN
      case 0x0203: // WM_LBUTTONDBLCLK
        this.focus = hit?.id === 'c5' ? 'c5' : null;
        if (hit?.id === 'c1') this.state.pump = !this.state.pump; // switch when pressed
        if (hit?.id === 'c4') this.state.mode = (this.state.mode + 1) % hit.items.length;
        if (hit?.id === 'c3') {
          this.dragging = 'c3';
          this.slide(x);
        }
        break;
      case 0x0200: // WM_MOUSEMOVE
        if (this.dragging === 'c3' && (wParam & 1)) this.slide(x);
        break;
      case 0x0202: // WM_LBUTTONUP
        this.dragging = null;
        break;
      case 0x020a: { // WM_MOUSEWHEEL: signed delta in the high word of wParam
        const delta = (wParam >>> 16) << 16 >> 16;
        if (hit?.id === 'c2') {
          const v = this.state.setpoint + Math.sign(delta) * 0.1;
          this.state.setpoint = Math.round(Math.min(10, Math.max(-10, v)) * 10) / 10;
        }
        break;
      }
    }
  }

  /** The open popup as an image {x, y, w, h, pixels}, or null. */
  renderPopup() {
    if (!this.popup) return null;
    const { x, y, items } = this.popup;
    const w = POPUP_W, h = items.length * POPUP_ITEM_H + 4;
    const saved = { pixels: this.pixels, width: this.width, height: this.height };
    this.pixels = new Uint32Array(w * h);
    this.width = w;
    this.height = h;
    this.box([0, 0, w, h], CTRL_BG);
    items.forEach((item, i) => {
      if (i === this.state.mode) this.rect(1, 2 + i * POPUP_ITEM_H, w - 2, POPUP_ITEM_H, 0xcce4ff);
      drawText(this.pixels, w, 8, 6 + i * POPUP_ITEM_H, item, TEXT);
    });
    const img = { x, y, w, h, pixels: this.pixels };
    Object.assign(this, saved);
    return img;
  }

  /** Apply one Win32 keyboard message; only WM_CHAR into the focused string matters here. */
  key(msg, wParam) {
    if (msg !== 0x0102 || this.focus !== 'c5') return;
    if (wParam === 8) this.state.operator = this.state.operator.slice(0, -1);
    else if (wParam >= 32 && this.state.operator.length < 24) this.state.operator += String.fromCharCode(wParam).toUpperCase();
  }

  slide(x) {
    const c = this.byId('c3');
    const [bx, , bw] = c.bounds;
    const f = Math.min(1, Math.max(0, (x - bx - 6) / (bw - 12)));
    this.state.gain = Math.round(f * (c.max - c.min) * 10) / 10 + c.min;
  }

  hit(x, y) {
    for (let i = this.controls.length - 1; i >= 0; i--) {
      const [bx, by, bw, bh] = this.controls[i].bounds;
      if (x >= bx && y >= by && x < bx + bw && y < by + bh) return this.controls[i];
    }
    return null;
  }

  // --- rendering ----------------------------------------------------------

  /** Advance the simulation and redraw; returns the pixel buffer (0x00RRGGBB). */
  render() {
    const s = this.state;
    const t = (Date.now() - this.t0) / 1000;
    if (s.pump) {
      const amp = s.setpoint * (s.gain / 10);
      s.history.push(Math.sin(t * 2 * Math.PI * 0.5) * amp + Math.sin(t * 13) * 0.2 * (s.mode === 2 ? 1 : 0));
      if (s.history.length > 210) s.history.shift();
    }

    const px = this.pixels;
    px.fill(PANEL_BG);
    for (const c of this.controls) this.label(c);
    const [b, n, sl, en, st, ch, stat] = this.controls;

    this.box(b.bounds, s.pump ? 0xd9f2dc : 0xd4d4d4);
    this.rect(b.bounds[0] + 8, b.bounds[1] + 9, 12, 12, s.pump ? LED_ON : LED_OFF);
    drawText(px, this.width, b.bounds[0] + 28, b.bounds[1] + 12, s.pump ? 'ON' : 'OFF', TEXT);

    this.box(n.bounds, CTRL_BG);
    drawText(px, this.width, n.bounds[0] + 6, n.bounds[1] + 8, s.setpoint.toFixed(2), TEXT);
    this.rect(n.bounds[0] + 104, n.bounds[1], 16, 22, 0xd4d4d4);

    const [sx, sy, sw] = sl.bounds;
    this.rect(sx + 6, sy + 9, sw - 12, 4, FRAME);
    const knob = sx + 6 + Math.round(((s.gain - sl.min) / (sl.max - sl.min)) * (sw - 12));
    this.rect(knob - 5, sy + 1, 10, 20, 0x5b8def);
    drawText(px, this.width, sx + sw - 30, sy - 12, s.gain.toFixed(1), TEXT);

    this.box(en.bounds, CTRL_BG);
    drawText(px, this.width, en.bounds[0] + 6, en.bounds[1] + 8, en.items[s.mode], TEXT);

    this.box(st.bounds, CTRL_BG);
    drawText(px, this.width, st.bounds[0] + 6, st.bounds[1] + 8, s.operator, TEXT);

    this.chart(ch.bounds);

    this.box(stat.bounds, 0xf4f4f4);
    const status = s.pump ? `${en.items[s.mode]} T ${t.toFixed(1)}` : 'STOPPED';
    drawText(px, this.width, stat.bounds[0] + 6, stat.bounds[1] + 8, status, TEXT);
    return px;
  }

  chart([x, y, w, h]) {
    this.box([x, y, w, h], CHART_BG);
    const mid = y + Math.floor(h / 2);
    this.rect(x + 2, mid, w - 4, 1, 0x2a3138);
    const hist = this.state.history;
    let prevY = null;
    for (let i = 0; i < hist.length; i++) {
      const py = Math.max(y + 2, Math.min(y + h - 3, Math.round(mid - (hist[i] / 10) * (h / 2 - 4))));
      const lo = prevY === null ? py : Math.min(prevY, py);
      const hi = prevY === null ? py : Math.max(prevY, py);
      this.rect(x + 3 + i, lo, 1, hi - lo + 1, CHART_FG);
      prevY = py;
    }
  }

  label(c) {
    drawText(this.pixels, this.width, c.bounds[0], c.bounds[1] - 12, c.label, TEXT);
  }

  box([x, y, w, h], fill) {
    this.rect(x, y, w, h, FRAME);
    this.rect(x + 1, y + 1, w - 2, h - 2, fill);
  }

  rect(x, y, w, h, color) {
    const x0 = Math.max(0, x), y0 = Math.max(0, y);
    const x1 = Math.min(this.width, x + w), y1 = Math.min(this.height, y + h);
    for (let yy = y0; yy < y1; yy++) this.pixels.fill(color, yy * this.width + x0, yy * this.width + x1);
  }
}
