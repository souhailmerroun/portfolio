// Persistent CDP daemon for the mcp-browser pw_* tools.
//
// Legacy model: every pw_* call spawned a fresh `node -e` that did
// chromium.connectOverCDP(...) + browser.close() — paying a full CDP handshake
// and tab enumeration per call. This daemon holds ONE connectOverCDP session
// per cdp_url and reuses it across calls, so the per-call cost drops to just
// running the action body.
//
// Contract: POST /run { cdp_url, body, timeout_ms }
//   `body` is the per-call JS that the tools used to run inside their IIFE — it
//   has `browser`, `console`, `chromium`, `require` in scope (same as the old
//   IIFE), uses console.log(JSON.stringify(...)) for output and `return;` for
//   early exit. Response: { ok, lines: [...] } — the captured console.log lines.
// GET /health -> "ok".
//
// Self-exits after idle so it never leaks. If the port is taken, another daemon
// is already running and this one exits quietly.

const http = require('http');
const path = require('path');
const { createRequire } = require('module');

// A file run as `node cdp_daemon.js` resolves require() from THIS file's dir,
// which has no node_modules. The pw_* deps (playwright) live in the runtime
// dir, so resolve from there explicitly. MCP_CDP_RUNTIME is set by _cdp.py.
const RUNTIME = process.env.MCP_CDP_RUNTIME || process.cwd();
const rt = createRequire(path.join(RUNTIME, 'index.js'));
const { chromium } = rt('playwright');

const PORT = parseInt(process.env.MCP_CDP_DAEMON_PORT || '9224', 10);
const IDLE_MS = 10 * 60 * 1000; // exit after 10 min with no requests

const browsers = new Map(); // cdp_url -> Browser
let lastUsed = Date.now();

async function getBrowser(cdpUrl) {
  let b = browsers.get(cdpUrl);
  if (b && b.isConnected()) return b;
  if (b) { try { await b.close(); } catch (e) {} browsers.delete(cdpUrl); }
  b = await chromium.connectOverCDP(cdpUrl);
  b.on('disconnected', () => { if (browsers.get(cdpUrl) === b) browsers.delete(cdpUrl); });
  browsers.set(cdpUrl, b);
  return b;
}

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

async function runBody(cdpUrl, body, timeoutMs) {
  const browser = await getBrowser(cdpUrl);
  const lines = [];
  const fakeConsole = {
    log: (...a) => lines.push(a.map(x => (typeof x === 'string' ? x : JSON.stringify(x))).join(' ')),
    error: (...a) => lines.push(a.map(x => (typeof x === 'string' ? x : JSON.stringify(x))).join(' ')),
  };
  // Same closure scope the legacy IIFE had: browser, console, chromium, require.
  const fn = new AsyncFunction('browser', 'console', 'chromium', 'require', body);
  let timer;
  const guard = new Promise((_, rej) => {
    timer = setTimeout(() => rej(new Error('daemon body timeout')), timeoutMs || 30000);
  });
  try {
    await Promise.race([fn(browser, fakeConsole, chromium, rt), guard]);
  } finally {
    clearTimeout(timer);
  }
  return lines;
}

const server = http.createServer((req, res) => {
  if (req.url === '/health') { res.writeHead(200); res.end('ok'); return; }
  if (req.url === '/run' && req.method === 'POST') {
    let data = '';
    req.on('data', c => { data += c; });
    req.on('end', async () => {
      lastUsed = Date.now();
      let payload;
      try { payload = JSON.parse(data); }
      catch (e) { res.writeHead(400); res.end(JSON.stringify({ ok: false, error: 'bad json' })); return; }
      const cdpUrl = payload.cdp_url || 'http://localhost:9222';
      try {
        const lines = await runBody(cdpUrl, payload.body, payload.timeout_ms);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, lines }));
      } catch (e) {
        // Surface as a normal status:error line so the tool behaves as before.
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, lines: [JSON.stringify({ status: 'error', error: e.message })] }));
      }
    });
    return;
  }
  res.writeHead(404); res.end('not found');
});

server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') process.exit(0); // another daemon already up
  process.exit(1);
});

server.listen(PORT, '127.0.0.1', () => {});

setInterval(async () => {
  if (Date.now() - lastUsed > IDLE_MS) {
    for (const b of browsers.values()) { try { await b.close(); } catch (e) {} }
    process.exit(0);
  }
}, 60 * 1000);
