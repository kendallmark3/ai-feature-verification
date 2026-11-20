import { useEffect, useState } from 'react';

const money = (n) => `$${Number(n).toFixed(2)}`;

export default function App() {
  const [cart, setCart] = useState(null);
  const [code, setCode] = useState('');
  const [applied, setApplied] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/cart').then((r) => r.json()).then(setCart);
  }, []);

  async function onApply(e) {
    e.preventDefault();
    setError('');
    const res = await fetch('/api/cart/discount', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    const body = await res.json();
    if (!res.ok) {
      setApplied(null);
      setError(body.error);
      return;
    }
    setApplied(body);
  }

  if (!cart) return <main className="page"><p>Loading cart…</p></main>;

  const total = applied ? applied.total : cart.subtotal;

  return (
    <main className="page">
      <h1>Your cart</h1>
      <ul className="items" aria-label="Cart items">
        {cart.items.map((i) => (
          <li key={i.sku}>
            <span>{i.name} × {i.qty}</span>
            <span>{money(i.price * i.qty)}</span>
          </li>
        ))}
      </ul>

      <form className="discount" onSubmit={onApply}>
        <label htmlFor="discount-code">Discount code</label>
        <div className="row">
          <input id="discount-code" value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" />
          <button type="submit">Apply</button>
        </div>
        {error && <p role="alert" className="error">{error}</p>}
      </form>

      <dl className="totals">
        <div><dt>Subtotal</dt><dd data-testid="subtotal">{money(cart.subtotal)}</dd></div>
        {applied && (
          <div><dt>Discount ({applied.code})</dt><dd data-testid="discount">−{money(applied.discount)}</dd></div>
        )}
        <div className="grand"><dt>Total</dt><dd data-testid="total">{money(total)}</dd></div>
      </dl>
    </main>
  );
}
