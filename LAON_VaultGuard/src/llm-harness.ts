// llm-harness.ts — multi-LLM secret scanning harness

import OpenAI from 'openai';
import type { Candidate, LlmScanResult, LlmProvider } from './types.js';
import { config } from './config.js';
import { logAudit } from './db.js';
import { maskCandidates, summarizeMasking } from './differential-privacy.js';

// ── System Prompt (abbreviated — full version in docs/LLM_Prompt.md) ──

const SYSTEM_PROMPT = `You are SecretSentinel, a read-only pre-publication secret-scanning auditor. Your sole job is to find hardcoded credentials, keys, tokens, and other secrets, and to report them WITHOUT EVER REPRODUCING THE SECRET VALUE.

<hard_safety_rules>
1. NEVER output a secret in cleartext. Emit ONLY a masked fingerprint: first 4 and last 2 chars with "…" between. If ≤12 chars, output "[REDACTED]".
2. NEVER reconstruct, decode, de-base64, decrypt, or show the full value.
3. NEVER write the secret into JSON output, code blocks, regex echo, or context snippets.
4. NEVER call tools, open URLs, or verify keys. You are read-only and offline.
5. If unsure whether a string is a secret, FLAG IT (prefer false positives), but still mask it.
6. Output ONLY the JSON object defined below. No preamble, no markdown, no commentary.
</hard_safety_rules>

Detect secrets for: AWS (AKIA/ASIA keys, secret keys), Azure (client secrets, storage keys, SAS tokens, connection strings), GCP (service account JSON keys, API keys with AIza prefix), KT Cloud (S3-compatible access/secret keys at ktcloud.com/ucloudbiz endpoints, OpenStack credentials), NAVER Cloud/NCP (access/secret keys, API gateway keys, SENS keys at ncloud.com endpoints), and Generic (private keys BEGIN/END blocks, GitHub tokens ghp_/gho_/ghs_, Slack tokens xox[baprs]-, JWT tokens, DB connection strings, hardcoded passwords).

For each finding, provide confidence (high/medium/low) and severity:
- critical: verified-shape provider keys (AWS AKIA, GCP service_account, Azure AccountKey, NCP/KT access+secret pairs)
- high: high-entropy matches with provider indicators
- medium: suspicious but ambiguous
- info: placeholders, test fixtures (is_placeholder=true)

Return ONLY this JSON object:
{
  "scanSummary": { "filesScanned": 0, "findingsCount": 0, "critical": 0, "high": 0, "medium": 0, "info": 0, "publishRecommendation": "PASS" },
  "findings": [
    {
      "id": "F-001",
      "file": "relative/path",
      "line": 42,
      "provider": "AWS",
      "secretType": "AWS Access Key ID",
      "maskedFingerprint": "AKIA…7Q",
      "confidence": "high",
      "severity": "critical",
      "isPlaceholder": false,
      "evidenceNote": "AKIA prefix + high entropy near aws_access_key_id identifier",
      "remediation": "1) Rotate/revoke immediately. 2) Move to secrets manager. 3) Purge from git history."
    }
  ],
  "notes": ""
}`;

// ── Provider Configs ──

interface ProviderConfig {
  name: LlmProvider;
  apiKey: string;
  baseUrl: string;
  model: string;
}

function getProviders(): ProviderConfig[] {
  const providers: ProviderConfig[] = [];
  const enabled = config.llm.providers;

  for (const name of enabled) {
    const c = config.llm[name as keyof typeof config.llm] as {
      apiKey: string;
      baseUrl: string;
      model: string;
    };
    if (c?.apiKey) {
      providers.push({ name: name as LlmProvider, ...c });
    }
  }
  return providers;
}

// ── Core ──

function buildUserPrompt(candidates: Candidate[]): string {
  const lines = candidates.map(c =>
    `FILE: ${c.filePath}:${c.lineNumber}\n${c.snippet}`
  );
  return `Scan the following candidate lines extracted from git diff:\n\n${lines.join('\n\n')}`;
}

function sanitizeResponse(text: string): string {
  // strip markdown code fences if present
  let cleaned = text.trim();
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```(?:json)?\s*\n?/, '').replace(/\n?```$/, '');
  }
  return cleaned.trim();
}

function maskSecretInLog(text: string): string {
  // aggressive masking for log safety — replace high-entropy patterns
  return text
    .replace(/[A-Za-z0-9+/]{20,}={0,2}/g, '[MASKED_B64]')
    .replace(/ghp_[A-Za-z0-9]{36,}/g, '[MASKED_GH_TOKEN]')
    .replace(/sk-[A-Za-z0-9]{32,}/g, '[MASKED_OPENAI_KEY]')
    .replace(/xox[baprs]-[A-Za-z0-9-]{10,}/g, '[MASKED_SLACK]');
}

