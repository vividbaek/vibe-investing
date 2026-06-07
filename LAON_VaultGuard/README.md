# LAON VaultGuard

[![npm version](https://img.shields.io/npm/v/laon-vaultguard)](https://www.npmjs.com/package/laon-vaultguard)
[![npm downloads](https://img.shields.io/npm/dt/laon-vaultguard)](https://www.npmjs.com/package/laon-vaultguard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **LLM-based Automated Observer for Non-public Keys**
>
> 개발자 PC와 팀 환경에서 Git 레포지토리를 정기적으로 감시해 AWS, Azure, GCP, KT Cloud, Naver Cloud 등 클라우드 프라이빗 키가 노출되지 않도록 사전 차단하는 크로스플랫폼 보안 감사 도구.

한국어 | [English](./README_EN.md) | [中文](./README_ZH.md) | [日本語](./README_JA.md)

## 왜 LAON VaultGuard인가

**2026년 6월, Tving의 GitHub 레포에 AWS 액세스 토큰이 하드코딩된 채 공개된 사건**은 단일 실수가 전체 인프라를 위험에 빠뜨릴 수 있음을 다시 한번 보여줬습니다. `gitleaks`, `trufflehog` 같은 정규식 기반 스캐너는 빠르지만 문맥을 이해하지 못합니다. 반면 LLM은 변수명이 평범하거나 조립된 형태의 시크릿도 "의미"로 탐지할 수 있습니다.

하지만 **단일 LLM에만 의존하는 것은 또 다른 단일 장애점**입니다. 모델마다 판단 편향이 있고, API 장애나 할당량 초과 시 탐지 공백이 발생합니다. LAON VaultGuard는 **여러 LLM을 동시에 교차 검증**하는 구조로 설계되었습니다:

- **각 LLM은 서로 다른 보안 페르소나를 형성** — Claude(규율 기반), DeepSeek(고성능·저비용), GPT(체계적), MiniMax(경량·빠름), **Ollama(로컬·오프라인)**
- **다수결 모드**로 오탐을 줄이고, **순차 fallback**으로 단일 LLM 장애에도 스캔이 중단되지 않음
- [Gitleaks](https://github.com/gitleaks/gitleaks) (pre-commit) → **LAON VaultGuard** (정기 감사) → [TruffleHog](https://github.com/trufflesecurity/trufflehog) (CI) → GitHub Secret Scanning (push 후) 4단계 방어선의 핵심 축

정규식은 속도를, LLM은 문맥을 담당합니다. **둘을 함께 쓸 때 진짜 안정성이 확보됩니다.**

## 핵심 기능

- **정기 레포 감시** — GitHub, GitLab, 로컬 레포를 cron 기반 스케줄러로 주기적 스캔
- **멀티 LLM 탐지** — OpenAI(ChatGPT), DeepSeek, MiniMax, Mimo, **Ollama(로컬)** 등 여러 LLM을 동시·교차 검증
- **오프라인 모드** — Ollama 연동 시 인터넷 없이 완전 로컬에서 시크릿 탐지 (API 키 불필요)
- **2단계 탐지** — 1차 `git grep` 키워드 필터 → 2차 LLM 문맥 분석으로 거짓양성 최소화
- **웹 대시보드** — 같은 네트워크의 팀이 함께 모니터링 가능한 로컬 웹 UI
- **멀티 알람** — Slack, Telegram, 이메일, 대시보드로 탐지 결과 실시간 통보
- **크로스플랫폼** — macOS, Linux, Windows (WSL)
- **v0.5 신규**: SQLite WAL 스토리지, Differential Privacy 전처리, SARIF export, Prometheus `/metrics`, Docker 지원

## 사용 시나리오

### 🧑‍💻 개인 개발자 — "내 레포에 실수로 키 올리기 전에"

```bash
npm run setup        # DeepSeek API 키만 입력 (월 $1 미만)
npm run dev          # http://localhost:3101/dashboard
```

- **DeepSeek 단독**으로 빠르고 저렴하게 (토큰당 $0.14/M)
- 파일 저장 시 VS Code 확장이 실시간 경고
- Ollama 설치하면 API 비용 0원, 완전 로컬

### 🏢 중소기업 / 팀 — "팀 레포 전체 감시 + 알람"

```bash
# .env 설정
LLM_PROVIDERS=claude,deepseek,ollama
LLM_MODE=majority   # 3중 교차검증, 오탐 최소화
SCAN_CRON=0 */4 * * *   # 4시간마다 자동 스캔
TELEGRAM_BOT_TOKEN=...
```

- **다수결 모드** — Claude + DeepSeek + Ollama 3중 검증, 2개 이상 동의 시에만 알람
- **팀 대시보드** — `HOST=0.0.0.0` 설정 시 같은 네트워크에서 `http://<IP>:3101` 접속
- **알람 연동** — Slack, Telegram, Email, Discord, Teams 중 선택
- **Docker 배포** — `docker-compose up -d` 한 줄로 실행 (아래 가이드 참고)

### 🔒 에어갭 / 오프라인 — "인터넷 없는 망분리 환경"

```bash
brew install ollama              # macOS
ollama pull deepseek-r1:8b       # 로컬 추론 모델
ollama pull securereview-7b      # 보안 특화 파인튜닝 (Apple Silicon)

# .env
LLM_PROVIDERS=ollama
LLM_MODE=sequential
STORAGE_ENGINE=sqlite
```

- **인터넷 완전 차단** — Ollama가 모든 LLM 추론을 로컬에서 처리
- **소스코드 외부 유출 Zero** — Git grep → Ollama → SQLite, 모든 데이터 머신 내 보존
- **교차검증** — deepseek-r1(추론) + securereview-7b(보안 도메인) 2중 검증으로 오탐 제어
- **망분리 규정 준수** — 국방·금융·공공기관 규제 환경에 적합

## Docker 설치

### 기본 실행 (앱만)

```bash
cd LAON_VaultGuard
cp .env.example .env        # LLM API 키 설정 필수
docker-compose up -d        # http://localhost:3101/dashboard
```

### Ollama 포함 실행 (GPU 가속)

```bash
docker-compose --profile ollama up -d
docker-compose exec ollama ollama pull deepseek-r1:8b
```

### 수동 Docker 빌드

```bash
docker build -t laon-vaultguard .
docker run -d -p 3101:3101 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  --name laon laon-vaultguard
```

**사전 구성된 값** (Docker 이미지 내):
- `STORAGE_ENGINE=sqlite` — ACID 트랜잭션, 동시성 안전
- `DP_ENABLED=true` — LLM 전송 전 시크릿 자동 마스킹
- `HOST=0.0.0.0` — 컨테이너 외부 접근 허용
- `HEALTHCHECK` — 30초마다 `/api/status` 체크

## VS Code 확장 설치

### 수동 설치 (개발자 모드)

```bash
cd LAON_VaultGuard/vscode-extension
npm install
npm run compile
```

VS Code에서:
1. `Cmd+Shift+P` → `Developer: Install Extension from Location...`
2. `LAON_VaultGuard/vscode-extension` 폴더 선택
3. VS Code 재시작

### 기능

| 기능 | 설명 |
|------|------|
| **실시간 하이라이트** | 13개 시크릿 패턴 자동 감지, 저장 시 스캔 |
| **Problems 패널** | 탐지된 시크릿을 마스킹 지문만 노출 (`AKIA****7Q`) |
| **Status Bar** | `LAON: clean` / `LAON: 3` 실시간 표시 |
| **Deep LLM Scan** | `Cmd+Shift+P` → `LAON VaultGuard: Scan Workspace` |
| **우클릭 메뉴** | 파일 컨텍스트 메뉴에서 `Scan Current File for Secrets` |

### 설정

| 설정 키 | 기본값 | 설명 |
|---------|--------|------|
| `laon-vaultguard.enabled` | `true` | 확장 활성화/비활성화 |
| `laon-vaultguard.scanOnSave` | `true` | 파일 저장 시 자동 스캔 |
| `laon-vaultguard.scanOnOpen` | `false` | 파일 열 때 스캔 |
| `laon-vaultguard.severity` | `medium` | 최소 심각도 (critical/high/medium/all) |

## Pre-commit Hook

커밋 전에 변경된 파일에서 시크릿을 자동 검사합니다.

```bash
npx laon-vaultguard hook install     # 현재 레포에 설치
npx laon-vaultguard hook uninstall   # 제거
```

**동작 방식**:
- `git commit` 실행 시 `pre-commit` 훅이 자동 발동
- 스테이징된 파일만 빠른 정규식 스캔 (LLM 호출 없음, <1초)
- critical/high 패턴 감지 시 커밋 차단
- `git commit --no-verify` 로 긴급 bypass 가능

### 유사 솔루션 대비 장점

| | LAON VaultGuard | gitleaks | trufflehog | GitHub Push Protection |
|---|---|---|---|---|
| 설치 | `npx` 1줄 | `brew install` | `pip install` | 설정 불필요 |
| 동작 위치 | **로컬 pre-commit** | pre-commit | pre-commit | push 시점 |
| LLM 분석 | Deep Scan 연동 | ❌ (정규식만) | ❌ (정규식+엔트로피) | ❌ |
| 커스텀 패턴 | git grep 60+ 패턴 | `.gitleaks.toml` | 제한적 | GitHub 관리 |
| 오프라인 | ✅ Ollama 연동 | ✅ | ✅ | ❌ |
| 차단 타이밍 | **커밋 전** (가장 빠름) | 커밋 전 | 커밋 전 | **푸시 후** (이미 노출) |

## 대시보드 인증

`HOST=0.0.0.0` 로 팀 공유 시 Bearer token 인증으로 API를 보호합니다.

```bash
# .env
DASHBOARD_TOKEN=my-secret-team-token
```

- 미설정 시: 모든 요청 허용 (개인 로컬 사용)
- 설정 시: `Authorization: Bearer <token>` 필요
- 대시보드 페이지(`/dashboard`)와 상태 확인(`/api/status`)은 인증 없이 접근 가능
- docker-compose에서도 `DASHBOARD_TOKEN` 환경변수로 설정

## PDF 리포트

스캔 결과를 PDF로 내보낼 수 있습니다.

```bash
open http://localhost:3101/api/report/pdf   # 브라우저에서 열기 → "PDF로 저장"
```

- print-optimized HTML로 렌더링, 브라우저 `Cmd+P` → PDF로 저장
- severity별 color coding (critical=빨강, high=주황)
- masked fingerprint만 포함 (보안 유지)
- 외부 의존성 없음 (브라우저 내장 기능 활용)

### 보안 스캔 확장 (v0.3+)

클라우드 키 탐지 외에 추가 보안 취약점도 함께 감사합니다:

| 카테고리 | 탐지 항목 |
|---|---|
| SQL Injection | 쿼리 문자열 연결, `rawQuery`, `db.execute()`, PreparedStatement 누락 |
| DB 연결정보 노출 | `jdbc:`, `mongodb://`, `redis://`, `DATABASE_URL`, `DB_PASSWORD` 평문 |
| TLS/SSL 설정 | `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `insecure=true` |
| 구버전 취약점 | OpenSSL 0.x/1.0, TLSv1.0, Apache 2.2, PHP 5.x/7.0-3, MySQL 5.0-6, WordPress 1-5 |

### 테스트 방법

**방법 1: CLI (빠른 단발 스캔)**

```bash
# 전체 스캔
npx laon-vaultguard scan .

# 카테고리별 스캔
npx laon-vaultguard scan . --mode sql       # SQL injection 만
npx laon-vaultguard scan . --mode secrets   # 클라우드 키·토큰 만
npx laon-vaultguard scan . --mode versions  # 구버전 취약점 만
npx laon-vaultguard scan . --mode db        # DB 연결정보 노출 만
npx laon-vaultguard scan . --mode tls       # TLS/SSL 설정 만

# LLM 없이 원시 후보만 확인
npx laon-vaultguard scan . --no-llm
```

**방법 2: 대시보드 (주기적 모니터링)**

```bash
npm run dev                           # http://localhost:3101/dashboard
# -> "지금 스캔" 버튼 or cron 자동 스캔
# -> 결과를 대시보드에서 필터링·확인 처리
# -> Slack/Telegram/Email/Discord/Teams 알람 연동 가능
```

### 테스트 레포 (로컬 전용)

`tests/test-repo/` 는 전체 탐지 카테고리를 커버하는 더미 시크릿 레포입니다.  
GitHub Push Protection 정책으로 인해 원격 레포에는 포함되지 않으며, 로컬에서만 사용합니다.

```bash
ls tests/test-repo/        # secrets.py + vulnerabilities.ts (38개 후보)
npx laon-vaultguard scan tests/test-repo --no-llm
```

| 파일 | 커버리지 |
|---|---|
| `secrets.py` | AWS/Azure/GCP/NCP/KT Cloud 키, DB URL, API 토큰, JWT, SSH 키 |
| `vulnerabilities.ts` | SQL Injection (5패턴), TLS/SSL 미설정, 구버전 (14종), DB 노출 |

![대시보드 스크린샷](public/dashboard.png)

## 빠른 시작

### npm (권장)

```bash
npx create-laon-vaultguard    # 대화형 설치 마법사 (한/영/중/일)
npx laon-vaultguard scan .    # 현재 폴더 스캔
```

[npm 패키지](https://www.npmjs.com/package/laon-vaultguard) • `npm install -g laon-vaultguard`

### 소스코드에서 실행

```bash
cd LAON_VaultGuard
npm install
cp .env.example .env   # LLM API 키, Slack/Telegram 웹훅 등 설정
npm run build
npm start              # 기본 포트 3101, http://localhost:3101/dashboard
```

### Ollama 오프라인 모드 — 기업 보안을 위한 구성

기업 환경이나 기밀 레포지토리에서는 **소스코드를 외부 LLM API로 전송하는 것 자체가 보안 위험**입니다. LAON VaultGuard는 [Ollama](https://ollama.com)를 통해 **완전히 오프라인에서도 동작**합니다.

```bash
# 1. Ollama 설치 + 모델 다운로드
brew install ollama && ollama pull llama3.1

# 2. .env 설정 (다른 LLM 키 불필요)
LLM_PROVIDERS=ollama
LLM_MODE=sequential

# 3. 실행 — 모든 분석이 로컬에서만 처리됨
npm run dev
```

**Ollama 오프라인 모드의 장점:**
- 🔒 **소스코드 외부 유출 Zero** — 모든 분석이 로컬 머신 내에서 완료
- 💰 **무료** — API 키 불필요, 토큰 비용 $0
- 🏢 **기업 보안 정책 준수** — 방화벽·에어갭 환경에서도 동작
- 🔄 **하이브리드 구성 가능** — `LLM_PROVIDERS=ollama,deepseek` 설정 시 평소엔 Ollama, 필요시 클라우드 LLM fallback

→ 상세: [docs/Ollama.md](docs/Ollama.md)

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
File Storage (JSON) + Alert Engine (Slack · Telegram · Email · Web)
  ↓
Dashboard (REST API + 정적 프론트)
```

## 기술 스택

| 계층 | 기술 |
|---|------|
| 런타임 | Node.js ≥18, TypeScript |
| 웹 프레임워크 | Express.js |
| 저장소 | **SQLite** (WAL, ACID) / JSON (1인 싱글 디바이스 전용) — 설정으로 전환 |
| Git 연동 | `simple-git`, `@octokit/rest` (GitHub) |
| 스케줄러 | `node-cron` |
| LLM | OpenAI SDK (ChatGPT, DeepSeek, Claude, Ollama — OpenAI 호환 API) |
| 보안 | Differential Privacy (14개 시크릿 패턴 마스킹) |
| 알람 | Slack Webhook, Telegram Bot API, Nodemailer, Discord, Teams |
| 메트릭 | Prometheus `/metrics` (카운터, 게이지, 히스토그램) |
| 익스포트 | SARIF v2.1.0 (GitHub Code Scanning 호환) |
| 배포 | Docker, docker-compose, npm (`npx create-laon-vaultguard`) |
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

1. **웹 대시보드** ✅ — 로컬 서버 REST API + 실시간 SSE
2. **Telegram Bot** ✅ — 개인/팀 채널로 탐지 알림
3. **Slack** ✅ — 웹훅 기반 채널 알림 (Block Kit)
4. **이메일** ✅ — nodemailer HTML 리포트 (실시간/일간/주간 선택 + 디바이스명)

## 저장소

파일 기반 JSON (`data/`) — 제로 설정, 제로 의존성.

`repos.json` · `findings.json` · `scans/` · `logs/` · `alert_config.json`
→ 상세: [docs/Database.md](docs/Database.md)

## 로드맵

- [x] 기본 아키텍처 설계
- [x] 파일 기반 JSON 저장소 (SQLite 불필요 — 로컬에선 JSON/MD 충분)
- [x] Git monitor + candidate filter (git grep 1차 필터)
- [x] 멀티 LLM harness (OpenAI, DeepSeek, MiniMax, Mimo, **Ollama**)
- [x] Ollama 로컬 모드 — 인터넷 없이 완전 오프라인 시크릿 탐지
- [x] 2단계 탐지 (git grep → LLM 문맥 분석)
- [x] 웹 대시보드 (REST API + SSE 실시간)
- [x] CLI 모드 (`npx laon-vaultguard scan`)
- [x] Telegram 봇 알람
- [x] Slack 알람 (Block Kit)
- [x] 이메일 리포트 (nodemailer · 일간/주간 HTML)
- [x] GitHub 원격 레포 + OAuth
- [x] 크로스플랫폼 (macOS / Linux / Windows WSL)

### v0.3 — 성능 및 정확도 최적화

- [x] 파일 해시 기반 증분 스캔 캐싱 (변경 없는 파일 스킵)
- [x] 2-Tier LLM: 경량 1차 필터링 → 고성능 2차 정밀 분석
- [x] 배치 처리: API 호출을 50건 단위로 분할해 비용 절감
- [x] Shannon 엔트로피 사전 필터 (3.5 threshold)
- [x] 컨텍스트 위험 분류 (.env.example, README, test = low risk)
- [x] 로그 보관 주기 (LOG_RETENTION_DAYS, 기본 30일)
- [x] CI/CD 통합 가이드: GitHub Actions, GitLab CI, pre-commit hook
- [x] 보안 표준 매핑: OWASP Top 10, CWE, KISA, NIST CSF

### v0.4 — 설치 마법사 + 스토리지 엔진 + Ollama 멀티 모델

- [x] `STORAGE_ENGINE` 설정: SQLite (ACID, WAL) / JSON (레거시) 선택 가능
- [x] 대화형 설치 마법사(`npm run setup`) — LLM 제공자 다중 선택 + 마스킹 API 키 입력
- [x] Ollama 자동 감지 + 미설치 시 OS별 설치 가이드 (brew/curl/download)
- [x] Ollama 모델 5종 추천 + 비교표 — deepseek-r1, llama3.1, mistral, codestral, securereview-7b
- [x] 보안 특화 파인튜닝 모델 지원: `vitorallo/securereview-7b-mlx-4bit` (Apple Silicon)
- [x] 멀티 Ollama 교차검증 가이드 — 2개 모델로 다수결 모드
- [x] SQLite vs RocksDB 스토리지 엔진 비교 평가 (`docs/Storage_Engine_Comparison.md`)
- [x] 2026-06-07 코드 리뷰 버그 7건 패치 (llm-harness, cli, scan-runner, candidate-filter, git-monitor)

### v0.5 — SQLite + SARIF + Differential Privacy + Prometheus + Docker

- [x] **SQLite 마이그레이션** — `better-sqlite3` WAL 모드, ACID 트랜잭션, `npm run migrate` JSON→SQLite 변환
- [x] **Dual-Engine** — `db.ts` facade → `STORAGE_ENGINE=sqlite|json` 으로 런타임 전환
- [x] **SARIF v2.1.0** — `npm run export-sarif` → GitHub Code Scanning / GitLab SAST 호환
- [x] **Differential Privacy** — 14개 룰로 LLM 전송 전 시크릿 마스킹 (`DP_ENABLED=true`)
- [x] **Prometheus 메트릭** — `/metrics` 엔드포인트 (scans, findings, tokens, latency)
- [x] **Docker 이미지** — multi-stage Alpine, docker-compose (app + Ollama 프로필)
- [x] **VS Code 확장** — 실시간 하이라이트, Problems 패널, 저장 시 스캔

### v0.6 (계획)

- [ ] 오탐 피드백 루프 (few-shot 프롬프트 개선)
- [ ] fine-tuned 모델 평가 파이프라인
- [ ] pre-commit hook 통합 코드 (`npx laon-vaultguard hook install`)

## 업데이트 내역

### 2026-06-07 — v0.5 SQLite + SARIF + DP + Prometheus + Docker

**스토리지 엔진**
- `better-sqlite3` WAL 모드 — ACID 트랜잭션, 무제한 concurrent read
- `npm run migrate` — 기존 JSON 파일 → SQLite 원클릭 마이그레이션
- `db.ts` → `STORAGE_ENGINE` 환경변수로 json/sqlite 런타임 전환

**SARIF v2.1.0**
- `npm run export-sarif -- --output results.sarif` — GitHub Code Scanning 업로드 가능
- severity→level 매핑, confidence→rank 스코어링

**Differential Privacy**
- 14개 시크릿 패턴 마스킹 (AWS, GCP, GitHub, JWT, PEM, connection string 등)
- `DP_ENABLED=true` (기본) — LLM 전송 전 자동 마스킹

**Prometheus /metrics**
- `laon_scans_total`, `laon_findings_*`, `laon_llm_tokens_total`, 히스토그램
- Grafana 대시보드 연동 가능

**Docker**
- Multi-stage Alpine 이미지 (better-sqlite3 네이티브 컴파일)
- `docker-compose up -d` → 앱 + 데이터 볼륨, `--profile ollama` → GPU LLM 추가

### 2026-06-07 — v0.5 설치 마법사 + Ollama 멀티 모델 + 스토리지 엔진

**대화형 설치 마법사 (`npm run setup`)**
- LLM 제공자 다중 선택: DeepSeek, Claude, ChatGPT, Ollama
- 마스킹 API 키 입력 + 키 등록 URL 안내
- Ollama 자동 감지 + OS별 설치 가이드 (macOS `brew`, Linux `curl`, Windows 다운로드)
- 모델 5종 비교표 + 추천 (deepseek-r1:8b, llama3.1, mistral, codestral, securereview-7b)
- 보안 파인튜닝 모델 `vitorallo/securereview-7b-mlx-4bit` 지원 (Apple Silicon)
- 멀티 Ollama 교차검증 구성 가이드 (LLM_PROVIDERS=ollama,ollama-secondary, LLM_MODE=majority)

**스토리지 엔진**
- `STORAGE_ENGINE=sqlite|json` 환경 변수 추가
- `docs/Storage_Engine_Comparison.md` — SQLite vs RocksDB 종합 평가

**구성**
- 버전 `0.4.0` → `0.5.0`

### 2026-06-07 — v0.4 버그 패치 + 설계 개선 검토

**코드 레벨 버그 수정 (7건)**

| # | 파일 | 수정 내용 |
|---|------|-----------|
| 1 | `llm-harness.ts` | `AbortController`/`timeoutId`를 try 블록 밖으로 호이스트 — `catch`에서 `clearTimeout(0)`(무동작) → `clearTimeout(timeoutId)` |
| 2 | `llm-harness.ts` | LLM 응답 JSON Schema 검증(`validateLlmScanResult()`) + cleartext 시크릿 유출 가드(`containsCleartextSecret()`) 추가 |
| 3 | `cli.ts` | 버전 표시 `v0.2.0` → `v0.4.0` (`index.ts`와 불일치 해소) |
| 4 | `scan-runner.ts` | 캐시 해시 `createHash('md5')` → `createHash('sha256')` (FIPS 호환) |
| 5 | `candidate-filter.ts` | `simple-git` 에러 핸들링 개선 — `err.code` 대신 `exited with code 1` 메시지 정규식 검사 |
| 6 | `git-monitor.ts` | `parseDiff()` 내 미사용 `filePattern` global regex 제거 |
| 7 | `git-monitor.ts` | GitHub clone URL에서 토큰 제거 → `.netrc` 파일로 대체 (로그·프로세스 목록 노출 방지) |

**문서 업데이트**

| 파일 | 추가 내용 |
|------|-----------|
| `DEVELOPMENT.md` | §8 설계적 개선 필요 사항 (7건) + §8.2 추가 필요 기능 (9건) |
| `DEVELOPMENT.md` | §9 경쟁 솔루션 대비 단점 및 보강 방안 (8건) + 우선순위 액션 Top 5 (상태 포함) |

**기타 수정**

- `01.Trading Strategy/ARDS-Defense/` — 중복 등록된 소문자 `readme.md` 제거 (macOS case-insensitive FS 충돌)
- `README.md` → `0ae76d4` 버전으로 복원 (vibe-investing 한글 콘텐츠)

**남은 과제** — [DEVELOPMENT.md §8~§9](./DEVELOPMENT.md#8-개선-필요-사항-review) 참고

## 백테스트 결과 (v0.5)

`npm run backtest` — **54개 자동화 테스트 전부 통과** ✅

| 모듈 | 통과 | 검증 항목 |
|------|------|-----------|
| 스토리지 (SQLite + JSON) | 12/12 | CRUD, WAL, 마이그레이션 |
| Differential Privacy | 10/10 | 14개 시크릿 마스킹 규칙 |
| SARIF Export | 4/4 | v2.1.0 호환, GitHub Code Scanning |
| Prometheus Metrics | 5/5 | `/metrics` 엔드포인트 |
| Candidate Filter | 4/4 | 60+ 패턴, grep 통합 |
| Config + Version | 7/7 | 검증, 기본값 |

→ [상세 체크리스트](./docs/BACKTEST_CHECKLIST.md)

## 라이선스

MIT

---

> *"공개되기 전에 찾는 것이 공개된 후 수습하는 것보다 백 배 쉽다."*
> — Tving AWS 키 노출 사건(2026.06)에서 얻은 교훈
