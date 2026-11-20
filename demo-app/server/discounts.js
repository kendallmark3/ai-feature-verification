// Discount rules for the demo shop.
// The catalog is static so tests are deterministic.

export const CART = {
  currency: 'USD',
  items: [
    { sku: 'SHOE-TRAIL-01', name: 'Trail Running Shoes', price: 89.0, qty: 1 },
    { sku: 'SOCK-RUN-03', name: 'Running Socks', price: 12.0, qty: 2 },
    { sku: 'BOTL-STEEL-07', name: 'Steel Water Bottle', price: 7.0, qty: 1 },
  ],
};

export const CODES = {
  SAVE10: { type: 'percent', value: 10, expires: '2027-12-31' },
  FLAT20: { type: 'fixed', value: 20, minSubtotal: 50, expires: '2027-12-31' },
  WELCOME5: { type: 'percent', value: 5, expires: '2025-06-30' },
};

const round2 = (n) => Math.round(n * 100) / 100;

export function subtotal(cart = CART) {
  return round2(cart.items.reduce((sum, i) => sum + i.price * i.qty, 0));
}

export function applyDiscount(code, cartSubtotal) {
  const raw = (code ?? '').trim();
  if (!raw) return { ok: false, error: 'Enter a discount code.' };

  const def = CODES[raw];
  if (!def) return { ok: false, error: 'That code is not valid.' };

  if (def.minSubtotal && cartSubtotal < def.minSubtotal) {
    return { ok: false, error: `This code needs a subtotal of at least $${def.minSubtotal}.` };
  }

  const discount =
    def.type === 'percent'
      ? round2((cartSubtotal * def.value) / 100)
      : Math.min(def.value, cartSubtotal);

  return { ok: true, code: raw, discount, total: round2(cartSubtotal - discount) };
}
