#!/usr/bin/env node
// cli.ts — LAON VaultGuard CLI: security scan

import { randomUUID } from 'node:crypto';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';
import 'dotenv/config';
import { checkGitInstalled } from './git-monitor.js';
import { extractCandidates } from './candidate-filter.js';
import { analyzeCandidates } from './llm-harness.js';
import type { Finding, LlmProvider, Candidate } from './types.js';
import { config } from './config.js';

type ScanMode = 'all' | 'secrets' | 'sql' | 'versions' | 'db' | 'tls';

const SEVERITY_LABEL: Record<string, string> = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  info: 'INFO',
};

function categoryForFinding(f: { secretType: string; filePath: string; provider: string }): string {
  const t = f.secretType.toLowerCase();
  if (t.includes('sql') || t.includes('query') || t.includes('injection')) return 'SQL Injection';
  if (t.includes('password') || t.includes('credential') || t.includes('key') || t.includes('token') || t.includes('secret')) return 'Secrets';
  if (t.includes('version') || t.includes('outdated') || t.includes('tls') || t.includes('ssl')) return 'Versions/TLS';
  if (t.includes('connection') || t.includes('database') || t.includes('jdbc') || t.includes('mongodb') || t.includes('redis') || t.includes('postgres')) return 'DB Exposure';
  if (f.provider === 'AWS' || f.provider === 'Azure' || f.provider === 'GCP' || f.provider === 'KTCloud' || f.provider === 'NCP') return 'Secrets';
  return 'Other';
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === 'help' || command === '--help' || command === '-h') {
    printHelp();
    process.exit(0);
  }

  if (command === 'version' || command === '--version' || command === '-v') {
    console.log(`LAON VaultGuard v${config.deviceName ? '' : ''}0.2.0`);
    process.exit(0);
  }

  if (command === 'scan') {
    let repoPath = '';
    let mode: ScanMode = 'all';
    let skipLLM = false;

    for (let i = 1; i < args.length; i++) {
      if (args[i] === '--mode' && args[i + 1]) {
        mode = args[++i] as ScanMode;
      } else if (args[i] === '--no-llm') {
        skipLLM = true;
      } else if (!args[i].startsWith('--')) {
        repoPath = args[i];
      }
    }

    if (!repoPath) {
      console.error('Error: repository path required');
      console.error('Usage: npx laon-vaultguard scan <path> [--mode all|secrets|sql|versions|db|tls] [--no-llm]');
      process.exit(1);
    }

    const absolutePath = resolve(repoPath);
    if (!existsSync(absolutePath)) {
      console.error(`Error: path not found: ${absolutePath}`);
      process.exit(1);
    }

    await runScan(absolutePath, mode, skipLLM);
  } else {
    console.error(`Unknown command: ${command}`);
    printHelp();
    process.exit(1);
  }
}

