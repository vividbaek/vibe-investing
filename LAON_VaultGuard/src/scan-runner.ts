// scan-runner.ts — single repository scan pipeline (v0.3)

import { randomUUID, createHash } from 'node:crypto';
import type { Repository, ScanRun, Finding, LlmProvider, Candidate } from './types.js';
import { saveScanRun, saveFindings, logAudit, readJson, writeJson } from './db.js';
import { checkGitInstalled, cloneGithubRepo, cleanupTempRepo } from './git-monitor.js';
import { extractCandidates, isHighEntropy, classifyContextRisk } from './candidate-filter.js';
import { analyzeCandidates } from './llm-harness.js';
import { emitSse } from './sse.js';
import { sendAlerts } from './alert-engine.js';
import { config } from './config.js';
import { join } from 'node:path';

const MAX_CANDIDATES = config.scan.maxCandidates;
const DATA_DIR = config.db.path;

interface CacheEntry {
  hash: string;
  findings: number;
  scannedAt: string;
}

function getCacheKey(repoId: string, filePath: string): string {
  return `cache_${repoId}_${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`;
}

function loadCache(repoId: string, filePath: string): CacheEntry | null {
  if (!config.scan.cacheEnabled) return null;
  const key = getCacheKey(repoId, filePath);
  return readJson<CacheEntry | null>(join(DATA_DIR, 'cache', `${key}.json`), null);
}

function saveCache(repoId: string, filePath: string, hash: string, findings: number) {
  if (!config.scan.cacheEnabled) return;
  const key = getCacheKey(repoId, filePath);
  writeJson(join(DATA_DIR, 'cache', `${key}.json`), { hash, findings, scannedAt: new Date().toISOString() });
}

export async function scanRepository(repo: Repository, trigger: 'scheduled' | 'manual' = 'scheduled') {
  const scanId = randomUUID();
  const startedAt = Date.now();
  const startedAtIso = new Date().toISOString();

  const scanRun: ScanRun = {
    id: scanId,
    repoId: repo.id,
    status: 'running',
    trigger,
    startedAt: startedAtIso,
    completedAt: null,
    filesScanned: 0,
    findingsCritical: 0,
    findingsHigh: 0,
    findingsMedium: 0,
    findingsInfo: 0,
    llmProvidersUsed: [],
    errorMessage: null,
  };

  saveScanRun(scanRun);
  logAudit('scan_repo_started', 'info', `Scan started: ${repo.name}`, { scanId, repoId: repo.id });

  try {
    if (!checkGitInstalled()) throw new Error('Git is not installed or not in PATH');

    // Phase 1: Extract candidates
    let candidates: Candidate[] = [];
    let tempDir: string | null = null;

    if (repo.type === 'github' || repo.type === 'gitlab') {
      const source = repo.type === 'github' ? await cloneGithubRepo(repo) : repo.pathOrUrl;
      tempDir = source;
      candidates = await extractCandidates(source);
    } else {
      candidates = await extractCandidates(repo.pathOrUrl);
    }
    if (tempDir) cleanupTempRepo(tempDir);

    // Filter: skip unchanged files (cache)
    if (config.scan.cacheEnabled) {
      const filtered: Candidate[] = [];
      for (const c of candidates) {
        const hash = createHash('md5').update(c.snippet + c.filePath).digest('hex');
        const cache = loadCache(repo.id, c.filePath);
        if (cache && cache.hash === hash) continue; // unchanged, skip
        filtered.push(c);
        saveCache(repo.id, c.filePath, hash, 0);
      }
      if (filtered.length < candidates.length) {
        logAudit('scan_cache', 'info', `Cache hit: ${candidates.length - filtered.length} unchanged files skipped`);
      }
      candidates = filtered;
    }

    // Entropy pre-filter
    const entropyFiltered = candidates.filter(c => isHighEntropy(c.snippet));
    if (entropyFiltered.length < candidates.length) {
      logAudit('scan_entropy', 'info', `Entropy filter: ${candidates.length - entropyFiltered.length} low-entropy skipped`);
    }
    candidates = entropyFiltered;

    // Truncate
    if (candidates.length > MAX_CANDIDATES) {
      candidates = candidates.slice(0, MAX_CANDIDATES);
    }

    scanRun.filesScanned = new Set(candidates.map(c => c.filePath)).size;

    // Phase 2: Tiered LLM
    let findings: Finding[] = [];
    let providersUsed: LlmProvider[] = [];
    let totalTokens = 0;

    if (candidates.length > 0 && config.scan.tieredLLM) {
      // Tier 1: Light LLM (fast, cheap)
      const lightProviders = config.scan.lightProviders.filter(p => {
        const cfg = config.llm[p as keyof typeof config.llm] as { apiKey: string } | undefined;
        return p === 'ollama' || cfg?.apiKey;
      });
      if (lightProviders.length > 0) {
        const orig = config.llm.providers;
        config.llm.providers = lightProviders;
        try {
          const batchResults = await analyzeInBatches(candidates, config.scan.batchSize);
          findings.push(...batchResults.findings.map((f, idx) => mapFinding(f, idx, scanId, repo.id, batchResults.providersUsed)));
          providersUsed.push(...batchResults.providersUsed);
          totalTokens += batchResults.totalTokens;
        } catch (err) {
          logAudit('llm_tier1_error', 'warn', `Tier 1 LLM failed: ${err instanceof Error ? err.message : String(err)}`);
        }
        config.llm.providers = orig;
      }

      // Tier 2: Heavy LLM for unresolved candidates
      const unresolved = candidates.filter(c => !findings.some(f => f.filePath === c.filePath && f.line === c.lineNumber));
      if (unresolved.length > 0) {
        const heavyProviders = config.scan.heavyProviders.filter(p => {
          const cfg = config.llm[p as keyof typeof config.llm] as { apiKey: string } | undefined;
          return p === 'ollama' || (cfg?.apiKey && !cfg.apiKey.startsWith('sk-your-'));
        });
        if (heavyProviders.length > 0) {
          const orig = config.llm.providers;
          config.llm.providers = heavyProviders;
          try {
            const batchResults = await analyzeInBatches(unresolved, config.scan.batchSize);
            findings.push(...batchResults.findings.map((f, idx) => mapFinding(f, idx + 1000, scanId, repo.id, batchResults.providersUsed)));
            providersUsed.push(...batchResults.providersUsed);
            totalTokens += batchResults.totalTokens;
          } catch (err) {
            logAudit('llm_tier2_error', 'warn', `Tier 2 LLM failed: ${err instanceof Error ? err.message : String(err)}`);
          }
          config.llm.providers = orig;
        }
      }
    } else if (candidates.length > 0) {
      try {
        const result = await analyzeCandidates(candidates);
        findings = result.findings.map((f, idx) => mapFinding(f, idx, scanId, repo.id, result.providersUsed));
        providersUsed = result.providersUsed;
        totalTokens = result.totalTokens;
      } catch (llmErr) {
        logAudit('llm_error', 'error', `LLM analysis failed: ${llmErr instanceof Error ? llmErr.message : String(llmErr)}`);
      }
    }

    // Phase 3: Context risk adjustment
    for (const f of findings) {
      const risk = classifyContextRisk(f.filePath);
      if (risk === 'low' && f.severity !== 'critical') f.severity = 'info';
    }

    // Deduplicate by fingerprint
    const seen = new Set<string>();
    findings = findings.filter(f => {
      const k = `${f.filePath}:${f.maskedFingerprint}`;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });

    // Save & alert
    if (findings.length > 0) {
      saveFindings(findings);
      logAudit('finding_detected', findings.some(f => f.severity === 'critical') ? 'warn' : 'info',
        `${findings.length} findings (${findings.filter(f => f.severity === 'critical').length} critical)`);
      for (const f of findings) {
        if (f.severity === 'critical' || f.severity === 'high') emitSse('finding:new', f);
      }
    }
    await sendAlerts(repo, findings);

    // Metrics
    const elapsedMs = Date.now() - startedAt;
    logAudit('scan_metrics', 'info', `Scan metrics: ${elapsedMs}ms, ${findings.length} findings, ${totalTokens} tokens, ${providersUsed.join(',')}`, {
      scanId, elapsedMs, findingsCount: findings.length, tokens: totalTokens, providers: providersUsed,
    });

    scanRun.status = 'completed';
    scanRun.completedAt = new Date().toISOString();
    scanRun.findingsCritical = findings.filter(f => f.severity === 'critical').length;
    scanRun.findingsHigh = findings.filter(f => f.severity === 'high').length;
    scanRun.findingsMedium = findings.filter(f => f.severity === 'medium').length;
    scanRun.findingsInfo = findings.filter(f => f.severity === 'info').length;
    scanRun.llmProvidersUsed = providersUsed;
    saveScanRun(scanRun);

  } catch (err) {
    scanRun.status = 'failed';
    scanRun.errorMessage = err instanceof Error ? err.message : String(err);
    scanRun.completedAt = new Date().toISOString();
    saveScanRun(scanRun);
    logAudit('scan_error', 'error', `Scan failed: ${repo.name}`, { scanId, error: scanRun.errorMessage });
  }

  return scanRun;
}

