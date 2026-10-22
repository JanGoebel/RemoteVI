// End-to-end tests against the reference server over real sockets.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';

import { startServer } from '../../tools/mock-server/server.mjs';
import { decodeFrame, ENC_SOLID, ENC_QOI, ENC_RAW_RGB } from '../../web/js/protocol.js';
import { decodeQoi } from '../../web/js/qoi.js';

let srv;
before(async () => {
  srv = await startServer({ port: 0, token: 'secret-token', fps: 60, log: () => {} });
});
after(() => srv.close());

/** Raw HTTP request; resolves with the full response text once the server closes. */
function rawRequest(text) {
  return new Promise((resolve, reject) => {
    const s = net.connect(srv.port, '127.0.0.1', () => s.write(text));
    const chunks = [];
    s.on('data', (d) => chunks.push(d));
    s.on('end', () => resolve(Buffer.concat(chunks).toString('latin1')));
    s.on('error', reject);
  });
}

/** WebSocket client that queues messages so tests can await them in order. */
function connect() {
  const ws = new WebSocket(`ws://127.0.0.1:${srv.port}/ws`);
  ws.binaryType = 'arraybuffer';
  const queue = [];
  const waiters = [];
  const push = (item) => {
    const i = waiters.findIndex((w) => w.pred(item));
    if (i >= 0) waiters.splice(i, 1)[0].resolve(item);
    else queue.push(item);
  };
  ws.onmessage = (ev) => push(typeof ev.data === 'string' ? JSON.parse(ev.data) : { binary: new Uint8Array(ev.data) });
  ws.onclose = (ev) => push({ closed: ev.code, reason: ev.reason });
  return {
    ws,
    opened: new Promise((r) => { ws.onopen = r; }),
    send: (m) => ws.send(JSON.stringify(m)),
    next(pred = () => true, ms = 2000) {
      const i = queue.findIndex(pred);
      if (i >= 0) return Promise.resolve(queue.splice(i, 1)[0]);
      return new Promise((resolve, reject) => {
        const w = { pred, resolve };
        waiters.push(w);
        setTimeout(() => {
          const j = waiters.indexOf(w);
          if (j >= 0) { waiters.splice(j, 1); reject(new Error('timed out waiting for message')); }
        }, ms);
      });
    },
  };
}

async function hello(token = 'secret-token') {
  const c = connect();
  await c.opened;
  c.send({ t: 'hello', v: 1, client: 'test', token });
  return c;
}

test('static files are served from the fixed table with security headers', async () => {
  const res = await rawRequest('GET / HTTP/1.1\r\nHost: x\r\n\r\n');
  assert.match(res, /^HTTP\/1\.1 200 OK\r\n/);
  assert.match(res, /Content-Security-Policy: default-src 'self'/);
  assert.match(res, /X-Content-Type-Options: nosniff/);
  assert.match(res, /<canvas id="panel"/);
});

test('unknown paths, traversal attempts and other methods are rejected', async () => {
  assert.match(await rawRequest('GET /../package.json HTTP/1.1\r\nHost: x\r\n\r\n'), /^HTTP\/1\.1 404 /);
  assert.match(await rawRequest('GET /%2e%2e/package.json HTTP/1.1\r\nHost: x\r\n\r\n'), /^HTTP\/1\.1 404 /);
  assert.match(await rawRequest('POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n'), /^HTTP\/1\.1 405 /);
  assert.match(await rawRequest('GET /ws HTTP/1.1\r\nHost: x\r\n\r\n'), /^HTTP\/1\.1 426 /);
});

test('cross-origin WebSocket handshakes are refused', async () => {
  const res = await rawRequest(`GET /ws HTTP/1.1\r\nHost: 127.0.0.1:${srv.port}\r\nOrigin: http://evil.example\r\n`
    + 'Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n');
  assert.match(res, /^HTTP\/1\.1 403 /);
});

test('wrong token closes the session with 4403', async () => {
  const c = await hello('wrong');
  const msg = await c.next((m) => 'closed' in m);
  assert.equal(msg.closed, 4403);
});

