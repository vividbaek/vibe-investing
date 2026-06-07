# LAON VaultGuard CLI 매뉴얼

> `laon-vaultguard` 명령줄 도구 — GUI 없이 단발성 시크릿 스캔

## 설치

```bash
cd LAON_VaultGuard
npm install
```

전역 설치 (선택):
```bash
npm link           # 현재 디렉토리를 전역 링크
# 이후 어디서나:
laon-vaultguard scan ./my-project
```

## 환경 설정

### .env 파일 (권장)

LAON_VaultGuard 디렉토리에 `.env` 파일 생성:

```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key
LLM_PROVIDERS=deepseek
LLM_MODE=sequential
SCAN_MAX_CANDIDATES=500
SCAN_TIMEOUT_MS=60000
```

### 환경변수

```bash
export DEEPSEEK_API_KEY=sk-your-deepseek-key
```

## 명령어

### scan — 레포지토리 스캔

```bash
# 기본 사용
npx laon-vaultguard scan .
npx laon-vaultguard scan ~/projects/my-app
npx laon-vaultguard scan /absolute/path/to/repo

# npm 스크립트로 실행
npm run scan .

# 전역 설치 시
laon-vaultguard scan .
```

**실행 흐름:**
1. Git 설치 확인
2. `git grep` 으로 의심 키워드 필터링 (AKIA, sk-, ghp_, password= 등 20+ 패턴)
3. LLM에 의심 라인 전송 → 문맥 분석
4. 결과 콘솔 출력

**출력 예시:**
```
╔══════════════════════════════════════════╗
║       🛡 LAON VaultGuard CLI             ║
║  LLM-based Observer for Non-public Keys  ║
╚══════════════════════════════════════════╝

📁 스캔 대상: /Users/dennis/my-project

✅ Git 확인 완료
🔍 1단계: git grep 키워드 필터링...
   → 15개 의심 라인 발견
🤖 2단계: LLM 문맥 분석 중...
   → 1개 LLM 응답 완료 (3200 tokens)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 탐지 결과: 2건 (critical: 1, high: 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 [CRITICAL] AWS — AWS Access Key ID
   파일: src/config.ts:42
   지문: AKIA…7Q
   조치: 1) Rotate/revoke immediately. 2) Move to secrets manager. 3) Purge from git history.

🟠 [HIGH] Generic — Hardcoded Password
   파일: .env.production:8
   지문: [REDACTED]
   조치: 1) Rotate/revoke immediately...
```

### version — 버전 확인

```bash
npx laon-vaultguard version
# → LAON VaultGuard v0.1.1
```

### help — 도움말

```bash
npx laon-vaultguard help
npx laon-vaultguard --help
```

## 환경변수 레퍼런스

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DEEPSEEK_API_KEY` | — | DeepSeek API 키 (필수) |
| `OPENAI_API_KEY` | — | OpenAI API 키 |
| `MINIMAX_API_KEY` | — | MiniMax API 키 |
| `LLM_PROVIDERS` | `deepseek` | 사용할 LLM 목록 (쉼표 구분) |
| `LLM_MODE` | `sequential` | parallel / sequential / majority |
| `SCAN_TIMEOUT_MS` | `60000` | LLM 호출 타임아웃 (ms) |
| `SCAN_MAX_CANDIDATES` | `500` | git grep 최대 결과 수 |

## 에러 케이스

| 에러 | 원인 | 해결 |
|---|---|---|
| `Git이 설치되어 있지 않음` | git 미설치 | `brew install git` |
| `LLM auth failed` | API 키 오류 | `.env`에서 키 확인 |
| `LLM quota exceeded` | API 할당량 초과 | 대기 후 재시도 또는 다른 LLM 사용 |
| `LLM timeout` | 네트워크 지연 | `SCAN_TIMEOUT_MS` 증가 |

## CI/CD 연동

```yaml
# .github/workflows/secret-scan.yml
- name: LAON VaultGuard Scan
  run: |
    cd LAON_VaultGuard && npm install
    npx laon-vaultguard scan $GITHUB_WORKSPACE
  env:
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
```

## 라이선스

MIT
