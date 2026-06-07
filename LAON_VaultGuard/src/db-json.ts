// db-json.ts — file-based JSON storage (legacy backend)
// Structure: data/repos.json, data/findings.json, data/logs/

import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import type { Repository, ScanRun, Finding } from './types.js';
import { config } from './config.js';

const DATA_DIR = path.resolve(config.db.path);
const DB_PATH = path.join(DATA_DIR, 'vaultguard.db');

export { DATA_DIR, DB_PATH };

function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

export function readJson<T>(filePath: string, fallback: T): T {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8')) as T;
    }
  } catch { /* corrupt file, return fallback */ }
  return fallback;
}

export function writeJson(filePath: string, data: unknown) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

// ── Repos ──

const REPOS_FILE = path.join(DATA_DIR, 'repos.json');

export function listRepos(): Repository[] {
  return readJson<Repository[]>(REPOS_FILE, []);
}

export function getRepo(id: string): Repository | undefined {
  return listRepos().find(r => r.id === id);
}

export function addRepo(input: Omit<Repository, 'id' | 'lastScan' | 'createdAt'>): Repository {
  const repos = listRepos();
  const repo: Repository = {
    ...input,
    id: randomUUID(),
    lastScan: null,
    createdAt: new Date().toISOString(),
  };
  repos.push(repo);
  writeJson(REPOS_FILE, repos);
  logAudit('repo_added', 'info', `Repo added: ${repo.name} (${repo.type})`, { repoId: repo.id });
  return repo;
}

export function removeRepo(id: string): boolean {
  const repos = listRepos();
  const idx = repos.findIndex(r => r.id === id);
  if (idx === -1) return false;
  const removed = repos.splice(idx, 1)[0];
  writeJson(REPOS_FILE, repos);
  logAudit('repo_removed', 'info', `Repo removed: ${removed.name}`, { repoId: id });
  return true;
}

export function updateRepoLastScan(id: string) {
  const repos = listRepos();
  const repo = repos.find(r => r.id === id);
  if (repo) {
    repo.lastScan = new Date().toISOString();
    writeJson(REPOS_FILE, repos);
  }
}

// ── Findings ──

const FINDINGS_FILE = path.join(DATA_DIR, 'findings.json');

export function listFindings(filter?: {
  severity?: string;
  acknowledged?: boolean;
  repoId?: string;
  limit?: number;
  offset?: number;
}): { total: number; findings: Finding[] } {
  const all = readJson<Finding[]>(FINDINGS_FILE, []);
  let filtered = all;

  if (filter?.severity) {
    filtered = filtered.filter(f => f.severity === filter.severity);
  }
  if (filter?.acknowledged !== undefined) {
    filtered = filtered.filter(f => f.acknowledged === filter.acknowledged);
  }
  if (filter?.repoId) {
    filtered = filtered.filter(f => f.repoId === filter.repoId);
  }

  filtered.sort((a, b) => new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime());
  const total = filtered.length;
  const offset = filter?.offset || 0;
  const limit = filter?.limit || 50;

  return { total, findings: filtered.slice(offset, offset + limit) };
}

export function getFinding(id: string): Finding | undefined {
  return readJson<Finding[]>(FINDINGS_FILE, []).find(f => f.id === id);
}

export function saveFindings(findings: Finding[]) {
  const existing = readJson<Finding[]>(FINDINGS_FILE, []);
  existing.push(...findings);
  writeJson(FINDINGS_FILE, existing);
}

export function acknowledgeFinding(id: string, note?: string): Finding | undefined {
  const all = readJson<Finding[]>(FINDINGS_FILE, []);
  const f = all.find(f => f.id === id);
  if (!f) return undefined;
  f.acknowledged = true;
  f.acknowledgedAt = new Date().toISOString();
  f.acknowledgedNote = note || null;
  writeJson(FINDINGS_FILE, all);
  logAudit('finding_acknowledged', 'info', `Finding acknowledged: ${f.id}`, { findingId: id });
  return f;
}

export function unacknowledgeFinding(id: string): Finding | undefined {
  const all = readJson<Finding[]>(FINDINGS_FILE, []);
  const f = all.find(f => f.id === id);
  if (!f) return undefined;
  f.acknowledged = false;
  f.acknowledgedAt = null;
  f.acknowledgedNote = null;
  writeJson(FINDINGS_FILE, all);
  logAudit('finding_unacknowledged', 'info', `Finding un-acknowledged: ${f.id}`, { findingId: id });
  return f;
}