function validateLlmScanResult(v: unknown): v is LlmScanResult {
  if (!v || typeof v !== 'object') return false;
  const r = v as Partial<LlmScanResult>;
  if (!r.scanSummary || typeof r.scanSummary !== 'object') return false;
  const s = r.scanSummary;
  if (!Array.isArray(r.findings)) return false;
  if (typeof s.filesScanned !== 'number') return false;
  if (typeof s.findingsCount !== 'number') return false;
  if (!['BLOCK', 'REVIEW', 'PASS'].includes(s.publishRecommendation as string)) return false;
  for (const f of r.findings) {
    if (!f || typeof f !== 'object') return false;
    if (typeof f.file !== 'string') return false;
    if (typeof f.maskedFingerprint !== 'string') return false;
    if (typeof f.provider !== 'string') return false;
  }
  return true;
}

function containsCleartextSecret(llmOutput: string, candidates: Candidate[]): boolean {
  for (const c of candidates) {
    const snippet = c.snippet.trim();
    if (snippet.length < 16) continue;
    if (llmOutput.includes(snippet)) return true;
  }
  return false;
}

async function callSingleLLM(
  provider: ProviderConfig,
  candidates: Candidate[],
): Promise<{ provider: LlmProvider; result: LlmScanResult; tokensUsed: number }> {
  const client = new OpenAI({
    apiKey: provider.apiKey,
    baseURL: provider.baseUrl,
    timeout: config.scan.timeoutMs,
    maxRetries: 3,
  });

  // ── Differential Privacy: mask actual secret values before LLM ──
  const dpEnabled = process.env.DP_ENABLED !== 'false'; // enabled by default
  const maskedCands = dpEnabled ? maskCandidates(candidates) : candidates;

  if (dpEnabled) {
    const summary = summarizeMasking(maskedCands as ReturnType<typeof maskCandidates>);
    if (summary.masked > 0) {
      logAudit('dp_masking', 'info',
        `DP masked ${summary.masked}/${summary.total} candidates (${summary.replacements} secrets)`,
        { replaced: summary.replacements, rules: Object.fromEntries(summary.rules) },
      );
    }
  }

  const feedToLLM: Candidate[] = dpEnabled
    ? (maskedCands as ReturnType<typeof maskCandidates>).map(m => ({
      filePath: m.filePath, lineNumber: m.lineNumber,
      snippet: m.snippet, matchedPattern: m.matchedPattern,
    })) as Candidate[]
    : candidates;

  const userPrompt = buildUserPrompt(feedToLLM);
  const startTime = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.scan.timeoutMs);

  try {
    const response = await client.chat.completions.create({
      model: provider.model,
      temperature: 0,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userPrompt },
      ],
      max_tokens: 4096,
    }, { signal: controller.signal });

    clearTimeout(timeoutId);

    const elapsed = Date.now() - startTime;
    const content = response.choices[0]?.message?.content || '';
    const tokensUsed = response.usage?.total_tokens || 0;

    logAudit('llm_call', 'info',
      `LLM call: ${provider.name} (${provider.model}) — ${elapsed}ms, ${tokensUsed} tokens`,
      { provider: provider.name, model: provider.model, tokens: tokensUsed, elapsedMs: elapsed },
    );

    const sanitized = sanitizeResponse(content);
    let result: LlmScanResult;
    try {
      result = JSON.parse(sanitized) as LlmScanResult;
    } catch {
      logAudit('llm_parse_error', 'error', `Failed to parse LLM response: ${sanitized.slice(0, 200)}`);
      throw new Error('LLM returned invalid JSON');
    }

    if (!validateLlmScanResult(result)) {
      logAudit('llm_schema_error', 'error', 'LLM response failed schema validation');
      throw new Error('LLM response failed schema validation');
    }
    if (containsCleartextSecret(JSON.stringify(result), candidates)) {
      logAudit('llm_secret_leak', 'error', 'LLM response contains cleartext secret', { provider: provider.name });
      throw new Error('LLM response leaked a cleartext secret');
    }

    result.scanSummary.filesScanned = candidates.length;

    return { provider: provider.name, result, tokensUsed };
  } catch (err) {
    clearTimeout(timeoutId);
    const msg = err instanceof Error ? err.message : String(err);

    if (msg.includes('aborted') || msg.includes('timeout') || msg.includes('ETIMEDOUT')) {
      throw new Error(`LLM timeout: ${provider.name} exceeded ${config.scan.timeoutMs}ms`);
    }
    if (msg.includes('429') || msg.includes('rate') || msg.includes('quota')) {
      logAudit('llm_quota', 'warn', `LLM quota exceeded: ${provider.name}`, { provider: provider.name });
      throw new Error(`LLM quota exceeded: ${provider.name}`);
    }
    if (msg.includes('401') || msg.includes('403') || msg.includes('auth')) {
      throw new Error(`LLM auth failed: ${provider.name} — check API key`);
    }
    throw err;
  }
}

