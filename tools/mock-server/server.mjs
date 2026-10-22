#!/usr/bin/env node
// RemoteVI reference server.
//
// Implements the server half of docs/protocol.md on raw TCP sockets - the same
// building blocks the G implementation has (TCP Listen/Read/Write) - against a
// simulated front panel. Use it to develop the web client without LabVIEW and
// as the behavioural reference for the LabVIEW side.
//
//   node tools/mock-server/server.mjs [--port 8080] [--host 127.0.0.1]
//        [--token <t> | --no-token] [--mode single|everyone|view] [--fps 30]

import net from 'node:net';
import fs from 'node:fs';
import path from 'node:path';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

import { PROTOCOL_VERSION, FRAME_FLAG_KEYFRAME, encodeFrame } from '../../web/js/protocol.js';
import { diffTiles, encodeTile, DEFAULT_TILE_SIZE } from '../lib/tiles.mjs';
import { findHeadEnd, parseRequestHead, isWebSocketUpgrade, buildResponseHead, HttpError, SECURITY_HEADERS } from '../lib/http.mjs';
import {
  acceptKey, decodeClientFrame, encodeServerFrame, closePayload, WsError,
  OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG, CLOSE_NORMAL, CLOSE_POLICY, CLOSE_PROTOCOL_ERROR,
} from '../lib/websocket.mjs';
import { SimulatedPanel } from './panel.mjs';

const HEAD_TIMEOUT_MS = 5000;
const HELLO_TIMEOUT_MS = 3000;
const MAX_CONNECTIONS = 16;
const FRAMES_IN_FLIGHT = 2;
const MAX_SOCKET_BACKLOG = 1 << 20;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon',
};

// --- configuration --------------------------------------------------------------

