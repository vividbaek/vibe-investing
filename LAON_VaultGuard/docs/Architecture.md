# Architecture — LAON VaultGuard

> 🇰🇷 LAON VaultGuard의 전체 아키텍처와 컴포넌트 설계를 설명합니다.
> 🇺🇸 Describes the overall architecture and component design of LAON VaultGuard.
> 🇨🇳 描述 LAON VaultGuard 的整体架构和组件设计。

> **v0.2**: 크로스플랫폼 지원 (macOS / Linux / Windows WSL), 파일 기반 JSON 저장소

## High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│                    .env (Config)                         │
│  LLM Keys · Repo List · Cron · Alert Channels           │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Scheduler (node-cron)                       │
│  "0 */6 * * *" → 6시간마다 scanAllRepos() 트리거        │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Git Monitor (simple-git + Octokit)         │
│  · 로컬 레포: git log --since="last_scan"               │
│  · GitHub 레포: Octokit compareCommits (delta only)     │
│  → 변경된 커밋·파일 목록 수집                            │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│         Candidate Filter (1차 — git grep)               │
│  의심 키워드/패턴 매칭 (로컬 실행, LLM 호출 전)          │
│  → suspects: { file, line, snippet }[]                   │
│  LLM 토큰 최소화: 의심 라인만 전달                       │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│           LLM Harness (2차 — 멀티 LLM)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ OpenAI   │ │ DeepSeek │ │ MiniMax  │ │ Mimo     │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       └─────────────┴────────────┴────────────┘         │
│                         ↓                               │
│              Result Aggregator                           │
│  · parallel: 모든 결과 수집 후 다수결                    │
│  · sequential: 첫 high-confidence 사용, 실패 시 fallback │
│  · majority: 과반수 동의 건만 확정                       │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│           File Storage (JSON files)                      │
│  data/repos.json · data/findings.json · data/scans/*    │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Alert Engine                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Web(SSE) │ │ Telegram │ │  Slack   │ │  Email   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Express Server (localhost:3101)             │
│  REST API + Dashboard UI + SSE 실시간 이벤트             │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Scheduler (`scheduler.ts`)
- `node-cron`으로 주기적 작업 등록
- `.env`의 `SCAN_CRON` 표현식 사용 (기본: 6시간)
- 수동 트리거: `POST /api/scan/trigger`
- 초기 구동 시 모든 등록 레포 전체 스캔 1회 실행

### 2. Git Monitor (`git-monitor.ts`)
- **로컬 레포**: `simple-git` — `git log` + `git diff` delta 수집
- **GitHub 원격**: `@octokit/rest` — `compareCommitsWithBasehead` API로 증분 diff (전체 클론 방지)
- 마지막 스캔 시각 이후 변경사항만 delta 수집
- **최초 스캔 시**: 전체 파일 대상 (getWholeRepoChanges)

### 3. Candidate Filter (`candidate-filter.ts`)
- `git grep -nIE` 정규식 패턴 기반 1차 필터
- LLM 토큰 비용 최소화 (전체 파일 대신 의심 라인만)
- 결과 형식: `{ filePath, lineNumber, snippet, matchedPattern }`
- snippet 최대 200자 제한

### 4. LLM Harness (`llm-harness.ts`)

**안전 규칙 (코드 레벨 강제):**
1. 프롬프트에 `hard_safety_rules` 주입 (시크릿 출력 금지, 마스킹 강제)
2. LLM 응답 검증: `masked_fingerprint` 외 필드에서 시크릿 패턴 매칭 → 발견 시 해당 finding 폐기
3. 로그 출력 전 모든 문자열 마스킹 필터 적용
4. `temperature=0`로 결정론적 응답 유도

**멀티 LLM 모드:**
| 모드 | 동작 | 장점 | 단점 |
|---|---|---|---|
| `parallel` | 모든 LLM 동시 호출 → 결과 병합 | 가장 빠름 | 비용 ↑ |
| `sequential` | 우선순위 순 호출 → 첫 신뢰도 높은 결과 사용, 실패 시 fallback | 비용 ↓, 장애 내성 | 느림 |
| `majority` | 모든 LLM 결과 중 과반수 동의만 채택 | 정확도 ↑ | 비용 ↑, 느림 |

**LLM Fallback 체인 (sequential 모드):**
- Provider 1 실패(네트워크/할당량) → Provider 2 자동 fallback → Provider 3
- 모든 provider 실패 시 에러 로깅 후 스캔 중단 (치명적 실패 아님)

### 5. Alert Engine (`alert-engine.ts`)
- **Web SSE**: `GET /api/events` — Server-Sent Events로 대시보드 실시간 갱신
- **Telegram**: Bot API `sendMessage` — critical/high 건 즉시 발송
- **Slack**: Incoming Webhook (Phase 3)
- **Email**: Nodemailer — 일일/주간 요약 (Phase 4)

### 6. Dashboard (`public/`)
- 정적 HTML + Vanilla JS + SSE
- `127.0.0.1:3101/dashboard` (기본: 로컬 전용)
- 실시간 finding 목록, 상태별 필터, acknowledge 처리

## 데이터 흐름 (한 번의 스캔 주기)

```
1. Scheduler → scanAllRepos()
2. 각 repo에 대해:
   a. git-monitor: last_scan 이후 diff 추출 (최초: 전체)
   b. candidate-filter: git grep → candidates[]
   c. candidates.length > 0 → llm-harness.analyze(candidates)
   d. LLM 응답 파싱 → findings[]
3. findings → 파일 저장 (data/findings.json)
4. critical/high → alert-engine 발송
5. SSE 이벤트 → 대시보드 실시간 갱신
```

## 개선 로드맵 (v0.2+)

| 항목 | 우선순위 | 설명 |
|---|---|---|
| LLM 비용 로깅 | High | audit_log에 토큰 사용량·예상 비용 기록 |
| GitHub OAuth 연동 | Medium | 대시보드에서 GitHub 계정으로 레포 목록 가져오기 |
| 대시보드 인증 | Medium | HOST=0.0.0.0 시 비밀번호/토큰 인증 추가 |
| SQLite 확장 | Medium | 파일 기반 → SQLite 마이그레이션 (better-sqlite3) |
| 크로스플랫폼 | Low | Linux, Windows 지원 |
| GitLab API | Low | @gitbeaker/rest 원격 연동 |