async function runScan(repoPath: string, mode: ScanMode, skipLLM: boolean) {
  console.log(`
============================================
  LAON VaultGuard Security Scan
  LLM-based Observer for Non-public Keys
============================================
`);
  console.log(`Target:  ${repoPath}`);
  console.log(`Mode:    ${mode}`);
  console.log(`Device:  ${config.deviceName}`);
  console.log('');

  // Pre-flight
  if (!checkGitInstalled()) {
    console.error('Error: Git is not installed or not in PATH.');
    process.exit(1);
  }

  // Phase 1: git grep
  console.log('--- Stage 1: git grep keyword filter ---');
  let candidates: Candidate[];
  try {
    candidates = await extractCandidates(repoPath);
  } catch (err) {
    console.error(`Error: git grep failed: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  // Filter by mode
  if (mode !== 'all') {
    candidates = filterCandidates(candidates, mode);
  }

  console.log(`  Candidates found: ${candidates.length}`);

  if (candidates.length === 0) {
    console.log('\nResult: No suspicious patterns detected.');
    process.exit(0);
  }

  // Show candidate summary without LLM
  if (skipLLM) {
    printCandidateSummary(candidates, repoPath);
    process.exit(0);
  }

  // Phase 2: LLM
  console.log('\n--- Stage 2: LLM contextual analysis ---');
  const providers = config.llm.providers.filter(p => {
    if (p === 'ollama') return true;
    const c = config.llm[p as keyof typeof config.llm] as { apiKey: string };
    return c?.apiKey && !c.apiKey.startsWith('sk-your-');
  });

  if (providers.length === 0) {
    console.log('  No LLM configured. Use --no-llm to see raw candidates.');
    printCandidateSummary(candidates, repoPath);
    process.exit(0);
  }

  console.log(`  Providers: ${providers.join(', ')} (mode: ${config.llm.mode})`);

  let findings: Finding[] = [];
  try {
    const result = await analyzeCandidates(candidates);
    findings = result.findings.map((f, idx) => ({
      id: `CLI-${String(idx + 1).padStart(3, '0')}`,
      scanId: randomUUID(),
      repoId: 'cli',
      filePath: f.file,
      line: f.line,
      provider: f.provider,
      secretType: f.secretType,
      maskedFingerprint: f.maskedFingerprint,
      confidence: f.confidence,
      severity: f.severity,
      isPlaceholder: f.isPlaceholder,
      evidenceNote: f.evidenceNote,
      remediation: f.remediation,
      acknowledged: false,
      acknowledgedAt: null,
      acknowledgedNote: null,
      detectedAt: new Date().toISOString(),
      llmSources: result.providersUsed,
    }));
    console.log(`  LLM response: ${result.providersUsed.length} providers, ${result.totalTokens} tokens`);
  } catch (err) {
    console.error(`Error: LLM analysis failed: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  // Output
  if (findings.length === 0) {
    console.log('\nResult: No security issues detected.');
  } else {
    printFindingsReport(findings);
  }

  process.exit(0);
}

function filterCandidates(candidates: Candidate[], mode: ScanMode): Candidate[] {
  const patterns: Record<ScanMode, RegExp[]> = {
    secrets: [/key|token|secret|password|credential|ghp_|gho_|sk-|Bearer|eyJ|BEGIN/, /AKIA|ASIA|AIza|ncloud|ktcloud|ucloudbiz|x-ncp/],
    sql: [/SELECT.*FROM|INSERT.*INTO|\.query\s*\(|execute\s*\(|rawQuery|PreparedStatement|createQuery/, /sql\.format|db\.execute/],
    versions: [/OpenSSL|TLSv|SSLv|apache|nginx|php[ -]|python[ -]|node[ -]|mysql[ -]|postgres[ -]|redis[ -]|mongodb[ -]|wordpress|drupal|joomla/],
    db: [/jdbc:|mongodb:\/\/|redis:\/\/|mysql:\/\/|postgresql:\/\/|DATABASE_URL|DB_HOST|DB_PASSWORD|DB_USER|connectionString/],
    tls: [/verify\s*false|insecure\s*=\s*true|allowInsecure|rejectUnauthorized|NODE_TLS_REJECT_UNAUTHORIZED|ssl\s+off|WAF.*disabled|firewall.*off/],
    all: [/.*/],
  };

  const regexes = patterns[mode] || patterns.all;
  return candidates.filter(c => regexes.some(r => r.test(c.snippet)));
}

function printCandidateSummary(candidates: Candidate[], repoPath: string) {
  console.log('\n--- Raw Candidate Summary (no LLM analysis) ---');
  const byFile = new Map<string, Candidate[]>();
  for (const c of candidates) {
    const list = byFile.get(c.filePath) || [];
    list.push(c);
    byFile.set(c.filePath, list);
  }

  console.log(`Files with suspicious patterns: ${byFile.size}\n`);
  for (const [file, cands] of byFile) {
    console.log(`  ${file} (${cands.length} matches)`);
    for (const c of cands.slice(0, 3)) {
      console.log(`    L${c.lineNumber}: ${c.snippet.slice(0, 100)}`);
    }
    if (cands.length > 3) console.log(`    ... and ${cands.length - 3} more`);
  }
}

function printFindingsReport(findings: Finding[]) {
  const critical = findings.filter(f => f.severity === 'critical').length;
  const high = findings.filter(f => f.severity === 'high').length;
  const medium = findings.filter(f => f.severity === 'medium').length;
  const info = findings.filter(f => f.severity === 'info').length;

  // Group by category
  const byCategory = new Map<string, Finding[]>();
  for (const f of findings) {
    const cat = categoryForFinding(f);
    const list = byCategory.get(cat) || [];
    list.push(f);
    byCategory.set(cat, list);
  }

  console.log('\n============================================');
  console.log(`  SCAN RESULTS: ${findings.length} findings`);
  console.log(`  Critical: ${critical}  High: ${high}  Medium: ${medium}  Info: ${info}`);
  console.log('============================================\n');

  for (const [category, items] of byCategory) {
    const catCritical = items.filter(f => f.severity === 'critical').length;
    const catHigh = items.filter(f => f.severity === 'high').length;
    console.log(`--- ${category} (${items.length} findings, ${catCritical} critical, ${catHigh} high) ---`);

    for (const f of items) {
      const sev = SEVERITY_LABEL[f.severity] || f.severity;
      console.log(`\n  [${sev}] ${f.provider} — ${f.secretType}`);
      console.log(`  File:      ${f.filePath}${f.line ? `:${f.line}` : ''}`);
      console.log(`  Confidence: ${f.confidence}`);
      if (f.maskedFingerprint !== '[REDACTED]') {
        console.log(`  Fingerprint: ${f.maskedFingerprint}`);
      }
      console.log(`  Remediation: ${f.remediation}`);
    }
    console.log('');
  }
}

function printHelp() {
  console.log(`
LAON VaultGuard CLI — LLM-based Security Scanner

Usage:
  npx laon-vaultguard scan <path> [options]
  npx laon-vaultguard version
  npx laon-vaultguard help

Options:
  --mode <mode>    Scan mode: all (default), secrets, sql, versions, db, tls
  --no-llm         Skip LLM analysis, show raw candidates only

Examples:
  npx laon-vaultguard scan .
  npx laon-vaultguard scan ~/projects/my-app
  npx laon-vaultguard scan /path/to/repo --mode sql
  npx laon-vaultguard scan . --no-llm
  npx laon-vaultguard scan . --mode secrets

Scan Modes:
  all       All security checks (default)
  secrets   Cloud keys, API tokens, passwords, private keys
  sql       SQL injection patterns, raw queries, concatenation
  versions  Outdated OpenSSL, TLS, Apache, Nginx, PHP, Python, Node, DBMS, CMS
  db        Database connection strings, credentials in connection URLs
  tls       SSL/TLS misconfig, insecure settings, WAF bypass

Environment (.env or export):
  CLAUDE_API_KEY=sk-ant-...       Claude (Anthropic)
  DEEPSEEK_API_KEY=sk-...         DeepSeek
  OPENAI_API_KEY=sk-...           OpenAI
  LLM_PROVIDERS=claude,deepseek   LLM providers (comma-separated)
  LLM_MODE=parallel               parallel | sequential | majority
  SCAN_TIMEOUT_MS=60000           LLM timeout (ms)
  SCAN_MAX_CANDIDATES=500         Max candidates per scan

  API keys are stored in .env and never committed to Git.
`);
}

main().catch(err => {
  console.error('Error:', err instanceof Error ? err.message : String(err));
  process.exit(1);
});
