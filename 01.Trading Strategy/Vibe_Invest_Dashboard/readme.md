# Vibe Investing — 통합 퀀트 대시보드

룰 기반 퀀트 전략의 시그널과 미국 시장 현황·뉴스 요약을 단일 웹 페이지로 통합한 대시보드.
Cloudflare 무료 티어 + Azure 무료 티어 + DeepSeek로 운영.

> **원칙**: "LLM은 엑셀이지 오라클이 아니다" — 모든 시그널은 룰 기반이며,
> LLM(DeepSeek)은 뉴스 요약·정리 도구로만 사용한다.
>
> 🚩 **1차 출시 = ARDS + AMQS**. MU_Hynix 는 Phase 2 보류(KRX 소스·statsmodels 난점).

⚠️ **본 사이트의 모든 시그널은 룰 기반 백테스트 산출물이며, 투자 자문이나 매수·매도 권유가 아닙니다.**

## 문서
- [`VIBE-INVESTING-DEV-GUIDE.md`](./VIBE-INVESTING-DEV-GUIDE.md) — 전체 개발 가이드 & 화면 가이드 (기획)
- [`CLAUDE.md`](./CLAUDE.md) — 프로젝트 규칙·구조 (작업 시 우선 참조)
- [`docs/STRATEGY-ANALYSIS.md`](./docs/STRATEGY-ANALYSIS.md) — 3개 전략 룰·입출력 분석 (포팅 근거)

## 아키텍처 (Cloudflare Pages, 무료 티어)
- **Pages** = 정적 프론트 + **Pages Functions**(`functions/api/*` = HTTP API)
- **Cron Worker**(`cron-worker/`) = 스케줄 작업(Pages 가 Cron 미지원)
- **D1 + R2** = 양쪽 공유. 주기 데이터는 크론이 미리 저장 → API 읽기 + CDN 엣지 캐시
- 뉴스 요약은 AIInvestor(Azure) 앱에서 `/api/ingest/news` 로 전송

```
functions/api/   Pages Functions (HTTP API)
shared/          공용 로직 (ingest, http, 추후 시그널 엔진)
cron-worker/     스케줄 전용 Worker
frontend/        정적 프론트 (src·public·dist)
migrations/      D1 SQL
docs/            분석·프롬프트 문서
```

## 진행 상태
| # | 단계 | 상태 |
|---|---|---|
| 1 | 전략 분석 → `docs/STRATEGY-ANALYSIS.md` | ✅ |
| 2 | Pages/Cron 설정 + `migrations/0001_init.sql` | ✅ |
| 3 | `/api/ingest/news`(HMAC) + 단위테스트 | ✅ |
| 4 | Pages + Pages Functions + Cron Worker 재구성 | ✅ |
| 5 | 시그널 TS 포팅 (ARDS·AMQS) | ✅ Python 골든 일치 |
| 6 | Cron Worker | ◐ 일1회 시그널 ✅ / 10분 시세 스텁(키 필요) |
| 7 | API (dashboard·news·movers·rankings·search·track) | ✅ 로컬 D1/R2 검증 |
| 8 | 프론트 (PART B, 전략 카드 2장) | ⬜ |
| 9 | AIInvestor 뉴스 함수 연결 | ⬜ |
| 10 | 배포 + Python 병행 검증 | ⬜ |

## 로컬 개발
```bash
npm install
npm run build:frontend     # frontend/dist 생성
npm run dev                # wrangler pages dev (프론트 + API)
npm run dev:cron           # 크론 핸들러 테스트
npm run db:migrate:local   # D1 로컬 마이그레이션
npm test                   # vitest
```
> Cloudflare/Azure 계정·API 키 확보 전까지 로컬 모드 + mock 데이터로 검증한다.
