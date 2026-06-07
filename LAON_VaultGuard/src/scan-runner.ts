// scan-runner.ts — single repository scan pipeline

import { randomUUID } from 'node:crypto';
import type { Repository, ScanRun, Finding, LlmProvider, Candidate } from './types.js';
import { saveScanRun, saveFindings, logAudit } from './db.js';
import { checkGitInstalled } from './git-monitor.js';
import { extractCandidates } from './candidate-filter.js';
import { analyzeCandidates } from './llm-harness.js';
import { emitSse } from './sse.js';
import { sendAlerts } from './alert-engine.js';
import { config } from './config.js';

const MAX_CANDIDATES = config.scan.maxCandidates;

export async function scanRepository(repo: Repository, trigger: 'scheduled' | 'manual' = 'scheduled') {
  const scanId = randomUUID();
  const startedAt = new Date().toISOString();

  const scanRun: ScanRun = {
    id: scanId,
    repoId: repo.id,
    status: 'running',
    trigger,
    startedAt,
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
    // Pre-flight: check git
    if (repo.type === 'local' && !checkGitInstalled()) {
      throw new Error('Git is not installed or not in PATH');
    }

    // Phase 1: Extract candidates via git grep
    let candidates: Candidate[] = [];

    candidates = await extractCandidates(repo.pathOrUrl);

    if (candidates.length > MAX_CANDIDATES) {
      logAudit('scan_truncated', 'warn',
        `Candidates truncated: ${candidates.length} → ${MAX_CANDIDATES} (max)`,
        { scanId, repoId: repo.id },
      );
      candidates = candidates.slice(0, MAX_CANDIDATES);
    }

    scanRun.filesScanned = candidates.length > 0
      ? new Set(candidates.map(c => c.filePath)).size
      : 0;

    // Phase 2: LLM analysis
    let findings: Finding[] = [];
    let providersUsed: LlmProvider[] = [];
    let totalTokens = 0;

    if (candidates.length > 0) {
      try {
        const result = await analyzeCandidates(candidates);
        findings = result.findings.map((f, idx) => ({
          id: `F-${scanId.slice(0, 8)}-${String(idx + 1).padStart(3, '0')}`,
          scanId,
          repoId: repo.id,
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
        providersUsed = result.providersUsed;
        totalTokens = result.totalTokens;
      } catch (llmErr) {
        // LLM errors are non-fatal — log and continue
        logAudit('llm_error', 'error',
          `LLM analysis failed, scan continues without LLM results: ${llmErr instanceof Error ? llmErr.message : String(llmErr)}`,
          { scanId, repoId: repo.id },
        );
      }
    }

    // Phase 3: Save
    if (findings.length > 0) {
      saveFindings(findings);
      logAudit('finding_detected', findings.some(f => f.severity === 'critical') ? 'warn' : 'info',
        `${findings.length} findings (${findings.filter(f => f.severity === 'critical').length} critical)`,
        { scanId, repoId: repo.id },
      );

      for (const f of findings) {
        if (f.severity === 'critical' || f.severity === 'high') {
          emitSse('finding:new', f);
        }
      }
    }

    // Phase 4: Alerts
    await sendAlerts(repo, findings);

    // Update scan run
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
    logAudit('scan_error', 'error', `Scan failed: ${repo.name}`, {
      scanId, repoId: repo.id, error: scanRun.errorMessage,
    });
  }

  return scanRun;
}
