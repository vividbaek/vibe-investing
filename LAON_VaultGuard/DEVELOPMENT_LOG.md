# DEVELOPMENT LOG — LAON VaultGuard

> macOS / Linux / Windows (WSL) · Node.js/TypeScript · LLM 기반 시크릿 탐지 감사 도구

## 2026-06-07 — v0.5 SQLite + SARIF + DP + Prometheus + Docker 빌드아웃

### 완료
- [x] `src/db-sqlite.ts` — SQLite(better-sqlite3) WAL 모드, ACID 트랜잭션, 4개 테이블 + 3개 인덱스
- [x] `src/db-json.ts` — 기존 JSON 저장소 코드 분리 (레거시 백엔드)
- [x] `src/db.ts` — `STORAGE_ENGINE` 환경변수로 json/sqlite 런타임 전환 facade
- [x] `src/migrate-json-to-sqlite.ts` — `npm run migrate` 원클릭 JSON→SQLite 변환
- [x] `src/sarif-export.ts` — SARIF v2.1.0, GitHub Code Scanning / GitLab SAST 호환
- [x] `src/differential-privacy.ts` — 14개 시크릿 패턴 마스킹 (AWS, GCP, JWT, PEM, DB conn 등)
- [x] `src/llm-harness.ts` — DP 마스킹 통합 (LLM 전송 전 자동 적용, `DP_ENABLED` 토글)
- [x] `src/metrics.ts` — Prometheus `/metrics` (counters, gauges, histograms), 의존성 없음
- [x] `src/routes/api.ts` — `/metrics` 엔드포인트 추가
- [x] `Dockerfile` — Multi-stage Node 20 Alpine, better-sqlite3 네이티브 컴파일
- [x] `docker-compose.yml` — app + 데이터 볼륨 + Ollama 프로필 (GPU 패스스루)
- [x] `.dockerignore` — node_modules, dist, data, tests 제외
- [x] `README.md`, `README_EN.md` — v0.5 완료 + v0.6 계획 업데이트
- [x] `npm run typecheck` → 정상 통과

### v0.6 계획
1. [ ] VS Code 확장 플러그인
2. [ ] 오탐 피드백 루프
3. [ ] fine-tuned 모델 평가 파이프라인
4. [ ] pre-commit hook 통합 코드

## 2026-06-07 — v0.5 설치 마법사 + Ollama 멀티 모델 + 스토리지 엔진

### 완료
- [x] `src/setup.ts` — 대화형 설치 마법사 전면 개편 (LLM 다중 선택, Ollama 설치·모델 pull)
- [x] `src/config.ts` — `STORAGE_ENGINE` 필드 추가 (sqlite/json, 기본 sqlite)
- [x] `.env.example` — `STORAGE_ENGINE=sqlite` 항목 추가
- [x] `docs/Storage_Engine_Comparison.md` — SQLite vs RocksDB 전문 비교 평가 (304줄)
- [x] Ollama 5종 모델 비교표 + 추천: deepseek-r1:8b, llama3.1, mistral, codestral, securereview-7b
- [x] 보안 파인튜닝 모델 `vitorallo/securereview-7b-mlx-4bit` 지원 (Apple Silicon 자동 감지)
- [x] 멀티 Ollama 교차검증 가이드 (LLM_PROVIDERS=ollama,ollama-secondary, LLM_MODE=majority)
- [x] `package.json` → `0.5.0`, 모든 README/DEVELOPMENT_LOG 갱신
- [x] `README.md`, `README_EN.md` — v0.4→v0.5 로드맵 + 업데이트 내역 갱신

### v0.5 계획
1. [ ] Docker 이미지 (SQLite + Ollama + 대시보드)
2. [ ] SQLite 마이그레이션 (JSON → SQLite WAL)
3. [ ] SARIF 결과 내보내기
4. [ ] Differential Privacy 전처리
5. [ ] 오탐 피드백 루프
6. [ ] Prometheus 메트릭

## 2026-06-07 — v0.4 코드 리뷰 버그 패치 + 문서 갱신

### 완료
- [x] `llm-harness.ts` — `AbortController`/`timeoutId` try 밖으로 호이스트 (`catch`에서 `clearTimeout(0)` 무동작 → `clearTimeout(timeoutId)`)
- [x] `llm-harness.ts` — `validateLlmScanResult()` 스키마 검증 + `containsCleartextSecret()` cleartext 유출 가드 추가
- [x] `cli.ts` — 버전 표시 `v0.2.0` → `v0.4.0` (`index.ts`와 불일치 해소)
- [x] `scan-runner.ts` — 캐시 해시 `createHash('md5')` → `createHash('sha256')` (FIPS 호환)
- [x] `candidate-filter.ts` — `simple-git` 에러 핸들링 `err.code` → `/exited with code 1/` 메시지 정규식 검사
- [x] `git-monitor.ts` — `parseDiff()` 내 미사용 `filePattern` global regex 제거
- [x] `git-monitor.ts` — GitHub clone URL 토큰 노출 방지 → `.netrc` 파일로 대체
- [x] `DEVELOPMENT.md` §8 — 설계적 개선 필요 사항 (7건) + 추가 필요 기능 (9건)
- [x] `DEVELOPMENT.md` §9 — 경쟁 솔루션 대비 단점 및 보강 방안 (8건) + 우선순위 액션 Top 5
- [x] `README.md` — `0ae76d4` 버전으로 복원 (vibe-investing 한글 콘텐츠)
- [x] `LAON_VaultGuard/README.md` — 2026-06-07 업데이트 내역 § 추가
- [x] `DEVELOPMENT_LOG.md` — 본 항목 갱신
- [x] `01.Trading Strategy/ARDS-Defense/` — 중복 소문자 `readme.md` 제거 (macOS case-insensitive FS 충돌)
- [x] `npm run typecheck` → 정상 통과

### 검토 리포트
- 리포트 위치: `~/Downloads/LAON_VaultGuard_Review.md` (종합 검토 + 버그 패치 상태 포함)
- 총 7건 코드 버그 수정 (1건 오탐, 1건 의존성 추가 보류)
- 설계 개선 7건 + 추가 기능 9건 → `DEVELOPMENT.md` §8~§9에 문서화

## 2026-06-07 — v0.2.0 크로스플랫폼 + 이메일 리포트

### 완료
- [x] 크로스플랫폼: macOS, Linux, Windows (WSL) 공식 지원
- [x] `config.ts` — platform detection (`darwin`/`linux`/`win32`)
- [x] `alert-engine.ts` — nodemailer 이메일 알람 (실시간/일간/주간 HTML)
- [x] `scheduler.ts` — 일간(9am)/주간(Mon 9am) 리포트 cron
- [x] `db.ts` — `alert_config.json` 저장소, 채널별 토글
- [x] `routes/api.ts` — `GET/PUT /api/alerts/config`, OAuth 엔드포인트
- [x] `public/index.html` + `dashboard.js` — 알람 설정 UI, GitHub OAuth 패널
- [x] `src/oauth.ts` — GitHub App OAuth (token exchange, repo listing)
- [x] `src/git-monitor.ts` — GitHub 원격 레포 shallow clone + cleanup
- [x] `docs/Slack.md`, `docs/E2E_TEST.md`, `docs/GitHub_OAuth.md`
- [x] `package.json` v0.2.0, `npm run typecheck`/`build` 통과

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