test('messages before hello are refused', async () => {
  const c = connect();
  await c.opened;
  c.send({ t: 'set', id: 'c2', value: 1 });
  assert.equal((await c.next((m) => 'closed' in m)).closed, 4401);
});

test('keyframe reconstructs the panel pixel-exactly, deltas follow, acks pace the stream', async () => {
  const c = await hello();
  const welcome = await c.next((m) => m.t === 'welcome');
  assert.equal(welcome.role, 'controller');
  const layout = await c.next((m) => m.t === 'layout');
  assert.ok(layout.controls.some((x) => x.id === 'c2' && x.value === 2.5));

  const first = decodeFrame((await c.next((m) => m.binary)).binary);
  assert.equal(first.keyframe, true);
  const img = new Uint32Array(first.width * first.height);
  const paint = (frame) => {
    for (const t of frame.tiles) {
      for (let y = 0; y < t.h; y++) {
        for (let x = 0; x < t.w; x++) {
          let px;
          if (t.encoding === ENC_SOLID) px = (t.data[1] << 16) | (t.data[2] << 8) | t.data[3];
          else if (t.encoding === ENC_RAW_RGB) { const i = (y * t.w + x) * 3; px = (t.data[i] << 16) | (t.data[i + 1] << 8) | t.data[i + 2]; }
          else if (t.encoding === ENC_QOI) { const d = (t.decoded ??= decodeQoi(t.data).rgba); const i = (y * t.w + x) * 4; px = (d[i] << 16) | (d[i + 1] << 8) | d[i + 2]; }
          img[(t.y + y) * frame.width + t.x + x] = px;
        }
      }
    }
  };
  paint(first);
  // With the pump off the simulated panel is static, so a fresh render must equal what we rebuilt.
  assert.deepEqual(img, srv.panel.render().slice());

  // Without acks the server stops after FRAMES_IN_FLIGHT frames, even with a changing panel.
  c.send({ t: 'mouse', e: 'down', x: 30, y: 50, b: 0, mods: 0 }); // toggles the pump -> chart animates
  const second = decodeFrame((await c.next((m) => m.binary)).binary);
  assert.equal(second.keyframe, false);
  assert.ok(second.tiles.length > 0 && second.tiles.length < 40, 'only dirty tiles are sent');
  await assert.rejects(c.next((m) => m.binary, 300), /timed out/);

  c.send({ t: 'ack', seq: second.seq });
  const third = decodeFrame((await c.next((m) => m.binary)).binary);
  assert.equal(third.seq, second.seq + 1);
  c.send({ t: 'mouse', e: 'down', x: 30, y: 50, b: 0, mods: 0 }); // pump off again for other tests
  c.ws.close();
});

test('single-controller mode: viewers are read-only until they request control', async () => {
  const a = await hello();
  assert.equal((await a.next((m) => m.t === 'welcome')).role, 'controller');
  const b = await hello();
  assert.equal((await b.next((m) => m.t === 'welcome')).role, 'viewer');

  b.send({ t: 'set', id: 'c2', value: 1 });
  assert.equal((await b.next((m) => m.t === 'error')).code, 'not-controller');

  b.send({ t: 'control', action: 'request' });
  assert.equal((await b.next((m) => m.t === 'role' && m.role === 'controller')).role, 'controller');
  assert.equal((await a.next((m) => m.t === 'role' && m.role === 'viewer')).role, 'viewer');

  b.send({ t: 'set', id: 'c2', value: 99 });
  const v = await a.next((m) => m.t === 'value');
  assert.deepEqual(v, { t: 'value', id: 'c2', value: 10 }, 'value is clamped and broadcast to all sessions');

  b.send({ t: 'set', id: 'c6', value: 1 });
  assert.equal((await b.next((m) => m.t === 'error')).code, 'rejected', 'indicators are not writable');

  a.ws.close();
  b.ws.close();
});

test('ping is answered with the same timestamp', async () => {
  const c = await hello();
  c.send({ t: 'ping', ts: 1234.5 });
  assert.equal((await c.next((m) => m.t === 'pong')).ts, 1234.5);
  c.ws.close();
});
