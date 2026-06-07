// index.ts — LAON VaultGuard entry point

import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config, validateConfig } from './config.js';
import { apiRouter } from './routes/api.js';
import { startScheduler } from './scheduler.js';
import { addSseClient } from './sse.js';
import { logAudit } from './db.js';

const app = express();
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Validate config ──
const errors = validateConfig();
if (errors.length > 0) {
  console.warn('[config] Warnings:');
  errors.forEach(e => console.warn(`  - ${e}`));
}

// ── Middleware ──
app.use(express.json());

// CORS for same-network dashboard access
app.use((_req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

// ── Dashboard Auth (optional token) ──
const DASHBOARD_TOKEN = process.env.DASHBOARD_TOKEN || '';
if (DASHBOARD_TOKEN) {
  app.use((req, res, next) => {
    // public endpoints: status, dashboard page, events, static files
    if (req.method === 'GET' && (req.path === '/api/status' || req.path === '/dashboard' || req.path === '/api/events' || req.path.startsWith('/public'))) {
      return next();
    }
    const auth = req.headers.authorization;
    if (!auth || auth !== `Bearer ${DASHBOARD_TOKEN}`) {
      return res.status(401).json({ error: 'Unauthorized. Use Authorization: Bearer <token>' });
    }
    next();
  });
}

// ── Static files ──
app.use(express.static(path.join(__dirname, '../public')));

// ── SSE endpoint ──
app.get('/api/events', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  res.write(`data: ${JSON.stringify({ type: 'connected', data: { timestamp: new Date().toISOString() } })}\n\n`);
  addSseClient(res);
  req.on('close', () => {
    res.end();
  });
});

// ── API routes ──
app.use(apiRouter);

// ── Start ──
const PORT = config.port;
const HOST = config.host;

app.listen(PORT, HOST, () => {
  const banner = `
╔══════════════════════════════════════════╗
║       🛡 LAON VaultGuard v0.5.0         ║
║  LLM-based Observer for Non-public Keys  ║
╠══════════════════════════════════════════╣
║  Server:  http://${HOST}:${PORT}
║  Dashboard: http://${HOST}:${PORT}/dashboard
║  Platform: ${process.platform}
╚══════════════════════════════════════════╝`;
  console.log(banner);

  logAudit('server_started', 'info', `Server started on ${HOST}:${PORT}`);

  // Start cron scheduler
  if (config.scan.cron) {
    startScheduler();
  }
});

// ── Graceful shutdown ──
process.on('SIGTERM', () => {
  logAudit('server_shutdown', 'info', 'Server shutting down (SIGTERM)');
  process.exit(0);
});

process.on('SIGINT', () => {
  logAudit('server_shutdown', 'info', 'Server shutting down (SIGINT)');
  process.exit(0);
});
