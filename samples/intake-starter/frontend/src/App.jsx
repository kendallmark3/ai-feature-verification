import { useState } from 'react';

const TYPES = [
  ['ECOMMERCE', 'E-commerce'],
  ['WEBSITE', 'Website'],
  ['API', 'API'],
];

export default function App() {
  const [form, setForm] = useState({ clientName: '', projectType: 'ECOMMERCE', description: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    const res = await fetch('/api/intakes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const body = await res.json();
    if (res.ok) setResult(body);
    else setError(body.error || 'Something went wrong');
  }

  return (
    <main style={{ maxWidth: 560, margin: '2rem auto', fontFamily: 'system-ui, sans-serif', padding: '0 16px' }}>
      <h1>Tell us what you want built</h1>
      <form onSubmit={submit}>
        <label>
          Your name
          <input value={form.clientName} onChange={set('clientName')} />
        </label>
        <label>
          Project type
          <select value={form.projectType} onChange={set('projectType')}>
            {TYPES.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
        </label>
        <label>
          What do you want?
          <textarea rows={5} value={form.description} onChange={set('description')} />
        </label>
        <button type="submit">Send intake</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {result && <p role="status">Thanks. Your reference is <strong>{result.reference}</strong>.</p>}
      <style>{'label{display:block;margin:12px 0}input,select,textarea{display:block;width:100%;font:inherit}'}</style>
    </main>
  );
}
