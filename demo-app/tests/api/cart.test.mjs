import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../../server/server.js';

let server, base;
before(async () => {
  server = createServer().listen(0, '127.0.0.1');
  await new Promise((r) => server.once('listening', r));
  base = `http://127.0.0.1:${server.address().port}`;
});
after(() => server.close());

test('GET /api/cart returns the items and subtotal', async () => {
  const res = await fetch(`${base}/api/cart`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.items.length, 3);
  assert.equal(body.subtotal, 120);
});

test('GET /api/health reports ok', async () => {
  const res = await fetch(`${base}/api/health`);
  assert.deepEqual(await res.json(), { status: 'ok' });
});
