// End-to-end tests against the reference server (protocol v2) over real sockets.
// They describe what the LabVIEW server loop must do; the same scenarios are the
// manual acceptance test for the G implementation (docs/testing.md).
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import { inflateSync } from 'node:zlib';

import { startServer } from '../../tools/mock-server/server.mjs';
import { FRAME_MAGIC, MSG_FRAME, MSG_OVERLAY, MSG_WINDOW_FRAME, FRAMES_IN_FLIGHT } from '../../tools/lib/protocol.mjs';

let srv;
before(async () => {
  srv = await startServer({ port: 0, fps: 60, log: () => {} });
});
after(() => srv.close());

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
  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') return push({ text: ev.data });
    const type = new Uint8Array(ev.data)[1];
    if (type === MSG_OVERLAY) return push({ overlay: decodeOverlay(ev.data) });
    if (type === MSG_WINDOW_FRAME) return push({ windowFrame: decodeWindowFrame(ev.data) });
    return push({ frame: decodeFrame(ev.data) });
  };
  ws.onclose = (ev) => push({ closed: ev.code });
  return {
    ws,
    opened: new Promise((r) => { ws.onopen = r; }),
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

function decodeFrame(buf) {
  const b = Buffer.from(buf);
  assert.equal(b[0], FRAME_MAGIC);
  assert.equal(b[1], MSG_FRAME);
  const frame = { seq: b.readUInt32BE(2), width: b.readUInt16BE(6), height: b.readUInt16BE(8), rects: [] };
  let o = 12;
  for (let i = 0, n = b.readUInt16BE(10); i < n; i++) {
    const len = b.readUInt32BE(o + 4);
    frame.rects.push({ x: b.readInt16BE(o), y: b.readInt16BE(o + 2), ...decodePng(b.subarray(o + 8, o + 8 + len)) });
    o += 8 + len;
  }
  assert.equal(o, b.length, 'no trailing bytes');
  return frame;
}

function decodeOverlay(buf) {
  const b = Buffer.from(buf);
  const popups = [];
  let o = 4;
  for (let i = 0, n = b.readUInt16BE(2); i < n; i++) {
    const len = b.readUInt32BE(o + 4);
    popups.push({ x: b.readInt16BE(o), y: b.readInt16BE(o + 2), ...decodePng(b.subarray(o + 8, o + 8 + len)) });
    o += 8 + len;
  }
  assert.equal(o, b.length, 'no trailing bytes');
  return popups;
}

function decodeWindowFrame(buf) {
  const b = Buffer.from(buf);
  const f = { id: b.readUInt32BE(2), seq: b.readUInt32BE(6), width: b.readUInt16BE(10), height: b.readUInt16BE(12), rects: [] };
  let o = 16;
  for (let i = 0, n = b.readUInt16BE(14); i < n; i++) {
    const len = b.readUInt32BE(o + 4);
    f.rects.push({ x: b.readInt16BE(o), y: b.readInt16BE(o + 2), ...decodePng(b.subarray(o + 8, o + 8 + len)) });
    o += 8 + len;
  }
  assert.equal(o, b.length, 'no trailing bytes');
  return f;
}

/** Decoder for the truecolour, filter-0 PNGs the reference encoder writes. */
function decodePng(png) {
  assert.equal(png.subarray(1, 4).toString('latin1'), 'PNG');
  let o = 8, w = 0, h = 0;
  const idat = [];
  while (o < png.length) {
    const len = png.readUInt32BE(o);
    const type = png.subarray(o + 4, o + 8).toString('latin1');
    const data = png.subarray(o + 8, o + 8 + len);
    if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); }
    if (type === 'IDAT') idat.push(data);
    o += 12 + len;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const px = new Uint32Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * (1 + w * 3) + 1 + x * 3;
      px[y * w + x] = (raw[i] << 16) | (raw[i + 1] << 8) | raw[i + 2];
    }
  }
  return { w, h, px };
}

function paint(img, width, frame) {
  for (const r of frame.rects) {
    for (let y = 0; y < r.h; y++) img.set(r.px.subarray(y * r.w, (y + 1) * r.w), (r.y + y) * width + r.x);
  }
}

