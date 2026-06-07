// migrate-json-to-sqlite.ts — one-shot JSON → SQLite data migration
// Usage: npx tsx src/migrate-json-to-sqlite.ts

import fs from 'node:fs';
import path from 'node:path';
import type { Finding, Repository, ScanRun } from './types.js';
import { config } from './config.js';
import Database from 'better-sqlite3';

const DATA_DIR = path.resolve(config.db.path);
const DB_PATH = path.join(DATA_DIR, 'vaultguard.db');

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('busy_timeout = 5000');
db.pragma('foreign_keys = ON');

// ensure schema
db.exec(`
  CREATE TABLE IF NOT EXISTS repositories (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
    path_or_url TEXT NOT NULL, branch TEXT DEFAULT 'main',
    enabled INTEGER DEFAULT 1, cron_override TEXT,
    last_scan TEXT, created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY, scan_id TEXT, repo_id TEXT,
    file_path TEXT NOT NULL, line INTEGER, provider TEXT,
    secret_type TEXT, masked_fingerprint TEXT, confidence TEXT,
    severity TEXT, is_placeholder INTEGER DEFAULT 0,
    evidence_note TEXT, remediation TEXT, acknowledged INTEGER DEFAULT 0,
    acknowledged_at TEXT, acknowledged_note TEXT,
    detected_at TEXT NOT NULL, llm_sources TEXT
  );
  CREATE TABLE IF NOT EXISTS scan_runs (
    id TEXT PRIMARY KEY, repo_id TEXT, status TEXT NOT NULL,
    trigger TEXT NOT NULL, started_at TEXT NOT NULL,
    completed_at TEXT, files_scanned INTEGER DEFAULT 0,
    findings_critical INTEGER DEFAULT 0, findings_high INTEGER DEFAULT 0,
    findings_medium INTEGER DEFAULT 0, findings_info INTEGER DEFAULT 0,
    llm_providers_used TEXT, error_message TEXT
  );
  CREATE TABLE IF NOT EXISTS alert_config (
    key TEXT PRIMARY KEY, value TEXT NOT NULL
  );
`);

const insertRepo = db.prepare(`
  INSERT OR IGNORE INTO repositories
  (id, name, type, path_or_url, branch, enabled, cron_override, last_scan, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const insertFinding = db.prepare(`
  INSERT OR IGNORE INTO findings
  (id, scan_id, repo_id, file_path, line, provider, secret_type,
   masked_fingerprint, confidence, severity, is_placeholder,
   evidence_note, remediation, acknowledged, acknowledged_at,
   acknowledged_note, detected_at, llm_sources)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const insertScanRun = db.prepare(`
  INSERT OR IGNORE INTO scan_runs
  (id, repo_id, status, trigger, started_at, completed_at,
   files_scanned, findings_critical, findings_high, findings_medium, findings_info,
   llm_providers_used, error_message)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

// ── migrate repos ──
const reposFile = path.join(DATA_DIR, 'repos.json');
if (fs.existsSync(reposFile)) {
  const repos = JSON.parse(fs.readFileSync(reposFile, 'utf-8')) as Repository[];
  const tx = db.transaction(() => {
    for (const r of repos) {
      insertRepo.run(
        r.id, r.name, r.type, r.pathOrUrl, r.branch,
        r.enabled ? 1 : 0, r.cronOverride, r.lastScan, r.createdAt,
      );
    }
  });
  tx();
  console.log(`  ✅ ${repos.length} repos migrated`);
} else {
  console.log('  ⏭ no repos.json found');
}

// ── migrate findings ──
const findingsFile = path.join(DATA_DIR, 'findings.json');
if (fs.existsSync(findingsFile)) {
  const findings = JSON.parse(fs.readFileSync(findingsFile, 'utf-8')) as Finding[];
  const tx = db.transaction(() => {
    for (const f of findings) {
      insertFinding.run(
        f.id, f.scanId, f.repoId, f.filePath, f.line, f.provider, f.secretType,
        f.maskedFingerprint, f.confidence, f.severity, f.isPlaceholder ? 1 : 0,
        f.evidenceNote, f.remediation, f.acknowledged ? 1 : 0,
        f.acknowledgedAt, f.acknowledgedNote, f.detectedAt,
        f.llmSources.join(','),
      );
    }
  });
  tx();
  console.log(`  ✅ ${findings.length} findings migrated`);
} else {
  console.log('  ⏭ no findings.json found');
}

// ── migrate scan runs ──
const scansDir = path.join(DATA_DIR, 'scans');
if (fs.existsSync(scansDir)) {
  const files = fs.readdirSync(scansDir).filter(f => f.endsWith('.json'));
  const tx = db.transaction(() => {
    for (const file of files) {
      const run = JSON.parse(fs.readFileSync(path.join(scansDir, file), 'utf-8')) as ScanRun;
      insertScanRun.run(
        run.id, run.repoId, run.status, run.trigger, run.startedAt, run.completedAt,
        run.filesScanned, run.findingsCritical, run.findingsHigh,
        run.findingsMedium, run.findingsInfo,
        run.llmProvidersUsed.join(','), run.errorMessage,
      );
    }
  });
  tx();
  console.log(`  ✅ ${files.length} scan runs migrated`);
} else {
  console.log('  ⏭ no scans/ directory found');
}

// ── migrate alert config ──
const alertFile = path.join(DATA_DIR, 'alert_config.json');
if (fs.existsSync(alertFile)) {
  const config = JSON.parse(fs.readFileSync(alertFile, 'utf-8'));
  db.prepare('INSERT OR REPLACE INTO alert_config (key, value) VALUES (?, ?)').run('alert_config', JSON.stringify(config));
  console.log('  ✅ alert config migrated');
} else {
  console.log('  ⏭ no alert_config.json found');
}

const count = db.prepare('SELECT COUNT(*) as cnt FROM repositories').get() as { cnt: number };
console.log(`\n📊 Migration complete. DB now has ${count.cnt} repos.`);
console.log(`   Set STORAGE_ENGINE=sqlite in .env to use SQLite.\n`);

db.close();
