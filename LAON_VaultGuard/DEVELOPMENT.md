# LAON VaultGuard — 개발 가이드

> 🇰🇷 LAON VaultGuard 개발 환경 설정 및 단계별 구현 계획.
> 🇺🇸 Development environment setup and phased implementation plan.
> 🇨🇳 开发环境设置和分阶段实施计划。

> TypeScript · Node.js 기반. LLM을 활용한 비공개 키 감시 자동화 도구.

## 1. 개발 환경 설정

### 필수 조건

- Node.js ≥18
- npm ≥9
- Git (macOS: `brew install git`, Linux: `apt install git`, Windows: WSL + `apt install git`)

### 설치

```bash
git clone https://github.com/gameworkerkim/vibe-investing.git
cd vibe-investing/LAON_VaultGuard
npm install
cp .env.example .env
```

### .env 구성

```bash
# ─── 서버 ───
PORT=3101
HOST=0.0.0.0           # 같은 네트워크 팀 접근 허용 (로컬 전용 시 127.0.0.1)

# ─── LLM API 키 (최소 1개 필수, 여러 개 병렬 사용 가능) ───
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
MINIMAX_API_KEY=...
MIMO_API_KEY=...

# 각 LLM 기본 URL (OpenAI 호환)
# OPENAI_BASE_URL=https://api.openai.com/v1
# DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
# MINIMAX_BASE_URL=https://api.minimaxi.com/v1
# MIMO_BASE_URL=...

# 사용할 LLM 목록 (쉼표 구분, 우선순위 순)
LLM_PROVIDERS=openai,deepseek,minimax

# LLM 호출 방식: "parallel" (동시) | "sequential" (순차) | "majority" (과반수)
LLM_MODE=parallel

# ─── Git(GitHub/GitLab) ───
# GitHub Personal Access Token (private repo 접근 시 필요)
GITHUB_TOKEN=ghp_...
# GitLab Personal Access Token
GITLAB_TOKEN=glpat-...

# ─── 알람 ───
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TELEGRAM_BOT_TOKEN=123:abc
TELEGRAM_CHAT_ID=-456
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=...
EMAIL_PASS=...

# ─── 스캔 스케줄 (cron 표현식) ───
SCAN_CRON=0 */6 * * *     # 6시간마다 (기본값)

# ─── DB ───
DB_PATH=./data/vaultguard.db
```

### 스크립트

```bash
npm run build        # TypeScript 컴파일 (esbuild)
npm run dev          # 개발 모드 (tsx --watch)
npm start            # 프로덕션 실행
npm test             # vitest
npm run lint         # eslint
npm run typecheck    # tsc --noEmit
```

## 2. 프로젝트 구조

```
LAON_VaultGuard/
├── src/
│   ├── index.ts           ← Express 서버 + 스케줄러 시작
│   ├── config.ts          ← .env 로드 + 설정 객체
│   ├── scheduler.ts       ← node-cron 기반 주기적 스캔 트리거
│   ├── git-monitor.ts     ← 로컬/원격 레포 변경 감지
│   ├── diff-extractor.ts  ← git diff 추출 (변경된 파일+라인)
│   ├── candidate-filter.ts← 1차 git grep → 의심 라인 추출
│   ├── llm-harness.ts     ← 멀티 LLM 호출 + 안전규칙 적용
│   ├── db.ts              ← better-sqlite3 CRUD
│   ├── alert-engine.ts    ← Slack·Telegram·Email·SSE 통보
│   ├── routes/
│   │   └── api.ts         ← Express REST 라우트
│   └── types.ts           ← 공통 인터페이스/타입
├── public/
│   ├── index.html
│   └── dashboard.js
├── tests/
│   ├── candidate-filter.test.ts
│   ├── llm-harness.test.ts
│   └── alert-engine.test.ts
└── data/                  ← .gitignore 대상 (런타임 생성)
    └── vaultguard.db
```

## 3. 핵심 설계 결정

### 3.1 2단계 탐지 파이프라인

**1단계: Candidate Filter (로컬, LLM 호출 전)**

