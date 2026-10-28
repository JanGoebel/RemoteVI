#!/usr/bin/env node
// RemoteVI reference server, protocol v2.
//
// Does what the LabVIEW toolkit's server loop does (source/RemoteVI.lvlib,
// Server/Server Loop.vi), in the same single-loop shape, against a simulated
// panel: serve the one-file web client, upgrade /ws, stream dirty rectangles as
// PNGs with ack-based flow control, and turn input messages into Win32 messages.
// Use it to develop the web client without LabVIEW and as the behavioural
// reference for the G code.
//
//   node tools/mock-server/server.mjs [--port 8090] [--host 127.0.0.1] [--fps 30] [--view-only] [--token <t>]
//
// Like the toolkit, every request needs the share's access token as ?t=<token> (docs/security.md);
// without --token a random one is made and printed with the URL.

import net from 'node:net';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

import { findHeadEnd, parseRequestHead, isWebSocketUpgrade, buildResponseHead, HttpError, SECURITY_HEADERS, tokenOk } from '../lib/http.mjs';
import {
  acceptKey, decodeClientFrame, encodeServerFrame, closePayload, WsError,
  OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG, CLOSE_NORMAL, CLOSE_POLICY, CLOSE_PROTOCOL_ERROR,
} from '../lib/websocket.mjs';
import { encodeFrame, encodeOverlay, encodeWindowFrame, windowsMessage, tipsMessage, parseInput, FRAMES_IN_FLIGHT } from '../lib/protocol.mjs';
import { translateInput } from '../lib/input.mjs';
import { dirtyRects, crop } from '../lib/rects.mjs';
import { encodePng } from '../lib/png-encode.mjs';
import { SimulatedPanel } from './panel.mjs';

const HEAD_TIMEOUT_MS = 5000;
const MAX_CLIENTS = 8;

