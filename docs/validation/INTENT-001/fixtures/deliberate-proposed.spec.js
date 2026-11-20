// @ai-proposed SHOP-142 — DELIBERATE FAILURE · INTENT-001 validation fixture, not a real requirement.
// Expects an error text the product never shows, so we can prove an unreviewed failing test
// is run interactively, labelled, reported as a suspected defect, and withheld in pipeline mode.
import { test, expect } from '@playwright/test';

test('SHOP-142 AC-3 DELIBERATE an unknown code shows "Code rejected."', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Discount code').fill('NOPE');
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByRole('alert')).toHaveText('Code rejected.', { timeout: 3000 });
});