```typescript
// candidate-filter.ts — 의심 키워드가 있는 라인만 추출 (LLM 토큰 최소화)
const SUSPECT_PATTERNS = [
  'AKIA', 'ASIA', 'AIza', '-----BEGIN',
  'client_secret', 'AccountKey=', 'aws_secret',
  'x-ncp', 'ncloud', 'ktcloud', 'ucloudbiz',
  'api_key', 'api-key', 'secret_key', 'secret-key',
  'password', 'token', 'ghp_', 'gho_', 'ghs_',
  'xox[baprs]-', 'github_pat_',
  'NCP_ACCESS_KEY', 'NCP_SECRET_KEY',
  'x-ncp-apigw-api-key', 'x-ncp-iam-access-key',
  'OS_USERNAME', 'OS_PASSWORD',
  'DefaultEndpointsProtocol',
  'service_account', 'private_key_id',
];

// git grep 실행 → 의심 라인 + 파일경로 + 라인번호 수집
// LLM에는 이 결과만 전달 (전체 파일 내용이 아님)
```

**2단계: LLM Harness (문맥 분석)**

```typescript
// llm-harness.ts
interface LLMProvider {
  name: string;
  client: OpenAI;  // OpenAI 호환 클라이언트
  model: string;
}

// parallel 모드: 모든 LLM에 동시 전송 → 결과 병합
// majority 모드: 과반수 동의 시 확정, 아니면 재분석
// sequential 모드: 우선순위 순으로 호출, 첫 high-confidence 결과 사용
```

### 3.2 LLM 안전 규칙 (코드로 강제)

참조: `docs/LLM_Prompt.md`

```typescript
// 절대 원칙 — 코드 레벨에서도 방어
// 1. LLM 응답 파싱 시 masked_fingerprint 외 필드에서 원문 패턴 검사 → 있으면 폐기
// 2. 로그 출력 전 시크릿 마스킹 (정규식 기반)
// 3. LLM에 전송하는 프롬프트에 candidates.txt "내용"만 포함, 절대 전체 파일 내용 전송 금지
// 4. temperature=0 (결정론적 응답)
```

### 3.3 LLM 다수결 로직

```typescript
// result-aggregator.ts (추후 구현)
interface AggregatedResult {
  verdict: 'BLOCK' | 'REVIEW' | 'PASS';
  confidence: number;        // 0~1
  agreeingProviders: number; // 동의한 LLM 수
  totalProviders: number;
  findings: Finding[];       // 모든 LLM 결과 통합 (중복 제거)
}
```

## 4. 개발 단계

### Phase 1: 코어 엔진 (1~2주) ✅ 완료

- [x] `tsconfig.json`, `package.json`, `esbuild` 설정
- [x] `config.ts` — .env 로드 + STORAGE_ENGINE
- [x] `types.ts` — 인터페이스 정의
- [ ] `db.ts` — better-sqlite3 초기화 + 마이그레이션 (→ v0.5)
- [x] `git-monitor.ts` — 로컬 레포 git log/diff 수집
- [x] `diff-extractor.ts` — 변경 파일·라인 추출
- [x] `candidate-filter.ts` — git grep 필터
- [x] `llm-harness.ts` — 단일 LLM 연동 (OpenAI 우선)
- [x] `scheduler.ts` — node-cron 등록

### Phase 2: 알람 + 대시보드 (1주) ✅ 완료

- [x] `routes/api.ts` — REST API
- [x] `public/index.html` + SSE 실시간 업데이트
- [x] `alert-engine.ts` — Telegram 봇 연동

### Phase 3: 멀티 LLM + 확장 (1주) ✅ 완료

- [x] 멀티 LLM 병렬 호출 (DeepSeek, MiniMax 추가)
- [x] 다수결 엔진
- [x] Slack 알람
- [x] 이메일 리포트

### Phase 4: 완성도 (1~2주) ✅ 완료

- [x] GitHub/GitLab API 원격 레포 지원
- [x] 크로스플랫폼 검증 (macOS, Linux, Windows)
- [~] 단위 테스트 작성 (vitest) — 일부 작성됨, v0.5에서 확장
- [x] README / 가이드 문서 완성

### Phase 5: v0.5 — 프로덕션 배포 준비 ✅ 완료

- [x] SQLite 마이그레이션 (`better-sqlite3`, WAL 모드, `npm run migrate`)
- [x] SARIF v2.1.0 결과 내보내기 (`npm run export-sarif`)
- [x] Differential Privacy 전처리 (14개 시크릿 마스킹 룰, `DP_ENABLED`)
- [x] Prometheus `/metrics` 엔드포인트 (counters, gauges, histograms)
- [x] Docker 이미지 (multi-stage Alpine) + docker-compose (app + Ollama 프로필)

### Phase 6: v0.6 — 에코시스템 확장 (계획)

