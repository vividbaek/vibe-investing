// db-sqlite.ts — SQLite (better-sqlite3) storage engine
// replaces JSON file read-modify-write with ACID transactions + WAL mode

import Database from 'better-sqlite3';
import path from 'node:path';
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import type { Repository, ScanRun, Finding } from './types.js';
import { config } from './config.js';

const DATA_DIR = path.resolve(config.db.path);
const DB_PATH = path.join(DATA_DIR, 'vaultguard.db');

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const db = new Database(DB_PATH);

// ── performance + concurrency tuning ──
db.pragma('journal_mode = WAL');
db.pragma('busy_timeout = 5000');
db.pragma('foreign_keys = ON');
db.pragma('synchronous = NORMAL');

// ── schema ──
db.exec(`
  CREATE TABLE IF NOT EXISTS repositories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    path_or_url TEXT NOT NULL,
    branch TEXT DEFAULT 'main',
    enabled INTEGER DEFAULT 1,
    cron_override TEXT,
    last_scan TEXT,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    scan_id TEXT,
    repo_id TEXT,
    file_path TEXT NOT NULL,
    line INTEGER,
    provider TEXT,
    secret_type TEXT,
    masked_fingerprint TEXT,
    confidence TEXT,
    severity TEXT,
    is_placeholder INTEGER DEFAULT 0,
    evidence_note TEXT,
    remediation TEXT,
    acknowledged INTEGER DEFAULT 0,
    acknowledged_at TEXT,
    acknowledged_note TEXT,
    detected_at TEXT NOT NULL,
    llm_sources TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idx_findings_repo ON findings(repo_id);
  CREATE INDEX IF NOT EXISTS idx_findings_ack ON findings(acknowledged);
  CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
  CREATE INDEX IF NOT EXISTS idx_findings_detected ON findings(detected_at DESC);

  CREATE TABLE IF NOT EXISTS scan_runs (
    id TEXT PRIMARY KEY,
    repo_id TEXT,
    status TEXT NOT NULL,
    trigger TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    files_scanned INTEGER DEFAULT 0,
    findings_critical INTEGER DEFAULT 0,
    findings_high INTEGER DEFAULT 0,
    findings_medium INTEGER DEFAULT 0,
    findings_info INTEGER DEFAULT 0,
    llm_providers_used TEXT,
    error_message TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS alert_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  );
`);

export { DATA_DIR, DB_PATH };

// ── column mapping: snake_case DB → camelCase TS ──

function rowToRepo(r: Record<string, unknown>): Repository {
  return {
    id: r.id as string,
    name: r.name as string,
    type: r.type as Repository['type'],
    pathOrUrl: r.path_or_url as string,
    branch: r.branch as string,
    enabled: Boolean(r.enabled),
    cronOverride: (r.cron_override as string) || null,
    lastScan: (r.last_scan as string) || null,
    createdAt: r.created_at as string,
  };
}

function rowToFinding(r: Record<string, unknown>): Finding {
  return {
    id: r.id as string,
    scanId: (r.scan_id as string) || '',
    repoId: (r.repo_id as string) || '',
    filePath: r.file_path as string,
    line: (r.line as number) || null,
    provider: r.provider as Finding['provider'],
    secretType: r.secret_type as string,
    maskedFingerprint: r.masked_fingerprint as string,
    confidence: r.confidence as Finding['confidence'],
    severity: r.severity as Finding['severity'],
    isPlaceholder: Boolean(r.is_placeholder),
    evidenceNote: r.evidence_note as string,
    remediation: r.remediation as string,
    acknowledged: Boolean(r.acknowledged),
    acknowledgedAt: (r.acknowledged_at as string) || null,
    acknowledgedNote: (r.acknowledged_note as string) || null,
    detectedAt: r.detected_at as string,
    llmSources: (r.llm_sources as string) ? (r.llm_sources as string).split(',').filter(Boolean) as Finding['llmSources'] : [],
  };
}

