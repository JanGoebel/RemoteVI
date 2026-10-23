import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync(new URL('../../web/index.html', import.meta.url));

test('web client is pure ASCII, so the G string constant holds exactly these bytes', () => {
  const offending = [...html.entries()].filter(([, b]) => b > 0x7f).map(([i]) => i);
  assert.deepEqual(offending, [], 'use \\u escapes in JS and HTML entities in markup');
});

test('web client is self-contained: no external scripts, styles or images', () => {
  const text = html.toString('latin1');
  assert.doesNotMatch(text, /<script[^>]+src=/i);
  assert.doesNotMatch(text, /<link[^>]+rel=["']?stylesheet/i);
  assert.doesNotMatch(text, /<img\b/i);
});
