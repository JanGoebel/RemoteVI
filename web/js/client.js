// RemoteVI browser client: connection, flow control, input forwarding, overlays.

import { PROTOCOL_VERSION, decodeFrame, parseTextMessage } from './protocol.js';
import { PanelRenderer } from './renderer.js';
import { hitTest, wantsOverlay, overlayRect, parseOverlayValue, toPanelCoords, modifiers } from './layout.js';

const CLIENT_ID = 'remotevi-web/0.1';
const PING_INTERVAL_MS = 2000;
const MAX_BACKOFF_MS = 5000;

class RemoteViClient {
  constructor(root) {
    this.root = root;
    this.canvas = root.querySelector('#panel');
    this.stage = root.querySelector('#stage');
    this.statusEl = root.querySelector('#status');
    this.statsEl = root.querySelector('#stats');
    this.titleEl = root.querySelector('#vi-name');
    this.controlBtn = root.querySelector('#control-btn');
    this.fitBtn = root.querySelector('#fit-btn');
    this.renderer = new PanelRenderer(this.canvas);

    this.ws = null;
    this.backoff = 250;
    this.role = 'viewer';
    this.mode = 'single';
    this.controls = [];
    this.values = new Map();
    this.overlay = null;
    this.pendingMove = null;
    this.buttons = 0;
    this.stats = { frames: 0, bytes: 0, rtt: NaN, since: performance.now() };

    // Token travels in the URL fragment so it never reaches server or proxy logs.
    this.token = new URLSearchParams(location.hash.slice(1)).get('token') ?? '';

    this.bindInput();
    this.controlBtn.addEventListener('click', () => this.toggleControl());
    this.fitBtn.addEventListener('click', () => this.toggleFit());
    setInterval(() => this.tick(), PING_INTERVAL_MS);
    this.connect();
  }

  // --- connection -----------------------------------------------------------

  connect() {
    const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${scheme}://${location.host}/ws`);
    ws.binaryType = 'arraybuffer';
    this.ws = ws;
    this.setStatus('connecting', 'Connecting…');

    ws.onopen = () => {
      this.backoff = 250;
      this.send({ t: 'hello', v: PROTOCOL_VERSION, client: CLIENT_ID, token: this.token });
    };
    ws.onmessage = (ev) => {
      try {
        if (typeof ev.data === 'string') this.onText(ev.data);
        else this.onFrame(ev.data);
      } catch (err) {
        console.error(err);
        ws.close(4000, 'client protocol error');
      }
    };
    ws.onclose = (ev) => {
      if (this.ws !== ws) return;
      this.closeOverlay();
      this.setRole('viewer');
      const fatal = ev.code === 4401 || ev.code === 4403 || ev.code === 1008;
      if (fatal) {
        this.setStatus('error', ev.reason || 'Access denied');
        return;
      }
      this.setStatus('offline', `Disconnected – retrying in ${(this.backoff / 1000).toFixed(1)} s`);
      setTimeout(() => this.connect(), this.backoff);
      this.backoff = Math.min(this.backoff * 2, MAX_BACKOFF_MS);
    };
  }