function mapFinding(f: { file: string; line: number | null; provider: string; secretType: string; maskedFingerprint: string; confidence: string; severity: string; isPlaceholder: boolean; evidenceNote: string; remediation: string }, idx: number, scanId: string, repoId: string, providers: LlmProvider[]): Finding {
  return {
    id: `F-${scanId.slice(0, 8)}-${String(idx + 1).padStart(3, '0')}`,
    scanId,
    repoId,
    filePath: f.file,
    line: f.line,
    provider: f.provider as Finding['provider'],
    secretType: f.secretType,
    maskedFingerprint: f.maskedFingerprint,
    confidence: f.confidence as Finding['confidence'],
    severity: f.severity as Finding['severity'],
    isPlaceholder: f.isPlaceholder,
    evidenceNote: f.evidenceNote,
    remediation: f.remediation,
    acknowledged: false,
    acknowledgedAt: null,
    acknowledgedNote: null,
    detectedAt: new Date().toISOString(),
    llmSources: providers,
  };
}

async function analyzeInBatches(candidates: Candidate[], batchSize: number) {
  let allFindings: Array<{ file: string; line: number | null; provider: string; secretType: string; maskedFingerprint: string; confidence: string; severity: string; isPlaceholder: boolean; evidenceNote: string; remediation: string }> = [];
  let allProviders: LlmProvider[] = [];
  let totalTokens = 0;

  for (let i = 0; i < candidates.length; i += batchSize) {
    const batch = candidates.slice(i, i + batchSize);
    const result = await analyzeCandidates(batch);
    allFindings.push(...result.findings);
    for (const p of result.providersUsed) if (!allProviders.includes(p)) allProviders.push(p);
    totalTokens += result.totalTokens;
  }

  return { findings: allFindings, providersUsed: allProviders, totalTokens };
}
