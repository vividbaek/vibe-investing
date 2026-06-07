#!/usr/bin/env node
// cli.ts — LAON VaultGuard CLI: single-shot scan

import { randomUUID } from 'node:crypto';
import { resolve } from 'node:path';
import 'dotenv/config';
import { checkGitInstalled } from './git-monitor.js';
import { extractCandidates } from './candidate-filter.js';
import { analyzeCandidates } from './llm-harness.js';
import type { Finding, LlmProvider } from './types.js';

function printBanner() {
  console.log(`
╔══════════════════════════════════════════╗
║       🛡 LAON VaultGuard CLI             ║
║  LLM-based Observer for Non-public Keys  ║
╚══════════════════════════════════════════╝
`);
}

function severityEmoji(s: string): string {
  switch (s) {
    case 'critical': return '🔴';
    case 'high': return '🟠';
    case 'medium': return '🟡';
    case 'info': return '🔵';
    default: return '⚪';
  }
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === 'help' || command === '--help' || command === '-h') {
    printHelp();
    process.exit(0);
  }

  if (command === 'scan') {
    const repoPath = args[1];
    if (!repoPath) {
      console.error('❌ 경로를 지정하세요: npx laon-vaultguard scan /path/to/repo');
      process.exit(1);
    }

    const absolutePath = resolve(repoPath);
    await runScan(absolutePath);
  } else if (command === 'version' || command === '--version' || command === '-v') {
    console.log('LAON VaultGuard v0.1.0');
  } else {
    console.error(`알 수 없는 명령어: ${command}`);
    printHelp();
    process.exit(1);
  }
}

async function runScan(repoPath: string) {
  printBanner();

  console.log(`📁 스캔 대상: ${repoPath}\n`);

  // Pre-flight
  if (!checkGitInstalled()) {
    console.error('❌ Git이 설치되어 있지 않거나 PATH에 없습니다.');
    process.exit(1);
  }
  console.log('✅ Git 확인 완료');

  // Phase 1: git grep
  console.log('🔍 1단계: git grep 키워드 필터링...');
  let candidates;
  try {
    candidates = await extractCandidates(repoPath);
  } catch (err) {
    console.error(`❌ git grep 실패: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  console.log(`   → ${candidates.length}개 의심 라인 발견`);

  if (candidates.length === 0) {
    console.log('\n✅ 탐지된 시크릿이 없습니다.');
    process.exit(0);
  }

  // Phase 2: LLM
  console.log('🤖 2단계: LLM 문맥 분석 중...');
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
    console.log(`   → ${result.providersUsed.length}개 LLM 응답 완료 (${result.totalTokens} tokens)`);
  } catch (err) {
    console.error(`❌ LLM 분석 실패: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  // Output
  if (findings.length === 0) {
    console.log('\n✅ 탐지된 시크릿이 없습니다.');
  } else {
    const critical = findings.filter(f => f.severity === 'critical').length;
    const high = findings.filter(f => f.severity === 'high').length;
    console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`🚨 탐지 결과: ${findings.length}건 (critical: ${critical}, high: ${high})`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);

    for (const f of findings) {
      console.log(`${severityEmoji(f.severity)} [${f.severity.toUpperCase()}] ${f.provider} — ${f.secretType}`);
      console.log(`   파일: ${f.filePath}${f.line ? `:${f.line}` : ''}`);
      console.log(`   지문: ${f.maskedFingerprint}`);
      console.log(`   조치: ${f.remediation}`);
      console.log('');
    }
  }

  process.exit(0);
}

function printHelp() {
  console.log(`
LAON VaultGuard CLI — LLM 기반 시크릿 탐지 도구

사용법:
  npx laon-vaultguard scan <경로>     로컬 Git 레포지토리 스캔
  npx laon-vaultguard version         버전 출력
  npx laon-vaultguard help            도움말

예시:
  npx laon-vaultguard scan .
  npx laon-vaultguard scan ~/projects/my-app
  npx laon-vaultguard scan /path/to/repo

환경변수 (.env 또는 export):
  DEEPSEEK_API_KEY=sk-...        DeepSeek API 키 (필수)
  OPENAI_API_KEY=sk-...          OpenAI API 키
  LLM_PROVIDERS=deepseek,openai  사용할 LLM (기본: deepseek)
  LLM_MODE=parallel              parallel | sequential | majority
  SCAN_TIMEOUT_MS=60000          LLM 호출 타임아웃 (ms)
  SCAN_MAX_CANDIDATES=500        최대 의심 라인 수

⚠️  API 키는 .env 파일에 저장하거나 환경변수로 설정하세요.
    .env 파일은 절대 Git에 커밋하지 마세요.
`);
}

main().catch(err => {
  console.error('❌', err instanceof Error ? err.message : String(err));
  process.exit(1);
});
