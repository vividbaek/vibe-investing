# DEVELOPMENT LOG — LAON VaultGuard

> macOS · Node.js/TypeScript · LLM 기반 시크릿 탐지 감사 도구

## 2026-06-07 — v0.1.1 에러 처리 + 대시보드 UX + CLI

### 완료
- [x] `src/config.ts` — SCAN_TIMEOUT_MS, SCAN_MAX_CANDIDATES, SCAN_MAX_FILE_SIZE_KB 추가
- [x] `src/llm-harness.ts` — AbortController 타임아웃, 429/quota 감지, 인증 에러 분류, JSON 파싱 실패 처리
- [x] `src/git-monitor.ts` — `checkGitInstalled()` 사전 검증
- [x] `src/scan-runner.ts` — git 미설치 사전 체크, candidates 최대치 truncation, LLM 에러 non-fatal 처리
- [x] `public/index.html` — 레포 필터 select, 날짜 범위 input, 체크박스 컬럼, bulk bar
- [x] `public/dashboard.js` — 레포 필터, 날짜 검색, 개별/전체 선택, 일괄 acknowledge
- [x] `src/routes/api.ts` — `PUT /api/findings/acknowledge/bulk`, 날짜 from/to 쿼리 파라미터
- [x] `src/cli.ts` — `laon-vaultguard scan <path>` CLI 모드 (git grep → LLM → 콘솔 출력)
- [x] `docs/CLI.md` — CLI 매뉴얼 (환경변수, 에러 케이스, CI/CD 예시)
- [x] `package.json` — bin entry, `npm run scan`, `npm run cli` 스크립트
- [x] `npm run typecheck` → 정상
- [x] `npm run build` → 정상

## 2026-06-07 — v0.1 프로젝트 초기화

### 완료
- [x] 프로젝트 디렉토리 구조, package.json, tsconfig.json
- [x] docs: Architecture.md, API.md, Database.md, LLM_Prompt.md
- [x] src: types, config, db, git-monitor, candidate-filter, llm-harness, scan-runner, scheduler, sse, alert-engine, routes/api, index
- [x] public: index.html + dashboard.js (SSE 대시보드)
- [x] npm install / build / typecheck 통과
- [x] 서버 구동 테스트 완료 (API, 레포 등록, 스캔, audit log)

### 다음 작업 (v0.2)
1. [ ] SQLite 마이그레이션 (better-sqlite3)
2. [ ] Slack 알람
3. [ ] 이메일 요약 리포트
4. [ ] GitHub App OAuth 연동