// ── Multi-LLM Modes ──

export async function analyzeCandidates(
  candidates: Candidate[],
): Promise<{ findings: LlmScanResult['findings']; providersUsed: LlmProvider[]; totalTokens: number }> {
  if (candidates.length === 0) {
    return { findings: [], providersUsed: [], totalTokens: 0 };
  }

  const providers = getProviders();
  if (providers.length === 0) {
    logAudit('llm_error', 'error', 'No LLM providers configured');
    return { findings: [], providersUsed: [], totalTokens: 0 };
  }

  const mode = config.llm.mode;

  if (mode === 'parallel') {
    return await parallelAnalysis(providers, candidates);
  } else if (mode === 'sequential') {
    return await sequentialAnalysis(providers, candidates);
  } else {
    return await majorityAnalysis(providers, candidates);
  }
}

async function parallelAnalysis(
  providers: ProviderConfig[],
  candidates: Candidate[],
) {
  const results = await Promise.allSettled(
    providers.map(p => callSingleLLM(p, candidates)),
  );

  const allFindings: LlmScanResult['findings'] = [];
  const providersUsed: LlmProvider[] = [];
  let totalTokens = 0;

  for (const r of results) {
    if (r.status === 'fulfilled') {
      allFindings.push(...r.value.result.findings);
      providersUsed.push(r.value.provider);
      totalTokens += r.value.tokensUsed;
    } else {
      logAudit('llm_error', 'error', `LLM call failed: ${r.reason}`);
    }
  }

  // deduplicate by masked fingerprint within same file
  const deduped = deduplicateFindings(allFindings);
  return { findings: deduped, providersUsed, totalTokens };
}

async function sequentialAnalysis(
  providers: ProviderConfig[],
  candidates: Candidate[],
): Promise<{ findings: LlmScanResult['findings']; providersUsed: LlmProvider[]; totalTokens: number }> {
  let totalTokens = 0;

  for (const provider of providers) {
    try {
      const { result, tokensUsed } = await callSingleLLM(provider, candidates);
      totalTokens += tokensUsed;

      // use first result and return (fallback only needed on failure)
      return {
        findings: result.findings,
        providersUsed: [provider.name],
        totalTokens,
      };
    } catch (err) {
      logAudit('llm_fallback', 'warn',
        `LLM ${provider.name} failed, trying next provider: ${err instanceof Error ? err.message : String(err)}`,
        { provider: provider.name },
      );
      // continue to next provider
    }
  }

  logAudit('llm_error', 'error', 'All LLM providers failed');
  return { findings: [], providersUsed: [], totalTokens };
}

async function majorityAnalysis(
  providers: ProviderConfig[],
  candidates: Candidate[],
) {
  const results = await Promise.allSettled(
    providers.map(p => callSingleLLM(p, candidates)),
  );

  const allFindings: LlmScanResult['findings'] = [];
  const providersUsed: LlmProvider[] = [];
  let totalTokens = 0;

  for (const r of results) {
    if (r.status === 'fulfilled') {
      allFindings.push(...r.value.result.findings);
      providersUsed.push(r.value.provider);
      totalTokens += r.value.tokensUsed;
    }
  }

  // majority: only keep findings reported by >50% of responding providers
  const threshold = Math.ceil(providersUsed.length / 2);
  const countMap = new Map<string, number>();
  for (const f of allFindings) {
    const key = `${f.file}:${f.maskedFingerprint}`;
    countMap.set(key, (countMap.get(key) || 0) + 1);
  }

  const majority = allFindings.filter(f => {
    const key = `${f.file}:${f.maskedFingerprint}`;
    return (countMap.get(key) || 0) >= threshold;
  });

  const deduped = deduplicateFindings(majority);
  return { findings: deduped, providersUsed, totalTokens };
}

function deduplicateFindings(findings: LlmScanResult['findings']): LlmScanResult['findings'] {
  const seen = new Set<string>();
  const unique: LlmScanResult['findings'] = [];

  for (const f of findings) {
    const key = `${f.file}:${f.line}:${f.maskedFingerprint}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(f);
    }
  }
  return unique;
}

// ── Cost Estimation (utility) ──

export function estimateCost(provider: LlmProvider, tokensUsed: number): number {
  // rough per-1M-token costs in USD (2026 estimates)
  const rates: Record<string, number> = {
    openai: 2.50,    // gpt-4o input
    deepseek: 0.14,  // deepseek-chat
    minimax: 1.00,   // abab6.5s
    mimo: 0.50,
    ollama: 0,       // local — free
  };
  return (tokensUsed / 1_000_000) * (rates[provider] || 1);
}
