# 01. Trading Strategy

vibe-investing 레포의 트레이딩 전략 라이브러리입니다. 백테스트 데이터, Python 봇, 칼럼, 다국어 퀀트 프롬프트가 함께 위치합니다.

→ [메인 README로 돌아가기](https://github.com/gameworkerkim/vibe-investing/blob/main/README.md)

---

## 폴더 구성

이 폴더는 4개의 하위 자산으로 구성되어 있습니다.

| 폴더 | 핵심 자산 | 형식 |
| --- | --- | --- |
| [Awesome claude quant scripts](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts) | Claude 기반 재현 가능한 퀀트 스크립트 라이브러리 (Dividend, Pharma KR/EN/CN, AI Supercycle) | 스크립트 + 칼럼 + 학술 + 다국어 |
| [Investment Strategy Based on Bitcoin and Nasdaq Coupling](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling) | BTC-QQQ 커플링 분석 + 547줄 Python 봇 + 6 regime 분류 | 칼럼 + Python 봇 + CSV 4종 |
| [Luxury investment strategy](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Luxury%20investment%20strategy) | LVMH/Hermès/Kering 명품 섹터 6년 데이터 + 3단계 포트폴리오 | 칼럼 + CSV 4종 + 백테스트 225건 |
| [AI-hedge-fund](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/AI-hedge-fund) | virattt/ai-hedge-fund 멀티 페르소나 분석 + GuruAgents 학술 결과 | 분석 보고서 |

---

## 주요 자산

### Awesome Claude Quant Scripts — 가장 활발히 업데이트 중

[전체 문서 보기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts)

이 레포에서 가장 활발하게 업데이트되는 폴더입니다. Claude 기반 *재현 가능한 퀀트 프롬프트 + 결과물 + 학술 검증*이 함께 위치합니다.

3개 하위 폴더:

- **Dividend growth prompt** — 배당 성장주 universe 프롬프트 + Cross-Lingual LLM 학술 검증 (SSRN IN REVIEW) + MSFT 사례 칼럼 v2 (6개 LLM 11/11 매수 합의 → 5월 -7% 하락)
- **Pharma growth prompt** — 미국 제약 LONG 7 + SHORT 3 (FDA Orange Book + ClinicalTrials.gov NCT 1차 출처 강제) — 한국어 / 영어 / 중국어 동시 제공
- **AI Supercycle Investment Quant Strategy** — AI 인프라 사이클의 시점적 정량 전략

이 폴더의 차별점:

- 단일 LLM 답변 의존이 아닌 *다국어 검증 + 1차 출처 강제* 의 재현 가능한 프롬프트 패턴
- 칼럼·학술 working paper·CSV 데이터·다국어 프롬프트가 *같은 폴더에* 함께 존재 → 사용자가 fork 하여 본인 universe에 즉시 적용 가능
- 메타 메시지 *\"LLM은 엑셀이지 정답을 알려주는 오라클이 아니다\"* 의 시스템 차원 implementation

### Nasdaq-BTC Coupling Bot — 547줄 Python 트레이딩 신호 생성기

[전체 문서 보기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling)

> Those who know the regime, know the trade.
> Regime을 아는 자가 거래를 안다.

BTC-QQQ 30일 rolling correlation 실시간 추적 + 6 regime 자동 분류 + Telegram/Slack 알림까지 엔드투엔드 파이프라인. Binance + Alpaca WebSocket 연동.

547 lines, 10 classes, 18 functions. 실행 모드 4종 (once / paper / backtest / live).

핵심 발견 (2020-2026 BTC-QQQ 데이터):

- 6년 평균 30일 rolling correlation: +0.335
- 2025년 평균 상관계수: 0.52 (2024년 0.23의 2배)
- 2026년 2월 regime swing: 2주 만에 -0.68 → +0.72
- 2026년 4월 현재: -0.20 (10년 중 최저, 역사적 BTC 반등 시그널)
- Medium regime (+0.30~+0.60) 에서 Nasdaq이 BTC를 15~60분 선행
- 비대칭 커플링: BTC는 나스닥 상승 무시, 하락은 따라감

Regime별 파라미터:

| Regime | Signal | Position | Stop Loss | Target | 신뢰도 | 빈도 |
| --- | --- | --- | --- | --- | --- | --- |
| NEGATIVE (<-0.50) | STRONG_LONG_BTC | +15% | -15% | +25% | 85% | 15% |
| DECOUPLING (-0.10~-0.49) | ACCUMULATE_BTC | +8% | -10% | +15% | 65% | 15% |
| LOW (-0.10~+0.30) | NEUTRAL | 0% | — | — | 40% | 25% |
| MEDIUM (+0.30~+0.60) | FOLLOW_NASDAQ | +10% | -8% | +12% | 70% | 54% |
| STRONG (+0.60~+0.80) | RISK_OFF | -5% | -5% | +5% | 75% | 15% |
| EXTREME (+0.80~+1.0) | CRISIS_MODE | -20% | -3% | +3% | 90% | 5% |

알려진 한계: 상관관계는 과거 통계, regime 전환 지연 (30일 window), flash crash 취약, 유동성 가정 위반 가능, API 안정성 의존, 한국 거주자 자동매매는 외환거래법 / 자본시장법 검토 필수.

### Luxury Investment Strategy — 명품 섹터 6년 실증 분석

[전체 문서 보기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Luxury%20investment%20strategy)

> A Birkin bag is forever. An LVMH share is not.
> 버킨 백은 영원하다. LVMH 주식은 그렇지 않다.

중국 경기 침체와 부동산 위기로 촉발된 2024-2025 명품 섹터 역사적 조정 실증 분석. LVMH, Hermès, Kering, Richemont, Ferrari 등 세계 주요 명품 기업 13개 (기업 11 + ETF 2) 의 2020-2026 전 구간 데이터 + 225건의 백테스트 + 저/중/고 위험 3단계 포트폴리오.

핵심 발견:

- 2020-2026 누적 복리: Ferrari +389%, Hermès +311%, Richemont +167%, LVMH +32%, Kering -42%
- 2024년 단년: Kering -39.4%, Burberry -30%, LVMH -13%, Moncler -7.8%
- 3가지 전략 백테스트 (LVMH 단일 종목): DCA -10.87%, Buy-the-Dip -11.11%, 중국 쇼크 역발상 -7.96%
- GLUX ETF 적립식이면 약 +30~40% 추정 (단일 종목 집중의 위험성 입증)

부속 데이터 4종:

- `luxury_companies_etfs_2026.csv` — 13개 투자 대상 상세
- `luxury_performance_2020_2026.csv` — 13 반기별 수익률
- `luxury_backtest_3strategies.csv` — 225건 백테스트 상세 로그
- `luxury_portfolio_by_risk.csv` — 19개 자산 할당안 (저/중/고 위험)

### AI-hedge-fund 페르소나 분석

[전체 문서 보기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/AI-hedge-fund)

virattt/ai-hedge-fund 레포의 멀티 페르소나 구조와 GuruAgents 학술 결과 (CAGR 42.2%) 를 한국 투자자 관점에서 분석한 working report. AI 페르소나 도구의 *작동 원리와 한계*를 정리.

이 분석은 칼럼 8번 (LLM 합의 vs 시장 현실 MSFT v2) 와 학술 자료 A (Cross-Lingual LLM Accuracy v5) 의 *왜 multi-agent 페르소나가 시장을 못 이기는가* 의 메커니즘 분석에 사용됩니다.

---

## 권장 진입 경로

### 재현 가능한 퀀트 프롬프트를 본인 전략에 적용하고 싶은 분

→ [Awesome claude quant scripts](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts) 폴더 README 부터.

특히 Pharma 프롬프트는 *섹터/시장 교체만으로* 본인 universe에 즉시 적용 가능합니다 (KR / EN / CN 동시 제공).

### 실시간 트레이딩 신호를 보고 싶은 분

→ [Coupling Bot](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling) 의 `python nasdaq_btc_coupling_bot.py --mode once` 로 현재 BTC-Nasdaq regime 즉시 확인.

### 명품·럭셔리 섹터에 관심 있는 분

→ [Luxury investment strategy](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Luxury%20investment%20strategy) 의 칼럼 + CSV 4종.

### AI 페르소나 도구의 작동 원리를 이해하고 싶은 분

→ [AI-hedge-fund 분석](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/AI-hedge-fund) + 칼럼 8번 (LLM 합의 vs 시장 현실) + 학술 자료 A (Cross-Lingual LLM Accuracy v5) 3개를 함께 읽기.

---

## 알려진 한계 (공통)

이 폴더의 모든 자산에 적용되는 공통 한계입니다.

- 백테스트 결과는 백테스트상 이상적 시나리오 — 실거래에서 slippage, commission, 세금, 파이프라인 지연으로 실제 수익률 낮아짐
- 시장 regime 의존성 — 2024-2026 AI 랠리에서 검증된 결과가 다른 regime (약세장, 섹터 로테이션) 에서도 동일하게 작동한다는 보장은 없음
- LLM 비용 — 일부 도구는 Opus 기준 월 $200~400
- 한국 거주자 외환거래법 / 자본시장법 검토 필수
- AI 페르소나는 실제 투자 거장의 의견이 아닌 LLM의 narrative 시뮬레이션

각 자산별 추가 한계는 해당 폴더 README 또는 칼럼 본문 참조.

---

## Disclaimer

모든 자산은 연구·교육 목적입니다. 시장 구조 분석은 통계적·학술적 논평이며 특정 주체를 지목하지 않습니다. 자세한 내용은 [메인 README의 Disclaimer](https://github.com/gameworkerkim/vibe-investing/blob/main/README.md#disclaimer) 참조.
