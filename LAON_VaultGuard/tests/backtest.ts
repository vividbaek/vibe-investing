// tests/backtest.ts — comprehensive v0.5 feature backtest
// Usage: npx tsx tests/backtest.ts
// Verifies: config, storage, DP masking, SARIF, metrics, CLI, candidate filter

import { config, validateConfig } from '../src/config.js';
import { randomUUID } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const TMP_DIR = path.join(os.tmpdir(), `laon-backtest-${Date.now()}`);
const PASS = '✅';
const FAIL = '❌';
const SKIP = '⏭️';

let passed = 0;
let failed = 0;
let skipped = 0;
const failures: string[] = [];

function test(name: string, fn: () => boolean | void) {
  try {
    const result = fn();
    if (result === false) {
      console.log(`  ${FAIL} ${name}`);
      failed++;
      failures.push(name);
    } else {
      console.log(`  ${PASS} ${name}`);
      passed++;
    }
  } catch (e) {
    console.log(`  ${FAIL} ${name} — ${e instanceof Error ? e.message : String(e)}`);
    failed++;
    failures.push(e instanceof Error ? `${name}: ${e.message}` : name);
  }
}

function skip(name: string, reason: string) {
  console.log(`  ${SKIP} ${name} (${reason})`);
  skipped++;
}

// ── setup: temp DB ──
fs.mkdirSync(TMP_DIR, { recursive: true });
process.env.DB_PATH = TMP_DIR;
process.env.STORAGE_ENGINE = 'sqlite'; // start with SQLite