function rowToScanRun(r: Record<string, unknown>): ScanRun {
  return {
    id: r.id as string,
    repoId: (r.repo_id as string) || '',
    status: r.status as ScanRun['status'],
    trigger: r.trigger as ScanRun['trigger'],
    startedAt: r.started_at as string,
    completedAt: (r.completed_at as string) || null,
    filesScanned: (r.files_scanned as number) || 0,
    findingsCritical: (r.findings_critical as number) || 0,
    findingsHigh: (r.findings_high as number) || 0,
    findingsMedium: (r.findings_medium as number) || 0,
    findingsInfo: (r.findings_info as number) || 0,
    llmProvidersUsed: (r.llm_providers_used as string) ? (r.llm_providers_used as string).split(',').filter(Boolean) : [],
    errorMessage: (r.error_message as string) || null,
  };
}

// ── Repos ──

export function listRepos(): Repository[] {
  return (db.prepare('SELECT * FROM repositories ORDER BY created_at DESC').all() as Record<string, unknown>[]).map(rowToRepo);
}

export function getRepo(id: string): Repository | undefined {
  const row = db.prepare('SELECT * FROM repositories WHERE id = ?').get(id);
  return row ? rowToRepo(row as Record<string, unknown>) : undefined;
}

export function addRepo(input: Omit<Repository, 'id' | 'lastScan' | 'createdAt'>): Repository {
  const id = randomUUID();
  const createdAt = new Date().toISOString();
  db.prepare(`
    INSERT INTO repositories (id, name, type, path_or_url, branch, enabled, cron_override, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).run(id, input.name, input.type, input.pathOrUrl, input.branch, input.enabled ? 1 : 0, input.cronOverride, createdAt);
  return getRepo(id)!;
}

export function removeRepo(id: string): boolean {
  const result = db.prepare('DELETE FROM repositories WHERE id = ?').run(id);
  return result.changes > 0;
}

export function updateRepoLastScan(id: string) {
  db.prepare('UPDATE repositories SET last_scan = ? WHERE id = ?').run(new Date().toISOString(), id);
}

// ── Findings ──

export function listFindings(filter?: {
  severity?: string;
  acknowledged?: boolean;
  repoId?: string;
  limit?: number;
  offset?: number;
}): { total: number; findings: Finding[] } {
  let where = '1=1';
  const params: unknown[] = [];

  if (filter?.severity) { where += ' AND severity = ?'; params.push(filter.severity); }
  if (filter?.acknowledged !== undefined) { where += ' AND acknowledged = ?'; params.push(filter.acknowledged ? 1 : 0); }
  if (filter?.repoId) { where += ' AND repo_id = ?'; params.push(filter.repoId); }

  const countRow = db.prepare(`SELECT COUNT(*) as cnt FROM findings WHERE ${where}`).get(...params) as { cnt: number };
  const total = countRow.cnt;

  const limit = filter?.limit || 50;
  const offset = filter?.offset || 0;
  const rows = db.prepare(`SELECT * FROM findings WHERE ${where} ORDER BY detected_at DESC LIMIT ? OFFSET ?`)
    .all(...params, limit, offset);

  return { total, findings: rows.map(r => rowToFinding(r as Record<string, unknown>)) };
}

export function getFinding(id: string): Finding | undefined {
  const row = db.prepare('SELECT * FROM findings WHERE id = ?').get(id);
  return row ? rowToFinding(row as Record<string, unknown>) : undefined;
}

export function saveFindings(findings: Finding[]) {
  const insert = db.prepare(`
    INSERT OR REPLACE INTO findings
    (id, scan_id, repo_id, file_path, line, provider, secret_type,
     masked_fingerprint, confidence, severity, is_placeholder,
     evidence_note, remediation, acknowledged, acknowledged_at,
     acknowledged_note, detected_at, llm_sources)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const tx = db.transaction((items: Finding[]) => {
    for (const f of items) {
      insert.run(
        f.id, f.scanId, f.repoId, f.filePath, f.line, f.provider, f.secretType,
        f.maskedFingerprint, f.confidence, f.severity, f.isPlaceholder ? 1 : 0,
        f.evidenceNote, f.remediation, f.acknowledged ? 1 : 0, f.acknowledgedAt,
        f.acknowledgedNote, f.detectedAt, f.llmSources.join(','),
      );
    }
  });
  tx(findings);
}

export function acknowledgeFinding(id: string, note?: string): Finding | undefined {
  const now = new Date().toISOString();
  const result = db.prepare('UPDATE findings SET acknowledged = 1, acknowledged_at = ?, acknowledged_note = ? WHERE id = ?')
    .run(now, note || null, id);
  return result.changes > 0 ? getFinding(id) : undefined;
}

export function unacknowledgeFinding(id: string): Finding | undefined {
  db.prepare('UPDATE findings SET acknowledged = 0, acknowledged_at = NULL, acknowledged_note = NULL WHERE id = ?').run(id);
  return getFinding(id);
}

export function addFindingComment(id: string, comment: string): Finding | undefined {
  const f = getFinding(id);
  if (!f) return undefined;
  const updated = (f.acknowledgedNote ? f.acknowledgedNote + ' | ' : '') + comment;
  db.prepare('UPDATE findings SET acknowledged_note = ? WHERE id = ?').run(updated, id);
  return getFinding(id);
}

export function countOpenFindings(): number {
  const row = db.prepare('SELECT COUNT(*) as cnt FROM findings WHERE acknowledged = 0').get() as { cnt: number };
  return row.cnt;
}

// ── Scan Runs ──

export function saveScanRun(run: ScanRun) {
  db.prepare(`
    INSERT OR REPLACE INTO scan_runs
    (id, repo_id, status, trigger, started_at, completed_at,
     files_scanned, findings_critical, findings_high, findings_medium, findings_info,
     llm_providers_used, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    run.id, run.repoId, run.status, run.trigger, run.startedAt, run.completedAt,
    run.filesScanned, run.findingsCritical, run.findingsHigh, run.findingsMedium, run.findingsInfo,
    run.llmProvidersUsed.join(','), run.errorMessage,
  );
}

export function getScanRun(id: string): ScanRun | undefined {
  const row = db.prepare('SELECT * FROM scan_runs WHERE id = ?').get(id);
  return row ? rowToScanRun(row as Record<string, unknown>) : undefined;
}

export function getLatestScan(): ScanRun | undefined {
  const row = db.prepare('SELECT * FROM scan_runs ORDER BY started_at DESC LIMIT 1').get();
  return row ? rowToScanRun(row as Record<string, unknown>) : undefined;
}

export function getScanCount(): number {
  const row = db.prepare('SELECT COUNT(*) as cnt FROM scan_runs').get() as { cnt: number };
  return row.cnt;
}

export function getScanHistory(limit = 20): ScanRun[] {
  return db.prepare('SELECT * FROM scan_runs ORDER BY started_at DESC LIMIT ?')
    .all(limit)
    .map(r => rowToScanRun(r as Record<string, unknown>));
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

const DEFAULT_ALERT_CONFIG: AlertConfig = {
  slack: false,
  telegram: false,
  email: false,
  teams: false,
  discord: false,
  frequency: 'daily',
};

export function getAlertConfig(): AlertConfig {
  const stored = db.prepare('SELECT value FROM alert_config WHERE key = ?').get('alert_config') as { value: string } | undefined;
  if (!stored) return { ...DEFAULT_ALERT_CONFIG };
  try {
    return { ...DEFAULT_ALERT_CONFIG, ...JSON.parse(stored.value) };
  } catch {
    return { ...DEFAULT_ALERT_CONFIG };
  }
}

export function updateAlertConfig(partial: Partial<AlertConfig>): AlertConfig {
  const current = getAlertConfig();
  const updated = { ...current, ...partial };
  db.prepare('INSERT OR REPLACE INTO alert_config (key, value) VALUES (?, ?)').run('alert_config', JSON.stringify(updated));
  return updated;
}

// ── Log (still file-based — audit log is append-only, simple) ──

const LOG_DIR = path.join(DATA_DIR, 'logs');

function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

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
      }
    }
  } catch { /* ok */ }
}

// ── File-based helpers (for cache, OAuth, and other non-SQLite data) ──

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