  send(msg) {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(msg));
  }

  onFrame(buf) {
    const frame = decodeFrame(buf);
    this.renderer.apply(frame);
    this.stats.frames++;
    this.stats.bytes += buf.byteLength;
    // Ack after painting: the server never has more than a couple of frames in
    // flight, so a slow client gets fresher frames instead of a growing backlog.
    this.send({ t: 'ack', seq: frame.seq });
  }

  onText(text) {
    const msg = parseTextMessage(text);
    if (!msg) return;
    switch (msg.t) {
      case 'welcome':
        this.mode = msg.mode;
        this.titleEl.textContent = msg.vi ?? '';
        document.title = `${msg.vi ?? 'RemoteVI'} – RemoteVI`;
        this.setStatus('online', 'Connected');
        this.setRole(msg.role);
        break;
      case 'layout':
        this.controls = Array.isArray(msg.controls) ? msg.controls : [];
        for (const c of this.controls) if ('value' in c) this.values.set(c.id, c.value);
        break;
      case 'value':
        this.values.set(msg.id, msg.value);
        break;
      case 'role':
        this.setRole(msg.role, msg.owner);
        break;
      case 'pong':
        this.stats.rtt = performance.now() - msg.ts;
        break;
      case 'error':
        console.warn('RemoteVI server error', msg.code, msg.message);
        this.flash(msg.message ?? msg.code);
        break;
    }
  }

  tick() {
    this.send({ t: 'ping', ts: performance.now() });
    const secs = (performance.now() - this.stats.since) / 1000;
    const fps = this.stats.frames / secs;
    const kbps = this.stats.bytes / 1024 / secs;
    const rtt = Number.isFinite(this.stats.rtt) ? `${this.stats.rtt.toFixed(0)} ms` : '–';
    this.statsEl.textContent = `${fps.toFixed(0)} fps · ${kbps.toFixed(0)} KiB/s · RTT ${rtt}`;
    this.stats.frames = 0;
    this.stats.bytes = 0;
    this.stats.since = performance.now();
  }

  // --- role / control ownership --------------------------------------------

  setRole(role, owner) {
    this.role = role === 'controller' ? 'controller' : 'viewer';
    this.root.dataset.role = this.role;
    if (this.mode === 'view') {
      this.controlBtn.hidden = true;
    } else {
      this.controlBtn.hidden = this.mode === 'everyone';
      this.controlBtn.textContent = this.role === 'controller' ? 'Release control' : 'Request control';
      this.controlBtn.title = owner && this.role !== 'controller' ? `Currently controlled by ${owner}` : '';
    }
    if (this.role !== 'controller') this.closeOverlay();
  }

  toggleControl() {
    this.send({ t: 'control', action: this.role === 'controller' ? 'release' : 'request' });
  }

  toggleFit() {
    const fit = this.stage.classList.toggle('fit');
    this.fitBtn.setAttribute('aria-pressed', String(fit));
  }

  // --- input ----------------------------------------------------------------

  panelPoint(e) {
    return toPanelCoords(this.canvas.getBoundingClientRect(), this.canvas.width, this.canvas.height, e.clientX, e.clientY);
  }

  bindInput() {
    const c = this.canvas;
    c.addEventListener('contextmenu', (e) => e.preventDefault());

    c.addEventListener('pointerdown', (e) => {
      if (this.role !== 'controller') return;
      e.preventDefault();
      c.focus();
      const { x, y } = this.panelPoint(e);
      const hit = hitTest(this.controls, x, y);
      if (e.button === 0 && wantsOverlay(hit)) {
        this.openOverlay(hit);
        return;
      }
      this.closeOverlay();
      c.setPointerCapture(e.pointerId);
      this.buttons = e.buttons;
      this.send({ t: 'mouse', e: 'down', x, y, b: e.button, mods: modifiers(e) });
    });

    c.addEventListener('pointermove', (e) => {
      if (this.role !== 'controller') return;
      // Coalesce moves to one per animation frame; only the latest position matters.
      const first = this.pendingMove === null;
      this.pendingMove = { ...this.panelPoint(e), b: e.buttons, mods: modifiers(e) };
      if (first) {
        requestAnimationFrame(() => {
          const m = this.pendingMove;
          this.pendingMove = null;
          if (m) this.send({ t: 'mouse', e: 'move', ...m });
        });
      }
    });

    const up = (e) => {
      if (this.role !== 'controller' || !this.buttons) return;
      this.buttons = e.buttons;
      const { x, y } = this.panelPoint(e);
      this.send({ t: 'mouse', e: 'up', x, y, b: e.button, mods: modifiers(e) });
    };
    c.addEventListener('pointerup', up);
    c.addEventListener('pointercancel', up);

    c.addEventListener('wheel', (e) => {
      if (this.role !== 'controller') return;
      e.preventDefault();
      const { x, y } = this.panelPoint(e);
      this.send({ t: 'mouse', e: 'wheel', x, y, dy: Math.sign(e.deltaY), mods: modifiers(e) });
    }, { passive: false });

    c.addEventListener('keydown', (e) => {
      if (this.role !== 'controller' || this.overlay) return;
      e.preventDefault();
      this.send({ t: 'key', e: 'down', key: e.key, code: e.code, mods: modifiers(e) });
    });
    c.addEventListener('keyup', (e) => {
      if (this.role !== 'controller' || this.overlay) return;
      this.send({ t: 'key', e: 'up', key: e.key, code: e.code, mods: modifiers(e) });
    });
  }

  // --- overlay editors ------------------------------------------------------

  openOverlay(control) {
    this.closeOverlay();
    const [x, y, w, h] = overlayRect(control);
    const isList = control.kind === 'enum' || control.kind === 'ring';
    const el = document.createElement(isList ? 'select' : 'input');
    el.className = 'overlay';
    el.setAttribute('aria-label', control.label || control.id);
    const current = this.values.get(control.id);
    if (isList) {
      (control.items ?? []).forEach((item, i) => el.add(new Option(item, String(i))));
      el.value = String(current ?? 0);
    } else {
      el.type = 'text';
      el.spellcheck = false;
      el.value = current == null ? '' : String(current);
    }
    // Panel pixels -> CSS pixels, so overlays line up in 1:1 and in fit mode.
    const s = this.canvas.getBoundingClientRect().width / this.canvas.width;
    Object.assign(el.style, { left: `${x * s}px`, top: `${y * s}px`, width: `${w * s}px`, height: `${h * s}px` });

    const commit = () => {
      try {
        const value = parseOverlayValue(control, el.value);
        this.send({ t: 'set', id: control.id, value });
        this.values.set(control.id, value);
        this.closeOverlay();
      } catch {
        el.classList.add('invalid');
        el.focus();
      }
    };
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !(control.kind === 'string' && control.multiline && !e.ctrlKey)) {
        e.preventDefault();
        commit();
      } else if (e.key === 'Escape') {
        this.closeOverlay();
      }
    });
    if (isList) el.addEventListener('change', commit);
    el.addEventListener('blur', () => { if (this.overlay?.el === el) this.closeOverlay(); });

    this.canvas.parentElement.appendChild(el);
    this.overlay = { el, control };
    el.focus();
    if (!isList) el.select();
  }

  closeOverlay() {
    if (!this.overlay) return;
    const { el } = this.overlay;
    this.overlay = null;
    el.remove();
    this.canvas.focus();
  }

  // --- status ---------------------------------------------------------------

  setStatus(state, text) {
    this.root.dataset.state = state;
    this.statusEl.textContent = text;
  }

  flash(text) {
    const prev = this.statusEl.textContent;
    this.statusEl.textContent = text;
    setTimeout(() => { if (this.statusEl.textContent === text) this.statusEl.textContent = prev; }, 2500);
  }
}

new RemoteViClient(document.body);
