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

### Phase 1: 코어 엔진 (1~2주)

- [ ] `tsconfig.json`, `package.json`, `esbuild` 설정
- [ ] `config.ts` — .env 로드
- [ ] `types.ts` — 인터페이스 정의
- [ ] `db.ts` — better-sqlite3 초기화 + 마이그레이션
- [ ] `git-monitor.ts` — 로컬 레포 git log/diff 수집
- [ ] `diff-extractor.ts` — 변경 파일·라인 추출
- [ ] `candidate-filter.ts` — git grep 필터
- [ ] `llm-harness.ts` — 단일 LLM 연동 (OpenAI 우선)
- [ ] `scheduler.ts` — node-cron 등록

### Phase 2: 알람 + 대시보드 (1주)

- [ ] `routes/api.ts` — REST API
- [ ] `public/index.html` + SSE 실시간 업데이트
- [ ] `alert-engine.ts` — Telegram 봇 연동

### Phase 3: 멀티 LLM + 확장 (1주)

- [ ] 멀티 LLM 병렬 호출 (DeepSeek, MiniMax 추가)
- [ ] 다수결 엔진
- [ ] Slack 알람
- [ ] 이메일 리포트

### Phase 4: 완성도 (1~2주)

- [ ] GitHub/GitLab API 원격 레포 지원
- [ ] 크로스플랫폼 검증 (macOS, Linux, Windows)
- [ ] 단위 테스트 작성 (vitest)
- [ ] README / 가이드 문서 완성

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
