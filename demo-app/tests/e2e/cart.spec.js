import { test, expect } from '@playwright/test';

test('cart page lists items and shows the subtotal', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Your cart' })).toBeVisible();
  await expect(page.getByRole('list', { name: 'Cart items' }).getByRole('listitem')).toHaveCount(3);
  await expect(page.getByTestId('subtotal')).toHaveText('$120.00');
});
