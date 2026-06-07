# LAON VaultGuard

> **LLM-based Automated Observer for Non-public Keys**
>
> 개발자 PC와 팀 환경에서 Git 레포지토리를 정기적으로 감시해 AWS, Azure, GCP, KT Cloud, Naver Cloud 등 클라우드 프라이빗 키가 노출되지 않도록 사전 차단하는 크로스플랫폼 보안 감사 도구.

## 왜 LAON VaultGuard인가

**2026년 6월, Tving의 GitHub 레포에 AWS 액세스 토큰이 하드코딩된 채 공개된 사건**은 단일 실수가 전체 인프라를 위험에 빠뜨릴 수 있음을 다시 한번 보여줬습니다. `gitleaks`, `trufflehog` 같은 정규식 기반 스캐너는 빠르지만 문맥을 이해하지 못합니다. 반면 LLM은 변수명이 평범하거나 조립된 형태의 시크릿도 "의미"로 탐지할 수 있습니다.

하지만 **단일 LLM에만 의존하는 것은 또 다른 단일 장애점**입니다. 모델마다 판단 편향이 있고, API 장애나 할당량 초과 시 탐지 공백이 발생합니다. LAON VaultGuard는 **여러 LLM을 동시에 교차 검증**하는 구조로 설계되었습니다:

