# Toss 프로젝트 문서 (docs)

`Toss × AMQS 퀀트 대시보드` 관련 문서·자료 모음입니다.
전략 철학과 대시보드 사용법은 상위 폴더의 문서를 먼저 보세요.

## 문서

| 문서 | 설명 |
| --- | --- |
| [Toss_OpenAPI_Guide.md](./Toss_OpenAPI_Guide.md) | **토스증권 Open API 기술 분석 문서** — 인증·토큰 정책, 20개 엔드포인트 전체 리스트, 6가지 활용 시나리오(트레이딩 봇·LLM 연동·백테스트 파이프라인 등), 설계 제약사항, 정보 검증 등급 |
| [Toss_OpenAPI_Analysis.pdf](./Toss_OpenAPI_Analysis.pdf) | 위 분석 문서의 **PDF 버전** (배포·인쇄용) |

## 대시보드 스크린샷

| 파일 | 화면 |
| --- | --- |
| [01-hero.png](./01-hero.png) | 레짐 배너 + ETF 시그널 그리드 |
| [02-search.png](./02-search.png) | 종목 검색 결과 (`?q=삼성전자`) |
| [03-overview.png](./03-overview.png) | 레짐 + ETF + 섹터 전체 개요 |

## 백테스트

| 파일 | 설명 |
| --- | --- |
| [../backtest/BACKTEST.md](../backtest/BACKTEST.md) | **국내 3년 백테스트 리포트** (정직한 성과 분석 + 데이터 한계) |
| [backtest_nav.png](./backtest_nav.png) | NAV·낙폭 비교 차트 |
| [../data/](../data) | 백테스트 로그 CSV (일간 NAV · 리밸런싱 로그 · 종목별 통계) |

## 🔗 상위 문서

- [../README.md](../README.md) — **투자 철학 문서** (왜 이렇게 만들었나 · 주의점)
- [../GUIDE.md](../GUIDE.md) — **사용 설명서** (설치 · API 키 연동 · 서버 API · 종목 교체)
- [../llms.txt](../llms.txt) — AI 에이전트용 프로젝트 요약