- [ ] VS Code 확장 플러그인
- [ ] 오탐 피드백 루프
- [ ] fine-tuned 모델 평가 파이프라인
- [ ] pre-commit hook 통합 코드

## 5. 테스트 전략

```bash
# 단위 테스트
npm test

# 특정 모듈만
npx vitest run tests/llm-harness.test.ts

# 수동 스캔 트리거로 통합 테스트
curl -X POST http://localhost:3101/api/scan/trigger
```

## 6. 보안 체크리스트 (개발 시)

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가
- [ ] LLM API 키가 로그에 출력되지 않는가
- [ ] LLM 응답 파싱 시 `masked_fingerprint` 외 시크릿 원문이 없는가
- [ ] 대시보드에서 `masked_fingerprint`만 노출되는가
- [ ] `data/vaultguard.db`가 `.gitignore`에 포함되어 있는가
- [ ] 같은 네트워크 접근 시 CORS·인증이 적절한가 (기본: 로컬 전용)
- [ ] 프롬프트 인젝션 방어: LLM에 전송되는 파일 내용이 지시로 해석되지 않도록 격리

## 7. 참고 문서

- [Secret Scanning LLM Harness Prompt](../TechDoc/LLM_Security/Secret%20scanning%20llm%20harness%20prompt.md) — LLM 프롬프트 원본
- [Architecture](./docs/Architecture.md) — 상세 아키텍처
- [API Reference](./docs/API.md) — REST API 명세
- [Database Schema](./docs/Database.md) — DB 테이블 설계
- [AGENTS.md](../AGENTS.md) — 레포 전체 AI 에이전트 가이드

## 8. 개선 필요 사항 (Review)

> 2026-06-07 종합 검토 기반. 우선순위는 **상 / 중 / 하**.

### 8.1 설계적 개선 필요 사항

| # | 항목 | 설명 | 우선순위 |
|---|------|------|----------|
| 1 | **JSON 파일 동시성** | 여러 API 요청 동시에 `findings.json`에 쓰기 발생 시 데이터 손상 위험. 최소한 `writeJson`에 파일 락(`proper-lockfile` 등) 추가 필요 | **상** |
| 2 | **대시보드 인증 부재** | `HOST=0.0.0.0` 시 네트워크 누구나 접근 가능. Architecture.md v0.2 로드맵에도 있으나 미구현 | **상** |
| 3 | **LLM 응답 스키마 검증 부재** | `JSON.parse()` 후 구조만 확인하고 필드 타입/범위 검증이 없음. Zod 또는 JSON Schema로 검증 필요 — LLM 환각 방어의 핵심 | **상** |
| 4 | **알람 기본값이 모두 `false`** | `getAlertConfig()` 기본값이 모든 채널 `false` → `.env`에 알람 설정을 해도 대시보드에서 명시적으로 켜지 않으면 알람이 가지 않음. UX 혼란 | **중** |
| 5 | **LLM 프롬프트 인젝션 방어 미흡** | `buildUserPrompt()`가 파일 내용을 그대로 프롬프트에 삽입. `<user_input>` 태그로 감싸거나 명시적 데이터/지시 구분자가 없음 | **상** |
| 6 | **`candidate-filter.ts` 정규식 과도** | 60개 이상의 패턴을 단일 `git grep -E`로 실행. 일부 패턴(예: `Bearer`, `sk-`)은 지나치게 광범위해 후보 과다 발생 가능. 패턴별 우선순위/가중치 도입 검토 | **중** |
| 7 | **에러 핸들링에 재시도 로직 없음** | LLM 호출 실패 시 `maxRetries: 1`만 있고 exponential backoff 없음. 429(Rate Limit) 발생 시 바로 실패 처리됨 | **중** |

### 8.2 추가 필요 기능