- **각 LLM은 서로 다른 보안 페르소나를 형성** — Claude(규율 기반), DeepSeek(고성능·저비용), GPT(체계적), MiniMax(경량·빠름)
- **다수결 모드**로 오탐을 줄이고, **순차 fallback**으로 단일 LLM 장애에도 스캔이 중단되지 않음
- [Gitleaks](https://github.com/gitleaks/gitleaks) (pre-commit) → **LAON VaultGuard** (정기 감사) → [TruffleHog](https://github.com/trufflesecurity/trufflehog) (CI) → GitHub Secret Scanning (push 후) 4단계 방어선의 핵심 축

정규식은 속도를, LLM은 문맥을 담당합니다. **둘을 함께 쓸 때 진짜 안정성이 확보됩니다.**

## 핵심 기능

- **정기 레포 감시** — GitHub, GitLab, 로컬 레포를 cron 기반 스케줄러로 주기적 스캔
- **멀티 LLM 탐지** — OpenAI(ChatGPT), DeepSeek, MiniMax, Mimo 등 여러 LLM을 동시·교차 검증
- **2단계 탐지** — 1차 `git grep` 키워드 필터 → 2차 LLM 문맥 분석으로 거짓양성 최소화
- **웹 대시보드** — 같은 네트워크의 팀이 함께 모니터링 가능한 로컬 웹 UI
- **멀티 알람** — Slack, Telegram, 이메일, 대시보드로 탐지 결과 실시간 통보
- **크로스플랫폼** — macOS 지원 (Linux, Windows 추후)

![대시보드 스크린샷](public/dashboard.png)

## 빠른 시작

```bash
cd LAON_VaultGuard
npm install
cp .env.example .env   # LLM API 키, Slack/Telegram 웹훅 등 설정
npm run build
npm start              # 기본 포트 3101, http://localhost:3101/dashboard
```

## 아키텍처 개요

```
Config (.env)
  ↓
Scheduler (node-cron)
  ↓
Git Monitor (simple-git + GitHub/GitLab API)
  ↓
Diff Extraction (git diff / git log)
  ↓
Candidate Filter (git grep — 1차 키워드 추출)
  ↓
LLM Harness (멀티 LLM — 병렬 or 순차 분석)
  ↓
Result Aggregation (다수결/합의 기반 판정)
  ↓
SQLite Audit DB + Alert Engine (Slack · Telegram · Email · Web)
  ↓
Dashboard (REST API + 정적 프론트)
```

## 기술 스택

| 계층 | 기술 |
|---|---|
| 런타임 | Node.js ≥18, TypeScript |
| 웹 프레임워크 | Express.js |
| DB | SQLite (`better-sqlite3`) |
| Git 연동 | `simple-git`, `@octokit/rest` (GitHub), `@gitbeaker/rest` (GitLab) |
| 스케줄러 | `node-cron` |
| LLM | OpenAI SDK (ChatGPT, DeepSeek, MiniMax, Mimo — OpenAI 호환 API) |
| 알람 | Slack Webhook, Telegram Bot API, Nodemailer |
| 프론트 | Vanilla HTML/JS + Server-Sent Events (실시간) |

## 디렉토리 구조

```
LAON_VaultGuard/
├── README.md
├── DEVELOPMENT.md          ← 개발 가이드
├── package.json
├── tsconfig.json
├── .env.example
├── src/
│   ├── index.ts            ← 진입점 (Express + Scheduler)
│   ├── config.ts           ← 환경변수 로드
│   ├── scheduler.ts        ← cron 기반 레포 스캔 스케줄
│   ├── git-monitor.ts      ← Git 레포 변경 수집 (로컬/원격)
│   ├── diff-extractor.ts   ← git diff 추출 + 파일별 변경사항
│   ├── candidate-filter.ts ← 1차 git grep 키워드 필터
│   ├── llm-harness.ts      ← 멀티 LLM 호출 + 결과 병합
│   ├── db.ts               ← SQLite (better-sqlite3)
│   ├── alert-engine.ts     ← Slack/Telegram/Email/Dashboard 통보
│   ├── routes/
│   │   └── api.ts          ← REST API 라우트
│   └── types.ts            ← 공통 타입 정의
├── docs/
│   ├── Architecture.md
│   ├── API.md
│   ├── Database.md
│   └── LLM_Prompt.md       ← 시크릿 스캐닝 LLM 프롬프트 (한·영)
├── public/
│   ├── index.html          ← 대시보드 UI
│   └── dashboard.js        ← 프론트엔드 로직
└── tests/
    └── ...
```

## LLM 시크릿 탐지 프롬프트

참고: [Secret scanning LLM harness prompt](../TechDoc/LLM_Security/Secret%20scanning%20llm%20harness%20prompt.md)

핵심 원칙:
- **시크릿 원문 절대 출력 금지** — 마스킹 지문(앞4자+뒤2자)만 보고
- **거짓양성 선호** — 의심되면 플래그 (false positive > false negative)
- **JSON 결정론적 출력** — 파싱 가능한 구조화된 결과
- **프롬프트 인젝션 방어** — 파일 내 텍스트를 지시가 아닌 데이터로 취급

탐지 대상 클라우드: AWS, Azure, GCP, **KT Cloud**, **Naver Cloud Platform (NCP)**

## REST API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/status` | 현재 스캔 상태 (미해결 건수, 마지막 스캔 시각) |
| GET | `/api/history` | 과거 탐지 이력 |
| PUT | `/api/acknowledge/:id` | 발견 건 확인 처리 |
| POST | `/api/scan/trigger` | 수동 스캔 트리거 |
| GET | `/api/repos` | 등록된 모니터링 레포 목록 |
| POST | `/api/repos` | 신규 레포 등록 |
| GET | `/dashboard` | 대시보드 UI |

→ 상세: [docs/API.md](docs/API.md)

## 알람 순서 (구현 우선순위)

1. **웹 대시보드** — 로컬 서버 REST API + 실시간 SSE
2. **Telegram Bot** — 개인/팀 채널로 탐지 알림
3. **Slack** — 웹훅 기반 채널 알림
4. **이메일** — 일일/주간 요약 리포트

## 데이터베이스

SQLite (`data/vaultguard.db`) — 제로 설정, 파일 기반.

주요 테이블: `repositories`, `scan_runs`, `findings`, `alert_config`, `audit_log`
→ 상세: [docs/Database.md](docs/Database.md)

## 로드맵

- [x] 기본 아키텍처 설계
- [x] DB 스키마 설계
- [ ] TypeScript 프로젝트 세팅 (tsconfig, esbuild)
- [ ] Git monitor + diff extractor 구현
- [ ] Candidate filter (git grep 연동)
- [ ] LLM harness (멀티 LLM 병렬 분석)
- [ ] Result aggregation (다수결 엔진)
- [ ] SQLite 저장 · 이력 조회
- [ ] 웹 대시보드 (REST API + UI)
- [ ] Telegram 봇 알람
- [ ] Slack 알람
- [ ] 이메일 리포트
- [ ] 크로스플랫폼 패키징 (pkg or electron)
- [ ] GitHub App / GitLab App 연동 (OAuth)
- [ ] VSCode 확장

## 라이선스

MIT

---

> *"공개되기 전에 찾는 것이 공개된 후 수습하는 것보다 백 배 쉽다."*
> — Tving AWS 키 노출 사건(2026.06)에서 얻은 교훈
