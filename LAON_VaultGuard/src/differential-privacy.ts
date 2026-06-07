// differential-privacy.ts — secret masking pre-processor for LLM transmission
//
// Masks actual secret values in code snippets before sending to the LLM.
// Preserves first 4 + last 2 characters for fingerprinting context.
// Prevents: LLM accidentally reproducing secrets, prompt injection via secret values.
//
// Integration: called from llm-harness.ts before buildUserPrompt()

import type { Candidate } from './types.js';

// ── masking patterns (regex + replacement) ──

interface MaskRule {
  name: string;
  pattern: RegExp;
  replace: (...args: string[]) => string;
}

const MASK_RULES: MaskRule[] = [
  // AWS Access Key IDs (AKIA/ASIA followed by 16 alphanumeric)
  {
    name: 'AWS Access Key',
    pattern: /\b(A[KS]IA[0-9A-Z]{16})\b/g,
    replace: m => m.slice(0, 6) + '…' + m.slice(-4),
  },
  // AWS Secret Access Keys (40-char base64ish)
  {
    name: 'AWS Secret Key',
    pattern: /\b(?<![A-Z0-9])([A-Za-z0-9+/]{40})(?![A-Za-z0-9])\b/g,
    replace: m => '[MASKED:AWS_SecretKey]',
  },
  // GCP API keys (AIza followed by 35 chars)
  {
    name: 'GCP API Key',
    pattern: /\b(AIza[0-9A-Za-z\-_]{35})\b/g,
    replace: m => m.slice(0, 8) + '…' + m.slice(-4),
  },
  // GCP service account JSON private_key_id
  {
    name: 'GCP Private Key ID',
    pattern: /("private_key_id"\s*:\s*)"([a-f0-9]{40})"/gi,
    replace: (_match: string, prefix: string, id: string) => `${prefix}"${id.slice(0, 4)}…${id.slice(-4)}"`,
  },
  // GitHub tokens (ghp_, gho_, ghs_, github_pat_)
  {
    name: 'GitHub Token',
    pattern: /\b((?:gh[po]_|ghs_|github_pat_)[A-Za-z0-9_]{22,})\b/g,
    replace: m => m.slice(0, 8) + '…' + m.slice(-4),
  },
  // OpenAI/DeepSeek API keys (sk-...)
  {
    name: 'OpenAI/LLM Key',
    pattern: /\b(sk-(?:ant-)?[A-Za-z0-9]{32,})\b/g,
    replace: m => m.slice(0, 7) + '…' + m.slice(-4),
  },
  // Slack tokens (xox[baprs]-...)
  {
    name: 'Slack Token',
    pattern: /\b(xox[baprs]-[A-Za-z0-9-]{10,})\b/g,
    replace: m => m.slice(0, 8) + '…' + m.slice(-4),
  },
  // JWT tokens (eyJ...)
  {
    name: 'JWT Token',
    pattern: /\b(eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})\b/g,
    replace: () => '[MASKED:JWT]',
  },
  // Private key blocks (PEM format)
  {
    name: 'Private Key',
    pattern: /(-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)/gm,
    replace: () => '[MASKED:PrivateKey]',
  },
  // Hardcoded passwords (key=value patterns)
  {
    name: 'Password',
    pattern: /((?:password|passwd|pwd|secret|SECRET)\s*[:=]\s*['"]?)([^'";\s]{16,})(['"]?)/gi,
    replace: (_match: string, prefix: string, val: string, suffix: string) => `${prefix}[MASKED:Password:${val.length}chars]${suffix}`,
  },
  // Connection strings (mongodb://, mysql://, postgres://, redis://)
  {
    name: 'Connection String',
    pattern: /\b((?:mongodb|mysql|postgres|postgresql|redis|sqlite)(?:\+srv)?:\/\/[^:]+):([^@]+)(@)/gi,
    replace: (_match: string, prefix: string, _password: string, suffix: string) => `${prefix}:[MASKED_DB_PASS]${suffix}`,
  },
  // Bearer tokens
  {
    name: 'Bearer Token',
    pattern: /(Bearer\s+)([A-Za-z0-9\-._~+/]{20,}=*)/g,
    replace: (_match: string, prefix: string, token: string) => `${prefix}${token.slice(0, 8)}…${token.slice(-4)}`,
  },
  // NCP / KT Cloud access/secret keys
  {
    name: 'NCP/KT Key',
    pattern: /\b(NCP_(?:ACCESS|SECRET)_KEY\s*=\s*)([A-Za-z0-9]{20,})\b/gi,
    replace: (_match: string, prefix: string, key: string) => `${prefix}${key.slice(0, 4)}…${key.slice(-4)}`,
  },
  // Base64 blobs (long, high entropy) — catch-all
  {
    name: 'Base64 Blob',
    pattern: /\b([A-Za-z0-9+/]{40,}={0,2})\b/g,
    replace: m => m.length > 50 ? `[MASKED:Base64:${m.length}chars]` : m.slice(0, 6) + '…' + m.slice(-4),
  },
];

// ── core masking function ──

export interface MaskReport {
  original: string;
  masked: string;
  rulesTriggered: { rule: string; count: number }[];
  totalReplacements: number;
}

export function maskSecrets(text: string): MaskReport {
  let masked = text;
  const rulesTriggered: { rule: string; count: number }[] = [];
  let totalReplacements = 0;

  for (const rule of MASK_RULES) {
    let count = 0;
    // reset regex lastIndex for global patterns
    rule.pattern.lastIndex = 0;
    masked = masked.replace(rule.pattern, (...args) => {
      count++;
      return rule.replace(args[0]);
    });
    if (count > 0) {
      rulesTriggered.push({ rule: rule.name, count });
      totalReplacements += count;
    }
  }

  return { original: text, masked, rulesTriggered, totalReplacements };
}

// ── candidate-level: mask snippets before LLM transmission ──

export function maskCandidate(candidate: Candidate): Candidate & { wasMasked: boolean; maskReport: MaskReport } {
  const report = maskSecrets(candidate.snippet);
  return {
    ...candidate,
    snippet: report.masked,
    wasMasked: report.totalReplacements > 0,
    maskReport: report,
  };
}

export function maskCandidates(candidates: Candidate[]): (Candidate & { wasMasked: boolean; maskReport: MaskReport })[] {
  return candidates.map(c => maskCandidate(c));
}

// ── audit log helper ──

export function summarizeMasking(maskedCandidates: (Candidate & { wasMasked: boolean; maskReport: MaskReport })[]): {
  total: number;
  masked: number;
  replacements: number;
  rules: Map<string, number>;
} {
  const rules = new Map<string, number>();
  let maskedCount = 0;
  let totalReplacements = 0;

  for (const c of maskedCandidates) {
    if (c.wasMasked) {
      maskedCount++;
      totalReplacements += c.maskReport.totalReplacements;
      for (const r of c.maskReport.rulesTriggered) {
        rules.set(r.rule, (rules.get(r.rule) || 0) + r.count);
      }
    }
  }

  return { total: maskedCandidates.length, masked: maskedCount, replacements: totalReplacements, rules };
}
