import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

import { findHeadEnd, parseRequestHead, isWebSocketUpgrade, buildResponseHead, HttpError, LIMITS } from '../../tools/lib/http.mjs';
import { acceptKey, decodeClientFrame, encodeServerFrame, WsError, MAX_CLIENT_PAYLOAD } from '../../tools/lib/websocket.mjs';
import { buildVectors, serialize } from '../../tools/gen-vectors.mjs';

const vectors = (name) => JSON.parse(fs.readFileSync(new URL(`../vectors/${name}`, import.meta.url)));
const fromHex = (h) => Buffer.from(h, 'hex');

test('committed vectors are up to date with the generator', () => {
  for (const [name, data] of Object.entries(buildVectors())) {
    const committed = fs.readFileSync(new URL(`../vectors/${name}`, import.meta.url), 'utf8');
    assert.equal(committed, serialize(data), `tests/vectors/${name} is stale - run npm run vectors`);
  }
});

test('HTTP vectors parse or fail with the expected status', () => {
  for (const c of vectors('http.json').cases) {
    if (c.status) {
      assert.throws(() => parseRequestHead(c.head), (e) => e instanceof HttpError && e.status === c.status, c.name);
    } else {
      const req = parseRequestHead(c.head);
      assert.equal(req.path, c.path, c.name);
      assert.equal(isWebSocketUpgrade(req), c.upgrade, c.name);
    }
  }
});

test('HTTP head boundary detection and size limit', () => {
  assert.equal(findHeadEnd('GET / HTTP/1.1\r\nHost: x\r\n'), -1);
  assert.equal(findHeadEnd('GET / HTTP/1.1\r\n\r\nBODY'), 18);
  assert.throws(() => findHeadEnd('x'.repeat(LIMITS.maxHeadBytes)), (e) => e.status === 431);
  assert.throws(() => findHeadEnd('x'.repeat(LIMITS.maxHeadBytes) + '\r\n\r\n'), (e) => e.status === 431);
});

test('HTTP header names are case-insensitive and query strings decode', () => {
  const req = parseRequestHead('GET /a?x=1&y=hello%20w&flag HTTP/1.1\r\nHOST: h\r\nX-Thing:  v  \r\n\r\n');
  assert.equal(req.headers.host, 'h');
  assert.equal(req.headers['x-thing'], 'v');
  assert.deepEqual({ ...req.query }, { x: '1', y: 'hello w', flag: '' });
  assert.throws(() => parseRequestHead('GET /a?x=%zz HTTP/1.1\r\n\r\n'), (e) => e.status === 400);
});

test('HTTP responses close the connection except for 101', () => {
  assert.match(buildResponseHead(404), /^HTTP\/1\.1 404 Not Found\r\nConnection: close\r\n\r\n$/);
  assert.doesNotMatch(buildResponseHead(101, { Upgrade: 'websocket' }), /close/);
});

test('WebSocket accept key matches RFC 6455', () => {
  for (const c of vectors('websocket.json').accept) assert.equal(acceptKey(c.key), c.accept);
});

test('WebSocket client frames decode or are rejected with the right close code', () => {
  for (const c of vectors('websocket.json').clientFrames) {
    if (c.error) {
      assert.throws(() => decodeClientFrame(fromHex(c.frame)), (e) => e instanceof WsError && e.code === c.error, c.name);
    } else {
      const f = decodeClientFrame(fromHex(c.frame));
      assert.equal(f.fin, c.fin, c.name);
      assert.equal(f.opcode, c.opcode, c.name);
      assert.equal(f.payload.toString('hex'), c.payload, c.name);
      assert.equal(f.size, c.frame.length / 2, c.name);
    }
  }
});

test('WebSocket decoder waits for more data on every incomplete prefix', () => {
  for (const h of vectors('websocket.json').incompleteClientFrames) assert.equal(decodeClientFrame(fromHex(h)), null, h);
});

test('WebSocket decoder enforces the client payload limit', () => {
  const len = MAX_CLIENT_PAYLOAD + 1;
  const head = Buffer.from([0x81, 0xff, 0, 0, 0, 0, len >>> 24, (len >>> 16) & 0xff, (len >>> 8) & 0xff, len & 0xff]);
  assert.throws(() => decodeClientFrame(head), (e) => e.code === 1009);
});

test('WebSocket server frames match RFC 6455 examples', () => {
  for (const c of vectors('websocket.json').serverFrames) {
    if (c.frame) {
      assert.equal(encodeServerFrame(c.opcode, fromHex(c.payload)).toString('hex'), c.frame, c.name);
    } else {
      const out = encodeServerFrame(c.opcode, Buffer.alloc(c.payloadLength));
      assert.equal(out.subarray(0, c.header.length / 2).toString('hex'), c.header, c.name);
      assert.equal(out.length, c.header.length / 2 + c.payloadLength);
    }
  }
});