export function addFindingComment(id: string, comment: string): Finding | undefined {
  const all = readJson<Finding[]>(FINDINGS_FILE, []);
  const f = all.find(f => f.id === id);
  if (!f) return undefined;
  f.acknowledgedNote = (f.acknowledgedNote ? f.acknowledgedNote + ' | ' : '') + comment;
  writeJson(FINDINGS_FILE, all);
  logAudit('finding_comment', 'info', `Comment added to finding: ${f.id}`, { findingId: id });
  return f;
}

export function countOpenFindings(): number {
  return readJson<Finding[]>(FINDINGS_FILE, []).filter(f => !f.acknowledged).length;
}

// ── Scan Runs ──

const SCANS_DIR = path.join(DATA_DIR, 'scans');

export function saveScanRun(run: ScanRun) {
  ensureDir(SCANS_DIR);
  const file = path.join(SCANS_DIR, `${run.id}.json`);
  writeJson(file, run);
}

export function getScanRun(id: string): ScanRun | undefined {
  const file = path.join(SCANS_DIR, `${id}.json`);
  return readJson<ScanRun | undefined>(file, undefined);
}

export function getLatestScan(): ScanRun | undefined {
  ensureDir(SCANS_DIR);
  const files = fs.readdirSync(SCANS_DIR)
    .filter(f => f.endsWith('.json'))
    .sort()
    .reverse();
  if (files.length === 0) return undefined;
  return readJson<ScanRun>(path.join(SCANS_DIR, files[0]), null as unknown as ScanRun);
}

export function getScanCount(): number {
  ensureDir(SCANS_DIR);
  try {
    return fs.readdirSync(SCANS_DIR).filter(f => f.endsWith('.json')).length;
  } catch { return 0; }
}

export function getScanHistory(limit = 20): ScanRun[] {
  ensureDir(SCANS_DIR);
  try {
    const files = fs.readdirSync(SCANS_DIR)
      .filter(f => f.endsWith('.json'))
      .sort()
      .reverse()
      .slice(0, limit);
    return files.map(f => readJson<ScanRun>(path.join(SCANS_DIR, f), null as unknown as ScanRun)).filter(Boolean);
  } catch { return []; }
}

// ── Audit Log ──

const LOG_DIR = path.join(DATA_DIR, 'logs');

export function logAudit(
  event: string,
  severity: 'info' | 'warn' | 'error',
  message: string,
  metadata?: Record<string, unknown>,
) {
  ensureDir(LOG_DIR);
  const today = new Date().toISOString().slice(0, 10);
  const file = path.join(LOG_DIR, `${today}.log`);
  const entry = JSON.stringify({
    timestamp: new Date().toISOString(),
    event,
    severity,
    message,
    metadata: metadata || {},
  });
  fs.appendFileSync(file, entry + '\n', 'utf-8');
}

// ── Log Rotation ──

const LOG_RETENTION_DAYS = parseInt(process.env.LOG_RETENTION_DAYS || '30', 10);

export function rotateLogs() {
  ensureDir(LOG_DIR);
  const cutoff = Date.now() - LOG_RETENTION_DAYS * 86400000;
  try {
    for (const file of fs.readdirSync(LOG_DIR)) {
      if (!file.endsWith('.log')) continue;
      const dateStr = file.replace('.log', '');
      const fileDate = new Date(dateStr).getTime();
      if (fileDate < cutoff) {
        fs.unlinkSync(path.join(LOG_DIR, file));
        logAudit('log_rotated', 'info', `Rotated log: ${file}`);
      }
    }
  } catch { /* ok */ }
}

// ── Alert Config ──

interface AlertConfig {
  slack: boolean;
  telegram: boolean;
  email: boolean;
  teams: boolean;
  discord: boolean;
  frequency: 'daily' | 'weekly' | 'off';
}

const ALERT_CFG_FILE = path.join(DATA_DIR, 'alert_config.json');

const DEFAULT_ALERT_CONFIG: AlertConfig = {
  slack: false,
  telegram: false,
  email: false,
  teams: false,
  discord: false,
  frequency: config.reportSchedule,
};

export function getAlertConfig(): AlertConfig {
  return readJson<AlertConfig>(ALERT_CFG_FILE, DEFAULT_ALERT_CONFIG);
}

export function updateAlertConfig(partial: Partial<AlertConfig>): AlertConfig {
  const current = getAlertConfig();
  const updated = { ...current, ...partial };
  writeJson(ALERT_CFG_FILE, updated);
  logAudit('alert_config_updated', 'info', 'Alert configuration updated', { config: updated });
  return updated;
}
