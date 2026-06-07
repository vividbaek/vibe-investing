// routes/api.ts — REST API endpoints

import { Router } from 'express';
import { randomUUID } from 'node:crypto';
import {
  listRepos, addRepo, removeRepo,
  listFindings, getFinding, acknowledgeFinding,
  countOpenFindings, getLatestScan, getScanCount,
} from '../db.js';
import { scanAllRepos } from '../scheduler.js';
import { sseClientCount, emitSse } from '../sse.js';

export const apiRouter = Router();

// ── Status ──

apiRouter.get('/api/status', (_req, res) => {
  const latest = getLatestScan();
  res.json({
    open_findings: countOpenFindings(),
    last_scan: latest?.completedAt || null,
    total_scans: getScanCount(),
    registered_repos: listRepos().length,
    sse_clients: sseClientCount(),
    uptime: process.uptime(),
  });
});

apiRouter.get('/api/health', (_req, res) => {
  res.json({
    status: 'ok',
    uptime: Math.floor(process.uptime()),
    version: '0.1.0',
    platform: process.platform,
  });
});

// ── Repos ──

apiRouter.get('/api/repos', (_req, res) => {
  const repos = listRepos();
  const result = repos.map(r => {
    const findings = listFindings({ repoId: r.id });
    return {
      ...r,
      findings_total: findings.total,
      findings_open: findings.findings.filter(f => !f.acknowledged).length,
    };
  });
  res.json({ repos: result });
});

apiRouter.post('/api/repos', (req, res) => {
  const { name, type, pathOrUrl, branch } = req.body;
  if (!name || !type || !pathOrUrl) {
    return res.status(400).json({ error: 'name, type, and pathOrUrl are required' });
  }
  const repo = addRepo({
    name,
    type,
    pathOrUrl,
    branch: branch || 'main',
    enabled: true,
    cronOverride: null,
  });
  res.status(201).json(repo);
});

apiRouter.delete('/api/repos/:id', (req, res) => {
  const ok = removeRepo(req.params.id);
  if (!ok) return res.status(404).json({ error: 'Repo not found' });
  res.json({ deleted: true });
});

// ── Scan ──

apiRouter.post('/api/scan/trigger', async (_req, res) => {
  res.json({ scan_id: randomUUID(), status: 'started' });
  // fire and forget
  scanAllRepos('manual').catch(err => {
    console.error('[api] Manual scan failed:', err);
  });
});

// ── Findings ──

apiRouter.get('/api/findings', (req, res) => {
  const { severity, acknowledged, repo_id, limit, offset, from, to } = req.query;
  const result = listFindings({
    severity: severity as string | undefined,
    acknowledged: acknowledged !== undefined ? acknowledged === 'true' : undefined,
    repoId: repo_id as string | undefined,
    limit: limit ? parseInt(limit as string, 10) : undefined,
    offset: offset ? parseInt(offset as string, 10) : undefined,
  });
  // date range filter
  let filtered = result.findings;
  if (from) {
    const fromDate = new Date(from as string).toISOString();
    filtered = filtered.filter(f => f.detectedAt >= fromDate);
  }
  if (to) {
    const toDate = new Date(to as string).toISOString();
    filtered = filtered.filter(f => f.detectedAt <= toDate);
  }
  // attach repo name
  const repos = listRepos();
  const withRepoName = filtered.map(f => ({
    ...f,
    repo_name: repos.find(r => r.id === f.repoId)?.name || 'unknown',
  }));
  res.json({ total: withRepoName.length, findings: withRepoName });
});

apiRouter.get('/api/findings/:id', (req, res) => {
  const f = getFinding(req.params.id);
  if (!f) return res.status(404).json({ error: 'Finding not found' });
  const repo = listRepos().find(r => r.id === f.repoId);
  res.json({ ...f, repo_name: repo?.name || 'unknown' });
});

apiRouter.put('/api/findings/:id/acknowledge', (req, res) => {
  const { note } = req.body;
  const f = acknowledgeFinding(req.params.id, note);
  if (!f) return res.status(404).json({ error: 'Finding not found' });
  emitSse('finding:acknowledged', { id: f.id });
  res.json(f);
});

// ── Bulk acknowledge ──
apiRouter.put('/api/findings/acknowledge/bulk', (req, res) => {
  const { ids, note } = req.body;
  if (!ids || !Array.isArray(ids)) {
    return res.status(400).json({ error: 'ids array required' });
  }
  let count = 0;
  for (const id of ids) {
    const f = acknowledgeFinding(id, note || 'Bulk acknowledged');
    if (f) {
      count++;
      emitSse('finding:acknowledged', { id: f.id });
    }
  }
  res.json({ acknowledged: count });
});

// ── Dashboard ──

import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.resolve(__dirname, '../../public');

apiRouter.get('/dashboard', (_req, res) => {
  res.sendFile(path.join(publicDir, 'index.html'));
});