export function startServer(opts = {}) {
  const cfg = {
    port: 8080, host: '127.0.0.1', mode: 'single', fps: 30, token: randomBytes(9).toString('base64url'),
    webRoot: path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../web'),
    log: console.log,
    ...opts,
  };
  if (!['single', 'everyone', 'view'].includes(cfg.mode)) throw new Error(`invalid mode ${cfg.mode}`);

  const files = loadStaticFiles(cfg.webRoot);
  const panel = new SimulatedPanel();
  const sessions = new Set();
  let owner = null;
  let nextSessionId = 1;
  let connections = 0;

  // --- static files: a fixed table, never a filesystem lookup per request ------

  function loadStaticFiles(root) {
    const table = new Map();
    const walk = (dir) => {
      for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, ent.name);
        if (ent.isDirectory()) walk(full);
        else if (MIME[path.extname(ent.name)]) {
          const url = '/' + path.relative(root, full).split(path.sep).join('/');
          table.set(url, { type: MIME[path.extname(ent.name)], body: fs.readFileSync(full) });
        }
      }
    };
    walk(root);
    table.set('/', table.get('/index.html'));
    return table;
  }

  // --- roles -----------------------------------------------------------------

  const roleOf = (s) => (cfg.mode === 'everyone' ? 'controller' : cfg.mode === 'view' ? 'viewer' : s === owner ? 'controller' : 'viewer');

  function broadcastRoles() {
    for (const s of sessions) s.sendJson({ t: 'role', role: roleOf(s), owner: owner?.name ?? null });
  }

  function releaseOwner(s) {
    if (owner === s) {
      owner = null;
      broadcastRoles();
    }
  }

  // --- connection handling ---------------------------------------------------

  const server = net.createServer((socket) => {
    if (connections >= MAX_CONNECTIONS) {
      socket.end(buildResponseHead(503, { 'Content-Length': '0' }));
      return;
    }
    connections++;
    socket.setNoDelay(true); // latency over throughput: no Nagle
    socket.on('close', () => connections--);
    socket.on('error', () => {});
    handleHttp(socket);
  });

  function handleHttp(socket) {
    let buf = Buffer.alloc(0);
    const timer = setTimeout(() => fail(new HttpError(408, 'timeout')), HEAD_TIMEOUT_MS);

    function fail(err) {
      clearTimeout(timer);
      const status = err instanceof HttpError ? err.status : 400;
      socket.end(buildResponseHead(status, { 'Content-Length': '0' }));
    }

    function onData(chunk) {
      buf = Buffer.concat([buf, chunk]);
      let end;
      try {
        end = findHeadEnd(buf);
        if (end < 0) return;
        socket.off('data', onData);
        clearTimeout(timer);
        route(socket, parseRequestHead(buf.subarray(0, end).toString('latin1')), buf.subarray(end));
      } catch (err) {
        socket.off('data', onData);
        fail(err);
      }
    }
    socket.on('data', onData);
  }

  function route(socket, req, rest) {
    if (req.path === '/ws') {
      if (!isWebSocketUpgrade(req)) throw new HttpError(426, 'websocket upgrade required');
      // Browsers always send Origin on WebSocket handshakes; reject cross-site pages.
      const origin = req.headers['origin'];
      if (origin !== undefined) {
        let originHost;
        try { originHost = new URL(origin).host; } catch { originHost = null; }
        if (originHost !== req.headers['host']) throw new HttpError(403, 'cross-origin websocket');
      }
      socket.write(buildResponseHead(101, {
        Upgrade: 'websocket', Connection: 'Upgrade', 'Sec-WebSocket-Accept': acceptKey(req.headers['sec-websocket-key']),
      }));
      new Session(socket, rest);
      return;
    }
    const file = files.get(req.path);
    if (!file) throw new HttpError(404, 'not found');
    socket.end(Buffer.concat([
      Buffer.from(buildResponseHead(200, { 'Content-Type': file.type, 'Content-Length': String(file.body.length), ...SECURITY_HEADERS }), 'latin1'),
      file.body,
    ]));
  }

  // --- WebSocket sessions ----------------------------------------------------

  class Session {
    constructor(socket, initial) {
      this.socket = socket;
      this.id = nextSessionId++;
      this.name = `${socket.remoteAddress}#${this.id}`;
      this.buf = Buffer.alloc(0);
      this.authed = false;
      this.seq = 0;
      this.acked = 0;
      this.lastSent = null;
      this.closed = false;
      this.helloTimer = setTimeout(() => this.close(4401, 'hello timeout'), HELLO_TIMEOUT_MS);
      socket.on('data', (d) => this.onData(d));
      socket.on('close', () => this.onClose());
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
      // Client messages are small JSON objects; fragmentation is not needed and is refused.
      if (!fin || opcode !== OP_TEXT) return this.close(CLOSE_POLICY, 'only unfragmented text messages accepted');
      let msg;
      try { msg = JSON.parse(payload.toString('utf8')); } catch { return this.close(CLOSE_POLICY, 'invalid JSON'); }
      if (!msg || typeof msg.t !== 'string') return this.close(CLOSE_POLICY, 'invalid message');
      this.onMessage(msg);
    }

    onMessage(msg) {
      if (!this.authed) {
        if (msg.t !== 'hello') return this.close(4401, 'hello expected');
        if (msg.v !== PROTOCOL_VERSION) return this.close(4400, `protocol version ${PROTOCOL_VERSION} required`);
        if (!tokenOk(msg.token)) return this.close(4403, 'invalid token');
        clearTimeout(this.helloTimer);
        this.authed = true;
        sessions.add(this);
        if (cfg.mode === 'single' && owner === null) owner = this;
        this.sendJson({ t: 'welcome', v: PROTOCOL_VERSION, session: String(this.id), vi: 'Simulated Panel.vi',
          panel: { w: panel.width, h: panel.height }, mode: cfg.mode, role: roleOf(this) });
        this.sendJson({ t: 'layout', controls: panel.layout() });
        broadcastRoles();
        cfg.log(`session ${this.name} connected (${sessions.size} active)`);
        return;
      }
      switch (msg.t) {
        case 'ack':
          if (Number.isInteger(msg.seq) && msg.seq <= this.seq) this.acked = Math.max(this.acked, msg.seq);
          return;
        case 'ping':
          return this.sendJson({ t: 'pong', ts: msg.ts });
        case 'refresh':
          this.lastSent = null;
          return;
        case 'control':
          if (cfg.mode !== 'single') return;
          if (msg.action === 'request' && owner !== this) {
            // The newest requester takes over, as with LabVIEW Remote Panels' "Request Control".
            owner = this;
            broadcastRoles();
          } else if (msg.action === 'release') {
            releaseOwner(this);
          }
          return;
        case 'mouse':
        case 'key':
        case 'set': {
          if (roleOf(this) !== 'controller') return this.sendJson({ t: 'error', code: 'not-controller', message: 'Request control first' });
          try {
            const changes = msg.t === 'set' ? panel.set(msg.id, msg.value) : msg.t === 'mouse' ? panel.mouse(msg) : [];
            for (const c of changes) for (const s of sessions) s.sendJson({ t: 'value', ...c });
          } catch (err) {
            this.sendJson({ t: 'error', code: 'rejected', message: err.message });
          }
          return;
        }
        default:
          return; // unknown message types are ignored for forward compatibility
      }
    }

    sendJson(obj) {
      this.write(OP_TEXT, JSON.stringify(obj));
    }

    write(opcode, payload) {
      if (!this.closed) this.socket.write(encodeServerFrame(opcode, payload));
    }

    /** Send a frame if flow control allows. `encoded` caches tile encodings across sessions. */
    pushFrame(pixels, encoded) {
      if (this.seq - this.acked >= FRAMES_IN_FLIGHT || this.socket.writableLength > MAX_SOCKET_BACKLOG) return;
      const keyframe = this.lastSent === null;
      const dirty = diffTiles(this.lastSent, pixels, panel.width, panel.height, DEFAULT_TILE_SIZE);
      if (!dirty.length) return;
      const tiles = dirty.map((t) => {
        const k = t.y * panel.width + t.x;
        if (!encoded.has(k)) encoded.set(k, encodeTile(pixels, panel.width, t));
        return encoded.get(k);
      });
      this.seq++;
      this.write(OP_BINARY, Buffer.from(encodeFrame({ flags: keyframe ? FRAME_FLAG_KEYFRAME : 0, seq: this.seq,
        width: panel.width, height: panel.height, tiles })));
      this.lastSent = pixels.slice();
    }

    close(code, reason) {
      if (this.closed) return;
      this.write(OP_CLOSE, closePayload(code, reason));
      this.closed = true;
      this.socket.end();
      this.onClose();
    }

    onClose() {
      clearTimeout(this.helloTimer);
      this.closed = true;
      if (sessions.delete(this)) {
        releaseOwner(this);
        cfg.log(`session ${this.name} closed (${sessions.size} active)`);
      }
    }
  }

  function tokenOk(token) {
    if (cfg.token === null) return true;
    if (typeof token !== 'string') return false;
    const a = Buffer.from(token);
    const b = Buffer.from(cfg.token);
    return a.length === b.length && timingSafeEqual(a, b);
  }

  // --- capture loop ----------------------------------------------------------

  const timer = setInterval(() => {
    if (!sessions.size) return;
    const pixels = panel.render();
    const encoded = new Map();
    for (const s of sessions) s.pushFrame(pixels, encoded);
  }, Math.round(1000 / cfg.fps));

  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(cfg.port, cfg.host, () => {
      const { port } = server.address();
      const url = `http://${cfg.host}:${port}/${cfg.token ? `#token=${cfg.token}` : ''}`;
      resolve({
        url, port, token: cfg.token, panel,
        close: () => new Promise((r) => {
          clearInterval(timer);
          for (const s of sessions) s.close(1001, 'server shutting down');
          server.close(() => r());
        }),
      });
    });
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const { values } = parseArgs({
    options: {
      port: { type: 'string', default: '8080' }, host: { type: 'string', default: '127.0.0.1' },
      token: { type: 'string' }, 'no-token': { type: 'boolean', default: false },
      mode: { type: 'string', default: 'single' }, fps: { type: 'string', default: '30' },
    },
  });
  const opts = { port: Number(values.port), host: values.host, mode: values.mode, fps: Number(values.fps) };
  if (values['no-token']) opts.token = null;
  else if (values.token) opts.token = values.token;
  const srv = await startServer(opts);
  console.log(`RemoteVI reference server: open ${srv.url}`);
}