export function startServer(opts = {}) {
  const cfg = {
    port: 8090, host: '127.0.0.1', fps: 30, viewOnly: false, log: console.log, token: crypto.randomBytes(16).toString('hex'),
    indexPath: path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../web/index.html'),
    ...opts,
  };
  // The toolkit embeds index.html as a string constant; read it once, like that.
  const index = fs.readFileSync(cfg.indexPath);
  const panel = new SimulatedPanel();
  const clients = new Set();
  /** Every input message that reached the "panel window", for tests. */
  const posted = [];

  const server = net.createServer((socket) => {
    socket.setNoDelay(true);
    socket.on('error', () => {});
    readHead(socket);
  });

  function readHead(socket) {
    let buf = Buffer.alloc(0);
    const timer = setTimeout(() => fail(new HttpError(408, 'timeout')), HEAD_TIMEOUT_MS);
    const fail = (err) => {
      clearTimeout(timer);
      socket.end(buildResponseHead(err instanceof HttpError ? err.status : 400, { 'Content-Length': '0' }));
    };
    const onData = (chunk) => {
      buf = Buffer.concat([buf, chunk]);
      try {
        const end = findHeadEnd(buf);
        if (end < 0) return;
        socket.off('data', onData);
        clearTimeout(timer);
        route(socket, parseRequestHead(buf.subarray(0, end).toString('latin1')), buf.subarray(end));
      } catch (err) {
        socket.off('data', onData);
        fail(err);
      }
    };
    socket.on('data', onData);
  }

  function route(socket, req, rest) {
    // The page and the WebSocket both need the token; nothing else is served either way.
    const known = req.path === '/ws' || req.path === '/' || req.path === '/index.html';
    if (known && !tokenOk(req.search, cfg.token)) throw new HttpError(403, 'missing or wrong access token');
    if (req.path === '/ws') {
      if (!isWebSocketUpgrade(req)) throw new HttpError(426, 'websocket upgrade required');
      // Browsers always send Origin on WebSocket handshakes: refuse other sites' pages.
      const origin = req.headers['origin'];
      if (origin !== undefined) {
        let host = null;
        try { host = new URL(origin).host; } catch { /* invalid origin */ }
        if (host !== req.headers['host']) throw new HttpError(403, 'cross-origin websocket');
      }
      if (clients.size >= MAX_CLIENTS) throw new HttpError(503, 'too many clients');
      socket.write(buildResponseHead(101, {
        Upgrade: 'websocket', Connection: 'Upgrade', 'Sec-WebSocket-Accept': acceptKey(req.headers['sec-websocket-key']),
      }));
      new Client(socket, rest);
      return;
    }
    if (req.method !== 'GET' || (req.path !== '/' && req.path !== '/index.html')) throw new HttpError(404, 'not found');
    socket.end(Buffer.concat([
      Buffer.from(buildResponseHead(200, {
        'Content-Type': 'text/html; charset=utf-8', 'Content-Length': String(index.length), ...SECURITY_HEADERS,
      }), 'latin1'),
      index,
    ]));
  }

  class Client {
    constructor(socket, initial) {
      this.socket = socket;
      this.buf = Buffer.alloc(0);
      this.seq = 0;
      this.acked = 0;
      this.lastSent = null;
      this.closed = false;
      this.tracking = false;
      clients.add(this);
      socket.on('data', (d) => this.onData(d));
      socket.on('close', () => this.onClose());
      this.write(OP_TEXT, 'title Simulated Panel.vi');
      this.write(OP_TEXT, `viewonly ${cfg.viewOnly ? 1 : 0}`);
      this.write(OP_TEXT, 'origin 0 0'); // the simulated panel has no window frame
      if (overlay.message) this.write(OP_BINARY, overlay.message);
      this.write(OP_TEXT, windows.message);
      this.write(OP_TEXT, tips.message);
      this.windowSent = null;
      cfg.log(`client connected (${clients.size})`);
      if (initial.length) this.onData(initial);
    }

    onData(chunk) {
      this.buf = Buffer.concat([this.buf, chunk]);
      try {
        for (;;) {
          const f = decodeClientFrame(this.buf);
          if (!f) return;
          this.buf = this.buf.subarray(f.size);
          this.onWsFrame(f);
          if (this.closed) return;
        }
      } catch (err) {
        this.close(err instanceof WsError ? err.code : CLOSE_PROTOCOL_ERROR, err.message);
      }
    }

    onWsFrame({ fin, opcode, payload }) {
      if (opcode === OP_PING) return this.write(OP_PONG, payload);
      if (opcode === OP_PONG) return;
      if (opcode === OP_CLOSE) return this.close(CLOSE_NORMAL, '');
      if (!fin || opcode !== OP_TEXT) return this.close(CLOSE_POLICY, 'only unfragmented text messages accepted');
      const msg = parseInput(payload.toString('latin1'));
      if (!msg) return; // malformed input is ignored, not fatal
      if (msg.kind === 'close') {
        if (!cfg.viewOnly) panel.closeDialog(msg.id);
        return;
      }
      if (msg.kind === 'ack') {
        if (msg.seq <= this.seq) this.acked = Math.max(this.acked, msg.seq);
        return;
      }
      if (cfg.viewOnly) return;
      // Same translation the LabVIEW server does; the simulated window sits at the
      // screen origin with no toolbar, so client = panel coordinates.
      // Front-most window under the pointer gets mouse input, in its own client coordinates.
      const d = panel.dialog;
      if (d && msg.kind === 'mouse' && msg.x >= d.x && msg.x < d.x + d.w && msg.y >= d.y && msg.y < d.y + d.h) {
        posted.push({ msg: msg.msg, wParam: msg.wParam, window: d.id });
        panel.postDialog(msg.msg, msg.x - d.x, msg.y - d.y);
        return;
      }
      const t = translateInput(msg, { panelX: 0, panelY: 0, clientX: 0, clientY: 0 }, this.tracking);
      this.tracking = t.tracking;
      for (const p of t.posts) {
        posted.push(p);
        if (p.msg >= 0x200) panel.post(p.msg, p.lParam & 0xffff, p.lParam >>> 16, p.wParam >>> 0);
        else panel.key(p.msg, p.wParam);
      }
    }

    /** Send the changes since this client's last frame, if flow control allows. */
    push(pixels, pngCache) {
      if (this.closed || this.seq - this.acked >= FRAMES_IN_FLIGHT) return;
      const rects = dirtyRects(this.lastSent, pixels, panel.width, panel.height);
      if (!rects.length) return;
      const encoded = rects.map((r) => {
        const key = `${r.x},${r.y},${r.w},${r.h}`;
        if (!pngCache.has(key)) pngCache.set(key, encodePng(crop(pixels, panel.width, r), r.w, r.h));
        return { x: r.x, y: r.y, png: pngCache.get(key) };
      });
      this.seq++;
      this.write(OP_BINARY, encodeFrame(this.seq, panel.width, panel.height, encoded));
      this.lastSent = pixels.slice();
    }

    write(opcode, payload) {
      if (!this.closed) this.socket.write(encodeServerFrame(opcode, payload));
    }

    close(code, reason) {
      if (this.closed) return;
      this.write(OP_CLOSE, closePayload(code, reason));
      this.closed = true;
      this.socket.end();
      this.onClose();
    }

    onClose() {
      this.closed = true;
      if (clients.delete(this)) cfg.log(`client disconnected (${clients.size})`);
    }
  }

  // Popups go out as OVERLAY messages whenever they change, outside flow control
  // (they are small and rare). The LabVIEW server captures them with PrintWindow.
  const overlay = { key: '', message: null };

  // Other windows (docs/protocol.md 7): the list as text, each window's picture as
  // WINDOW FRAME. The simulated dialog is static, so one full frame per client is enough.
  const windows = { key: '', message: 'windows []' };
  function pushWindows() {
    const d = panel.dialog;
    const key = d ? `${d.id},${d.x},${d.y}` : '';
    if (key === windows.key) return;
    windows.key = key;
    windows.message = windowsMessage(d ? [{ ...d, modal: true, active: true, closable: true }] : []);
    for (const c of clients) { c.write(OP_TEXT, windows.message); c.windowSent = null; }
  }
  // Tip strips (docs/protocol.md 3.3): read with the geometry, never while a popup or
  // a modal window is open, and sent to every client when they changed.
  const tips = { message: tipsMessage(panel.tips()) };
  function pushTips() {
    if (panel.popup || panel.dialog) return;
    const message = tipsMessage(panel.tips());
    if (message === tips.message) return;
    tips.message = message;
    for (const c of clients) c.write(OP_TEXT, message);
  }
  function pushOverlay() {
    const p = panel.renderPopup();
    const key = p ? `${p.x},${p.y},${panel.state.mode}` : '';
    if (key === overlay.key) return;
    overlay.key = key;
    overlay.message = p ? encodeOverlay([{ x: p.x, y: p.y, png: encodePng(p.pixels, p.w, p.h) }]) : encodeOverlay([]);
    for (const c of clients) c.write(OP_BINARY, overlay.message);
    if (!p) overlay.message = null;
  }

  // The capture loop: one capture per tick, shared by all clients; each client
  // diffs against what it was last sent.
  const timer = setInterval(() => {
    if (!clients.size) return;
    pushOverlay();
    pushWindows();
    pushTips();
    const dlg = panel.renderDialog();
    if (dlg) {
      const png = encodePng(dlg.pixels, dlg.w, dlg.h);
      for (const c of clients) {
        if (c.windowSent === windows.key) continue;
        c.seq++;
        c.write(OP_BINARY, encodeWindowFrame(panel.dialog.id, c.seq, dlg.w, dlg.h, [{ x: 0, y: 0, png }]));
        c.windowSent = windows.key;
      }
    }
    const pixels = panel.render();
    const pngCache = new Map();
    for (const c of clients) c.push(pixels, pngCache);
  }, Math.round(1000 / cfg.fps));

  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(cfg.port, cfg.host, () => {
      const { port } = server.address();
      resolve({
        url: `http://${cfg.host}:${port}/?t=${cfg.token}`, port, token: cfg.token, panel, posted,
        close: () => new Promise((r) => {
          clearInterval(timer);
          for (const c of clients) c.close(1001, 'server shutting down');
          server.close(() => r());
        }),
      });
    });
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const { values } = parseArgs({
    options: {
      port: { type: 'string', default: '8090' }, host: { type: 'string', default: '127.0.0.1' },
      fps: { type: 'string', default: '30' }, 'view-only': { type: 'boolean', default: false }, token: { type: 'string' },
    },
  });
  const srv = await startServer({
    port: Number(values.port), host: values.host, fps: Number(values.fps), viewOnly: values['view-only'],
    ...(values.token ? { token: values.token } : {}),
  });
  console.log(`RemoteVI reference server: open ${srv.url}`);
}