| # | 기능 | 설명 |
|---|------|------|
| 1 | **Docker 이미지** | 엔터프라이즈 배포를 위한 컨테이너화. `HOST=0.0.0.0` 의존 대신 docker-compose로 실행 |
| 2 | **결과 내보내기 (SARIF)** | GitHub Code Scanning, GitLab SAST와 연동되는 SARIF 포맷 출력 |
| 3 | **차등 프라이버시 전처리** | v0.4 로드맵 항목 — LLM에 코드 전송 전 키/토큰 부분만 마스킹하는 전처리 레이어 |
| 4 | **오탐 피드백 루프** | 사용자가 acknowledge/거짓양성 표시한 데이터로 LLM 프롬프트를 동적 개선 (few-shot 예시 추가) |
| 5 | **fine-tuned 모델** | 시크릿 탐지에 특화된 소형 모델 fine-tuning (예: llama3.1을 SecretBench 데이터셋으로 학습 후 Ollama에서 사용) |
| 6 | **pre-commit hook 통합 코드** | README의 4단계 방어선 중 첫 단계지만 실제 `.git/hooks` 설치 코드가 없음 |
| 7 | **Prometheus 메트릭** | 스캔 횟수, 탐지 건수, LLM 토큰 사용량, 지연시간 등을 `/metrics` 엔드포인트로 노출 |
| 8 | **VS Code 확장** | v0.4 로드맵에 있음. 실시간 에디터 내 경고 |
| 9 | **`result-aggregator.ts` 구현** | 본 문서 3.3절에 "추후 구현"으로 남아있는 다수결 로직 모듈 |

## 9. 경쟁 솔루션 대비 단점 및 우선순위 액션

> 2026-06-07 검토. LLM 바이브 코딩 보안 솔루션 카테고리(gitleaks, trufflehog, GitHub Secret Scanning 등) 대비 단점과 보강 방안.

### 9.1 LLM 바이브 코딩 보안 솔루션 대비 단점 및 보강 방안

| 약점 | 설명 | 보강 방안 |
|------|------|-----------|
| **설치 복잡도** | 여러 LLM API 키 + Ollama 설치 + .env 구성 필요. ChatGPT 플러그인식 원클릭 설치 안 됨 | `npx create-laon-vaultguard` 대화형 CLI 설치 마법사 |
| **LLM 지연시간** | API 호출 왕복 + 멀티 LLM 병렬 호출로 수 초~수십 초 소요. regex 스캐너는 밀리초 | 스트리밍 응답 + 후보 청크별 점진적 분석 |
| **정규식 기반보다 낮은 재현율 가능성** | LLM이 놓치는 단순 패턴(예: base64 인코딩 키)도 있음. gitleaks/trufflehog는 100% 재현 | 하이브리드: git grep → LLM → 정규식 fallback 3단계 |
| **비용** | API 호출 비용 발생 (월 수천 건 스캔 시 $10~100). gitleaks는 무료 | Ollama 기본값 + 경량 LLM 우선 사용 + 캐싱으로 비용 최소화 |
| **AST/의미 분석 부재** | 순수 텍스트 기반 grep. 변수 흐름 추적, taint analysis 불가 → SQL injection 탐지의 false positive 높음 | tree-sitter 기반 AST 분석 레이어 추가 (v0.5) |
| **엔터프라이즈 인증/권한 부재** | RBAC, SSO, LDAP 연동 없음. 팀 규모 확장에 한계 | 인증 미들웨어 + PostgreSQL 마이그레이션 |
| **SIEM/SOAR 연동 부재** | Splunk, Elastic, DataDog 등으로 이벤트 전송 불가 | Webhook 표준화 + Syslog 출력 |
| **fine-tuned 모델 없음** | 범용 LLM에 의존 → 시크릿 탐지 도메인 최적화 안 됨. Github Secret Scanning은 자체 학습 모델 사용 | SecretBench 데이터셋으로 llama3.1 fine-tuning |

### 9.2 우선순위 액션 아이템 (Top 5)

> 상태 표기: ✅ 완료 / ⏳ 진행 예정 / ⚠️ 오탐으로 종료

| 순위 | 항목 | 카테고리 | 예상 소요 | 상태 |
|------|------|----------|-----------|------|
| 1 | LLM 응답 JSON Schema 검증 (Zod) + maskedFingerprint 외 원문 재검증 | 보안 버그 | 1~2일 | ✅ 완료 (`llm-harness.ts`에 `validateLlmScanResult()` + `containsCleartextSecret()` 추가) |
| 2 | `LlmProvider` 타입에 `'claude'` 추가 | 타입 버그 | 5분 | ⚠️ **오탐** — `types.ts:10`의 `LlmProvider`는 이미 `'claude'`를 포함 |
| 3 | `writeJson` 파일 락 도입 (`proper-lockfile`) | 동시성 버그 | 반나절 | ⏳ 진행 예정 |
| 4 | 대시보드 기본 인증 (simple token/password) | 보안 설계 | 1일 | ⏳ 진행 예정 |
| 5 | `clearTimeout(0)` → `clearTimeout(timeoutId)` 수정 (timeoutId try 밖으로) | 버그 | 10분 | ✅ 완료 (`controller`+`timeoutId` 호이스트) |