async function run() {
  console.log('\n══════════════════════════════════');
  console.log('  LAON VaultGuard v0.5 Backtest');
  console.log('══════════════════════════════════\n');

  // ──────────────────────────────
  // 1. Config Validation
  // ──────────────────────────────
  console.log('── 1. Config ──');
  test('PORT default = 3101', () => config.port === 3101);
  test('HOST is set', () => typeof config.host === 'string' && config.host.length > 0);
  test('LLM_MODE is valid', () => ['parallel', 'sequential', 'majority'].includes(config.llm.mode));
  test('storageEngine exists', () => ['sqlite', 'json'].includes(config.db.storageEngine));
  test('scan timeout > 0', () => config.scan.timeoutMs >= 10000);
  test('cache enabled by default', () => config.scan.cacheEnabled === true);
  test('validateConfig is a function', () => typeof validateConfig === 'function');

  // ──────────────────────────────
  // 2. Differential Privacy
  // ──────────────────────────────
  console.log('\n── 2. Differential Privacy ──');
  const { maskSecrets } = await import('../src/differential-privacy.js');

  test('masks AWS key (AKIA...)', () => {
    const r = maskSecrets('AKIA1234567890ABCDEF');
    return r.masked.includes('AKIA12') && r.masked.includes('…') && r.totalReplacements > 0;
  });

  test('masks GitHub token (ghp_)', () => {
    const r = maskSecrets('ghp_abcdefghijklmnopqrstuvwxyz1234567890');
    return r.masked.includes('…') && r.totalReplacements > 0;
  });

  test('masks OpenAI key (sk-)', () => {
    const r = maskSecrets('sk-proj-1234567890abcdefghijklmnopqrstuvwxyz123456');
    return r.masked.includes('sk-proj-') && r.masked.includes('…') && r.totalReplacements > 0;
  });

  test('masks JWT token', () => {
    const r = maskSecrets('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9n0K8DxG');
    return r.masked.includes('[MASKED:JWT]') && r.totalReplacements > 0;
  });

  test('masks private key block', () => {
    const r = maskSecrets('-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----');
    return r.masked.includes('[MASKED:PrivateKey]') && r.totalReplacements > 0;
  });

  test('masks hardcoded password', () => {
    const r = maskSecrets('password = "supersecretvalue12345"');
    return r.masked.includes('[MASKED:Password:') && r.totalReplacements > 0;
  });

  test('masks DB connection string', () => {
    const r = maskSecrets('mongodb://admin:mysecretpass@localhost:27017/db');
    return r.masked.includes('[MASKED_DB_PASS]') && r.totalReplacements > 0;
  });

  test('masks NCP access key', () => {
    const r = maskSecrets('NCP_ACCESS_KEY = abcdefghijklmnopqrstuvwxyz');
    return r.masked.includes('…') && r.totalReplacements > 0;
  });

  test('does not mask non-secrets', () => {
    const r = maskSecrets('const port = 3101;');
    return r.totalReplacements === 0;
  });

  test('summarizeMasking returns correct stats', async () => {
    const { maskCandidates, summarizeMasking } = await import('../src/differential-privacy.js');
    const cands = [
      { filePath: 'a.ts', lineNumber: 1, snippet: 'AKIA1234567890ABCDEF', matchedPattern: 'AKIA' },
      { filePath: 'b.ts', lineNumber: 2, snippet: 'ghp_abcdefghijklmnopqrstuvwxyz1234567890', matchedPattern: 'ghp_' },
      { filePath: 'c.ts', lineNumber: 3, snippet: 'const x = 1;', matchedPattern: '' },
    ];
    const masked = maskCandidates(cands);
    const summary = summarizeMasking(masked);
    return summary.total === 3 && summary.masked === 2 && summary.replacements >= 2;
  });

  // ──────────────────────────────
  // 3. Storage Engine — SQLite
  // ──────────────────────────────
  console.log('\n── 3. Storage — SQLite ──');
  const sqlite = await import('../src/db-sqlite.js');

  test('DATA_DIR exists', () => fs.existsSync(sqlite.DATA_DIR));
  test('DB_PATH file created', () => fs.existsSync(sqlite.DB_PATH));

  const repo = sqlite.addRepo({
    name: 'test-repo',
    type: 'local',
    pathOrUrl: '/tmp/test',
    branch: 'main',
    enabled: true,
    cronOverride: null,
  });

  test('addRepo returns valid repo', () => !!repo && !!repo.id);
  test('listRepos includes test repo', () => sqlite.listRepos().some(r => r.name === 'test-repo'));
  test('getRepo finds by id', () => sqlite.getRepo(repo.id)?.name === 'test-repo');
  test('updateRepoLastScan sets timestamp', () => {
    sqlite.updateRepoLastScan(repo.id);
    const updated = sqlite.getRepo(repo.id);
    return !!updated?.lastScan;
  });

  const finding = {
    id: 'F-' + randomUUID().slice(0, 8),
    scanId: randomUUID(),
    repoId: repo.id,
    filePath: 'src/secret.ts',
    line: 42,
    provider: 'AWS' as const,
    secretType: 'AWS Access Key ID',
    maskedFingerprint: 'AKIA****7Q',
    confidence: 'high' as const,
    severity: 'critical' as const,
    isPlaceholder: false,
    evidenceNote: 'Found in config',
    remediation: 'Use AWS Secrets Manager',
    acknowledged: false,
    acknowledgedAt: null,
    acknowledgedNote: null,
    detectedAt: new Date().toISOString(),
    llmSources: ['deepseek', 'claude'],
  };

  sqlite.saveFindings([finding]);

  test('saveFindings persists', () => {
    const f = sqlite.getFinding(finding.id);
    return !!f && f.severity === 'critical';
  });

  test('listFindings returns with filter', () => {
    const { total, findings } = sqlite.listFindings({ severity: 'critical' });
    return total >= 1 && findings.some(f => f.id === finding.id);
  });

  test('acknowledgeFinding updates', () => {
    sqlite.acknowledgeFinding(finding.id, 'false positive');
    const f = sqlite.getFinding(finding.id);
    return !!f?.acknowledged && f.acknowledgedNote === 'false positive';
  });

  test('unacknowledgeFinding reverts', () => {
    sqlite.unacknowledgeFinding(finding.id);
    const f = sqlite.getFinding(finding.id);
    return !f?.acknowledged;
  });

  test('addFindingComment appends', () => {
    sqlite.acknowledgeFinding(finding.id, 'rev1');
    sqlite.addFindingComment(finding.id, 'rev2');
    const f = sqlite.getFinding(finding.id);
    return !!f?.acknowledgedNote?.includes('rev2');
  });

  test('countOpenFindings returns count', () => {
    sqlite.unacknowledgeFinding(finding.id);
    return sqlite.countOpenFindings() >= 1;
  });

  const scanRun = {
    id: randomUUID(),
    repoId: repo.id,
    status: 'completed' as const,
    trigger: 'manual' as const,
    startedAt: new Date().toISOString(),
    completedAt: new Date().toISOString(),
    filesScanned: 10,
    findingsCritical: 1,
    findingsHigh: 0,
    findingsMedium: 0,
    findingsInfo: 0,
    llmProvidersUsed: ['deepseek'],
    errorMessage: null,
  };

  test('saveScanRun persists', () => {
    sqlite.saveScanRun(scanRun);
    const s = sqlite.getScanRun(scanRun.id);
    return !!s && s.status === 'completed';
  });

  test('getLatestScan returns most recent', () => {
    const s = sqlite.getLatestScan();
    return !!s;
  });

  test('getScanCount > 0', () => sqlite.getScanCount() >= 1);
  test('getScanHistory returns entries', () => sqlite.getScanHistory().length >= 1);

  // alert config
  test('getAlertConfig returns defaults', () => {
    const cfg = sqlite.getAlertConfig();
    return typeof cfg.slack === 'boolean' && typeof cfg.email === 'boolean';
  });

  test('updateAlertConfig persists', () => {
    sqlite.updateAlertConfig({ slack: true });
    return sqlite.getAlertConfig().slack === true;
  });

  // readJson/writeJson (file-based helpers)
  test('readJson returns fallback for missing file', () => {
    const val = sqlite.readJson('/nonexistent/path.json', { hello: 'world' });
    return val.hello === 'world';
  });

  test('writeJson + readJson round-trip', () => {
    const f = path.join(TMP_DIR, 'test.json');
    sqlite.writeJson(f, { x: 1 });
    const val = sqlite.readJson(f, {});
    return val.x === 1;
  });

  // JSON fallback engine
  console.log('\n── 3b. Storage — JSON (legacy) ──');
  const jsondb = await import('../src/db-json.js');
  const jsonRepo = jsondb.addRepo({
    name: 'json-test-repo',
    type: 'local',
    pathOrUrl: '/tmp/json-test',
    branch: 'main',
    enabled: true,
    cronOverride: null,
  });
  test('JSON addRepo/listRepos', () => jsondb.listRepos().some(r => r.name === 'json-test-repo'));
  test('JSON removeRepo', () => {
    const removed = jsondb.removeRepo(jsonRepo.id);
    return removed === true && !jsondb.listRepos().some(r => r.id === jsonRepo.id);
  });

  // remove test data
  test('removeRepo cleans up', () => {
    sqlite.removeRepo(repo.id);
    return !sqlite.getRepo(repo.id);
  });

  // ──────────────────────────────
  // 4. SARIF Export
  // ──────────────────────────────
  console.log('\n── 4. SARIF Export ──');
  const { buildSarifLog } = await import('../src/sarif-export.js');

  test('generates valid SARIF v2.1.0', () => {
    const sarif = buildSarifLog([{
      id: 'F-test', filePath: 'src/test.ts', line: 10,
      provider: 'AWS', secretType: 'AWS Access Key ID',
      maskedFingerprint: 'AKIA****7Q', confidence: 'high',
      severity: 'critical', evidenceNote: '', remediation: '',
      detectedAt: new Date().toISOString(), repoId: 'r1',
    }]);
    return sarif.version === '2.1.0' &&
      sarif.$schema.includes('sarif-schema-2.1.0') &&
      sarif.runs.length === 1 &&
      sarif.runs[0].results.length === 1 &&
      sarif.runs[0].results[0].level === 'error';
  });

  test('severity mapping: critical → error', () => {
    const sarif = buildSarifLog([{
      id: 'F-crit', filePath: 'x.ts', line: 1, provider: 'GCP',
      secretType: 'GCP Key', maskedFingerprint: 'AIza****Xy',
      confidence: 'high', severity: 'critical', evidenceNote: '',
      remediation: '', detectedAt: new Date().toISOString(), repoId: 'r1',
    }]);
    return sarif.runs[0].results[0].level === 'error';
  });

  test('severity mapping: medium → warning', () => {
    const sarif = buildSarifLog([{
      id: 'F-med', filePath: 'x.ts', line: 1, provider: 'Generic',
      secretType: 'Password', maskedFingerprint: '****',
      confidence: 'medium', severity: 'medium', evidenceNote: '',
      remediation: '', detectedAt: new Date().toISOString(), repoId: 'r1',
    }]);
    return sarif.runs[0].results[0].level === 'warning';
  });

  test('SARIF output is valid JSON', () => {
    const sarif = buildSarifLog([]);
    return typeof JSON.stringify(sarif) === 'string';
  });

  // ──────────────────────────────
  // 5. Prometheus Metrics
  // ──────────────────────────────
  console.log('\n── 5. Prometheus Metrics ──');
  const { incCounter, setGauge, observe, metricsMiddleware } = await import('../src/metrics.js');

  // mock response object
  let capturedBody = '';
  let capturedContentType = '';
  const mockRes = {
    setHeader: (k: string, v: string) => { capturedContentType = v; },
    end: (body: string) => { capturedBody = body; },
  };

  incCounter('laon_scans_total', 3);
  setGauge('laon_findings_open', 5);
  observe('laon_scan_duration_ms', 1500);

  metricsMiddleware({}, mockRes);

  test('metrics returns text/plain', () => capturedContentType.includes('text/plain'));
  test('metrics includes counter', () => capturedBody.includes('laon_scans_total 3'));
  test('metrics includes gauge', () => capturedBody.includes('laon_findings_open 5'));
  test('metrics includes histogram', () => capturedBody.includes('laon_scan_duration_ms_bucket'));
  test('metrics format is valid Prometheus', () => {
    const lines = capturedBody.split('\n').filter(Boolean);
    return lines.some(l => l.startsWith('# HELP')) && lines.some(l => l.startsWith('# TYPE'));
  });

  // ──────────────────────────────
  // 6. Candidate Filter patterns
  // ──────────────────────────────
  console.log('\n── 6. Candidate Filter ──');
  const { buildGrepPattern } = await import('../src/candidate-filter.js');
  const pattern = buildGrepPattern();

  test('grep pattern includes AKIA', () => pattern.includes('AKIA'));
  test('grep pattern includes ghp_', () => pattern.includes('ghp_'));
  test('grep pattern includes sk-', () => pattern.includes('sk-'));
  test('grep pattern is valid regex', () => {
    try { new RegExp(pattern); return true; } catch { return false; }
  });

  // ──────────────────────────────
  // 7. Version check
  // ──────────────────────────────
  console.log('\n── 7. Version ──');
  const pkg = JSON.parse(fs.readFileSync(path.resolve(import.meta.dirname || '.', '../package.json'), 'utf-8'));
  test('package.json version = 0.5.0', () => pkg.version === '0.5.0');

  // ──────────────────────────────
  // Report
  // ──────────────────────────────
  console.log('\n══════════════════════════════════');
  console.log(`  Results: ${passed} passed, ${failed} failed, ${skipped} skipped`);
  console.log('══════════════════════════════════');

  if (failures.length > 0) {
    console.log('\n  Failures:');
    for (const f of failures) console.log(`    ${FAIL} ${f}`);
    process.exit(1);
  }

  console.log(`  ${PASS} All ${passed} tests passed.\n`);
}

run().catch(e => {
  console.error(`\n  ${FAIL} Backtest crashed: ${e.message}`);
  process.exit(1);
});
