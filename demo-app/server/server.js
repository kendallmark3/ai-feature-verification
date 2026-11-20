// Minimal Node.js backend for the demo shop. No dependencies.
// Serves the JSON API and the built React app (web/dist).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CART, subtotal, applyDiscount } from './discounts.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.resolve(here, '../web/dist');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' };

function json(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (c) => (data += c));
    req.on('end', () => {
      try { resolve(data ? JSON.parse(data) : {}); } catch { resolve(null); }
    });
  });
}

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let file = path.join(DIST, urlPath === '/' ? 'index.html' : urlPath);
  if (!file.startsWith(DIST) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    file = path.join(DIST, 'index.html');
  }
  if (!fs.existsSync(file)) {
    res.writeHead(503, { 'content-type': 'text/plain' });
    return res.end('Web app not built. Run: npm run build');
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}

export function createServer() {
  return http.createServer(async (req, res) => {
    const { pathname } = new URL(req.url, 'http://x');

    if (req.method === 'GET' && pathname === '/api/health') return json(res, 200, { status: 'ok' });

    if (req.method === 'GET' && pathname === '/api/cart') {
      return json(res, 200, { ...CART, subtotal: subtotal() });
    }

    if (req.method === 'POST' && pathname === '/api/cart/discount') {
      const body = await readBody(req);
      if (body === null) return json(res, 400, { error: 'Invalid JSON.' });
      const result = applyDiscount(body.code, subtotal());
      if (!result.ok) return json(res, 400, { error: result.error });
      const { ok, ...rest } = result;
      return json(res, 200, { subtotal: subtotal(), ...rest });
    }

    if (pathname.startsWith('/api/')) return json(res, 404, { error: 'Not found.' });
    return serveStatic(req, res);
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 4310);
  createServer().listen(port, '127.0.0.1', () => {
    console.log(`shop-demo listening on http://127.0.0.1:${port}`);
  });
}