test('GET / serves the one-file client with security headers; everything else is refused', async () => {
  const res = await rawRequest('GET / HTTP/1.1\r\nHost: x\r\n\r\n');
  assert.match(res, /^HTTP\/1\.1 200 OK\r\n/);
  assert.match(res, /X-Content-Type-Options: nosniff/);
  assert.match(res, /<canvas id="panel"/);
  assert.match(await rawRequest('GET /js/client.js HTTP/1.1\r\nHost: x\r\n\r\n'), /^HTTP\/1\.1 404 /);
  assert.match(await rawRequest('GET /../package.json HTTP/1.1\r\nHost: x\r\n\r\n'), /^HTTP\/1\.1 404 /);
  assert.match(await rawRequest('POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n'), /^HTTP\/1\.1 405 /);
  assert.match(await rawRequest('GET /ws HTTP/1.1\r\nHost: x\r\n\r\n'), /^HTTP\/1\.1 426 /);
});

test('cross-origin WebSocket handshakes are refused', async () => {
  const res = await rawRequest(`GET /ws HTTP/1.1\r\nHost: 127.0.0.1:${srv.port}\r\nOrigin: http://evil.example\r\n`
    + 'Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n');
  assert.match(res, /^HTTP\/1\.1 403 /);
});

test('title is sent on connect; the first frame is the whole panel, pixel-exact', async () => {
  const c = connect();
  await c.opened;
  assert.equal((await c.next((m) => m.text?.startsWith('title '))).text, 'title Simulated Panel.vi');
  const { frame } = await c.next((m) => m.frame);
  assert.deepEqual(frame.rects.map(({ x, y, w, h }) => ({ x, y, w, h })), [{ x: 0, y: 0, w: frame.width, h: frame.height }]);
  const img = new Uint32Array(frame.width * frame.height);
  paint(img, frame.width, frame);
  // With the pump off the simulated panel is static, so a fresh render must equal what we rebuilt.
  assert.deepEqual(img, srv.panel.render().slice());
  c.ws.close();
});

test('input becomes Win32 messages; only dirty bands follow; acks pace the stream', async () => {
  const c = connect();
  await c.opened;
  const { frame: first } = await c.next((m) => m.frame);
  const img = new Uint32Array(first.width * first.height);
  paint(img, first.width, first);
  c.ws.send(`a ${first.seq}`);

  // Click "Pump On": the chart starts animating, so frames keep coming.
  srv.posted.length = 0;
  c.ws.send('m 513 30 50 1');
  c.ws.send('m 514 30 50 0');
  const { frame: second } = await c.next((m) => m.frame);
  assert.ok(second.rects.length > 0);
  assert.ok(second.rects.every((r) => r.w * r.h < first.width * first.height), 'only dirty bands are sent');
  assert.deepEqual(srv.posted.map((p) => p.msg), [0x201, 0x202]);
  paint(img, first.width, second);

  // Without acks the server stops after FRAMES_IN_FLIGHT unacknowledged frames.
  const inFlight = [second];
  for (let i = 1; i < FRAMES_IN_FLIGHT; i++) inFlight.push((await c.next((m) => m.frame)).frame);
  await assert.rejects(c.next((m) => m.frame, 300), /timed out/);

  c.ws.send(`a ${inFlight.at(-1).seq}`);
  const { frame: next } = await c.next((m) => m.frame);
  assert.equal(next.seq, inFlight.at(-1).seq + 1);

  c.ws.send('m 513 30 50 1'); // pump off again for other tests
  c.ws.send('m 514 30 50 0');
  c.ws.close();
});

