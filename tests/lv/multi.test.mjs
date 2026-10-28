// Several shares in one LabVIEW application instance (the Server Loop is reentrant, one clone per port).
//
//   1. run tests/fixtures/RemoteVI Fixture.vi (port 8089) and examples/RemoteVI Demo.vi (port 8088) in the
//      same LabVIEW
//   2. RVI_LV_MULTI=1 RVI_URL=<fixture link with ?t=> RVI_URL2=<demo link with ?t=> node --test tests/lv/multi.test.mjs
//
// The links come from each VI's URL indicator or from RemoteVI Status.vi (tools/lv-share-url.ps1 -Port N).

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { connect, layout, readLog, waitLog, click, sleep } from './harness.mjs';

const enabled = process.env.RVI_LV_MULTI === '1';
const opts = { skip: !enabled && 'set RVI_LV_MULTI=1 and run the fixture (8089) and the demo (8088) in one LabVIEW' };

function demoUrl() {
  if (process.env.RVI_URL2) return new URL(process.env.RVI_URL2);
  const script = fileURLToPath(new URL('../../tools/lv-share-url.ps1', import.meta.url));
  return new URL(execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script, '-Port', '8088'],
    { encoding: 'utf8', timeout: 30000 }).trim().split(/\r?\n/).at(-1));
}

/** A plain client of the second share: acks every frame, keeps the title and counts frames. */
function connectDemo(u) {
  const ws = new WebSocket(`ws://${u.host}/ws?t=${u.searchParams.get('t')}`);
  ws.binaryType = 'arraybuffer';
  const d = { ws, title: null, frames: 0 };
  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') {
      if (ev.data.startsWith('title ')) d.title = ev.data.slice(6);
      return;
    }
    const v = new DataView(ev.data);
    if (v.getUint8(1) === 1) { d.frames++; ws.send(`a ${v.getUint32(2)}`); }
    if (v.getUint8(1) === 3) ws.send(`a ${v.getUint32(6)}`);
  };
  return new Promise((resolve, reject) => { ws.onopen = () => resolve(d); ws.onerror = () => reject(new Error(`cannot connect to ${u}`)); });
}

let c, d;
before(async () => {
  if (!enabled) return;
  await waitLog(([k]) => k === 'ready', { ms: 10000 });
  c = await connect();
  d = await connectDemo(demoUrl());
  await sleep(1500);
});
after(() => { c?.ws.close(); d?.ws.close(); });

test('two shares of one LabVIEW stream at the same time, each its own VI', opts, async () => {
  const f0 = c.frames, d0 = d.frames;
  await sleep(2000);
  assert.equal(d.title, 'RemoteVI Demo.vi');
  assert.ok(d.frames > d0, `demo frames ${d0} -> ${d.frames}`);
  // the fixture is static: a click makes it send a frame
  const r = layout(c).get('Switch');
  const s = readLog().length;
  await click(c, r.cx, r.cy);
  await waitLog(([k, l]) => k === 'value' && l === 'Switch', { since: s });
  await sleep(500);
  assert.ok(c.frames > f0, `fixture frames ${f0} -> ${c.frames}`);
});

test('input reaches the right VI while the other share is busy streaming', opts, async () => {
  const r = layout(c).get('Switch');
  for (let i = 0; i < 3; i++) {
    const s = readLog().length;
    await click(c, r.cx, r.cy);
    await waitLog(([k, l]) => k === 'value' && l === 'Switch', { since: s });
  }
});

test('a wrong token for one share is refused, the other share is unaffected', opts, async () => {
  const u = demoUrl();
  const bad = new WebSocket(`ws://${u.host}/ws?t=${u.searchParams.get('t')}0`);
  const opened = await new Promise((r) => { bad.onopen = () => r(true); bad.onerror = () => r(false); setTimeout(() => r(false), 3000); });
  assert.equal(opened, false);
  const n = d.frames;
  await sleep(1000);
  assert.ok(d.frames > n, 'the demo client keeps streaming');
});
