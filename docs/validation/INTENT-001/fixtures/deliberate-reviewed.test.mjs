// DELIBERATE FAILURE · INTENT-001 validation fixture, not a real requirement.
// A reviewed file: it carries no Gate 2 marker. It asserts a total the product owner never
// agreed to, so we can prove a failure is detected, classified and reported.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { applyDiscount } from '../../server/discounts.js';

test('SHOP-142 AC-2 DELIBERATE SAVE10 on the $120 cart totals 100', () => {
  const r = applyDiscount('SAVE10', 120);
  assert.strictEqual(r.total, 100);
});