test('keyboard and wheel messages reach the panel; malformed and disallowed ones are ignored', async () => {
  const c = connect();
  await c.opened;
  await c.next((m) => m.frame);
  srv.posted.length = 0;
  c.ws.send('m 513 50 270 1');       // focus Operator
  c.ws.send('k 258 120 1');          // WM_CHAR 'x'
  c.ws.send('m 522 40 110 7864320'); // WM_MOUSEWHEEL +120 over Setpoint
  c.ws.send('m 16 1 1 0');           // WM_CLOSE: not on the allow list
  c.ws.send('m 513 1 2');            // malformed
  c.ws.send('hello');                // malformed
  c.ws.send('a 1');
  await new Promise((r) => setTimeout(r, 100));
  assert.deepEqual(srv.posted.map((p) => p.msg), [0x201, 0x100, 0x102, 0x101, 0x20a]);
  assert.ok(srv.panel.state.operator.endsWith('X'));
  assert.equal(srv.panel.state.setpoint, 2.6);
  c.ws.close();
});

test('popups travel as OVERLAY messages, may overflow the panel, and close on a click', async () => {
  const c = connect();
  await c.opened;
  const { frame } = await c.next((m) => m.frame);
  c.ws.send(`a ${frame.seq}`);
  const before = srv.panel.state.mode;
  c.ws.send('m 516 480 280 2');      // right-click near the bottom-right corner
  c.ws.send('m 517 480 280 0');
  const { overlay } = await c.next((m) => m.overlay);
  assert.equal(overlay.length, 1);
  const [p] = overlay;
  assert.deepEqual([p.x, p.y], [480, 280]);
  assert.ok(p.x + p.w > frame.width && p.y + p.h > frame.height, 'the popup extends past the panel');
  const target = (before + 1) % 3;
  c.ws.send(`m 513 ${p.x + 10} ${p.y + 4 + target * 16} 1`);   // click an item outside the panel area
  c.ws.send(`m 514 ${p.x + 10} ${p.y + 4 + target * 16} 0`);
  const cleared = await c.next((m) => m.overlay);
  assert.deepEqual(cleared.overlay, []);
  assert.equal(srv.panel.state.mode, target);
  c.ws.close();
});

test('a modal dialog arrives as a window with its own frames; it is operated and closed remotely', async () => {
  const c = connect();
  await c.opened;
  const { frame } = await c.next((m) => m.frame);
  c.ws.send(`a ${frame.seq}`);
  assert.equal((await c.next((m) => m.text?.startsWith('windows '))).text, 'windows []');

  c.ws.send('m 513 300 225 1'); // click the Status indicator: opens "Proceed?"
  c.ws.send('m 514 300 225 0');
  const list = JSON.parse((await c.next((m) => m.text?.startsWith('windows [{'))).text.slice(8));
  assert.equal(list.length, 1);
  const [w] = list;
  assert.deepEqual([w.title, w.modal, w.active, w.closable], ['Proceed?', true, true, true]);
  const { windowFrame } = await c.next((m) => m.windowFrame);
  assert.deepEqual([windowFrame.id, windowFrame.width, windowFrame.height], [w.id, w.w, w.h]);
  assert.equal(windowFrame.rects[0].w * windowFrame.rects[0].h, w.w * w.h, 'first window frame is complete');
  c.ws.send(`a ${windowFrame.seq}`);

  // The panel behind a modal dialog takes no input; the dialog does.
  c.ws.send('m 513 30 50 1');
  c.ws.send('m 514 30 50 0');
  c.ws.send(`m 513 ${w.x + 40} ${w.y + 60} 1`); // "YES"
  c.ws.send(`m 514 ${w.x + 40} ${w.y + 60} 0`);
  assert.equal((await c.next((m) => m.text?.startsWith('windows '))).text, 'windows []');
  assert.equal(srv.panel.answer, 'YES');
  assert.equal(srv.panel.state.pump, false, 'the click on the disabled panel did nothing');

  // x <id> closes a window like its close box.
  c.ws.send('m 513 300 225 1');
  c.ws.send('m 514 300 225 0');
  const [again] = JSON.parse((await c.next((m) => m.text?.startsWith('windows [{'))).text.slice(8));
  c.ws.send(`x ${again.id}`);
  assert.equal((await c.next((m) => m.text?.startsWith('windows '))).text, 'windows []');
  assert.equal(srv.panel.answer, 'CLOSED');
  srv.panel.answer = '';
  c.ws.close();
});
