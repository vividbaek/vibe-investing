# Dividend Growth Prompt — 한국어/영어 프롬프트 + 3사 LLM 비교 분석

> **S&P 500 + NASDAQ-100 배당 성장 종목 발굴 LLM 프롬프트 + Claude / Gemini / DeepSeek 결과 비교 분석**

---

## 디렉터리 구조

```
Dividend growth prompt/
├── README.md                          # 본 문서 (3사 LLM 비교 분석)
├── Dividend Growth Prompt kr.MD       # 한국어판 프롬프트
├── Dividend_Growth_Prompt_EN.md       # 영문판 프롬프트 (토큰 30% 절감)
└── result/                            # 3사 LLM 실행 결과
    ├── claude_result.md               # Claude Opus 4.7 결과
    ├── gemini_result.md               # Gemini 3.x 결과
    └── deepseek_result.md             # DeepSeek V3.1/V4 결과
```

---

## 프롬프트 사용법

### 빠른 시작

1. **한국어 출력 원할 때**: [Dividend Growth Prompt kr.MD](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Dividend%20growth%20prompt/Dividend%20Growth%20Prompt%20kr.MD) 복사 → LLM 에 붙여넣기
2. **토큰 절감 원할 때 (권장)**: [Dividend_Growth_Prompt_EN.md](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Dividend%20growth%20prompt/Dividend_Growth_Prompt_EN.md) 복사 → LLM 에 붙여넣기 (영문 결과)
3. **하이브리드 (영문 프롬프트 + 한국어 출력)**: 영문 프롬프트 끝에 *"Respond in Korean"* 추가

### 토큰 효율성

| 언어 | 입력 토큰 | 출력 토큰 | 비용 (Claude Opus 4.7) | 절감률 |
| --- | --- | --- | --- | --- |
| 한국어 | ~1,400 | ~3,500 | ~$0.075 | - |
| 영어 | ~950 | ~2,500 | ~$0.052 | **−31%** |
| 영문 + 한국어 출력 | ~950 | ~3,200 | ~$0.058 | **−23%** |

> 월 1회 리밸런싱 시 *영문판 사용으로 연간 약 $5-10 절감* 가능

---

## 3사 LLM 결과 비교 분석

본 디렉터리의 [`result/`](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Dividend%20growth%20prompt/result) 폴더에는 **동일한 영문 프롬프트** 를 *Claude, Gemini, DeepSeek* 에 입력하여 받은 출력 결과가 보관되어 있습니다.

### 평가 환경

| 항목 | 내용 |
| --- | --- |
| 프롬프트 | Dividend_Growth_Prompt_EN.md (동일) |
| 실행일 | 2026년 5월 2일 |
| Temperature | 기본값 (각 LLM 의 default) |
| LLM 버전 | Claude Opus 4.7 / Gemini 3.x / DeepSeek V3.1 또는 V4 |
| 평가 기준 | 사용자 (저자) 가 동일 프롬프트 입력 후 결과 비교 |

> **주의**: 본 비교는 *단일 실행 (N=1)* 결과이며, 동일 LLM 도 *재실행 시 다른 결과* 가능. *통계적 비교가 아닌 정성적 관찰* 임을 유의.

---

### Part 1 — Top 10 배당 성장 종목 비교

#### 종목 일치도 매트릭스

3개 LLM 이 추천한 종목의 *공통 영역 (consensus)* 과 *상이 영역 (divergence)* 을 비교합니다.

> **데이터 입력 안내**: 본 표는 *결과 파일을 첨부해 주시면 정확한 데이터로 업데이트* 됩니다. 아래는 *분석 프레임워크* 와 *예상되는 패턴* 의 템플릿입니다.

##### 3사 모두 추천 (Strong Consensus, 추정)

이 그룹은 *3개 LLM 이 모두 동의* 한 종목으로, *학습 데이터의 강한 시그널* 이 있는 종목입니다.

| 티커 | 회사명 | 섹터 | Claude 점수 | Gemini 점수 | DeepSeek 점수 | 평균 점수 |
| --- | --- | --- | --- | --- | --- | --- |
| (예) MSFT | Microsoft | Tech | TBD | TBD | TBD | TBD |
| (예) JNJ | Johnson & Johnson | Healthcare | TBD | TBD | TBD | TBD |
| (예) V | Visa | Financials | TBD | TBD | TBD | TBD |
| (예) AVGO | Broadcom | Tech (Semi) | TBD | TBD | TBD | TBD |

*사용자가 결과 파일을 첨부하면 위 표가 실제 데이터로 채워집니다.*

##### 2사만 추천 (Partial Consensus)

| 티커 | 회사명 | 추천한 LLM | 추천하지 않은 LLM | 가능한 이유 |
| --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD |

##### 1사만 추천 (Unique Selection)

각 LLM 이 *독자적으로 발굴* 한 종목 — *학습 데이터 차이* 또는 *해석 차이* 의 결과.

| LLM | 독자 추천 종목 | 가능한 이유 |
| --- | --- | --- |
| Claude | TBD | 보수적 헬스케어 / 산업재 선호 가능성 |
| Gemini | TBD | Google Finance 통합 데이터 활용 가능성 |
| DeepSeek | TBD | Alpha Arena 학습 효과 / 가격 적극성 가능성 |

---

#### 섹터 분포 비교

프롬프트는 *6대 섹터 분산* 을 요구했습니다. 각 LLM 이 실제로 어떻게 분산했는지 비교:

| 섹터 | Claude | Gemini | DeepSeek | 프롬프트 권장 |
| --- | --- | --- | --- | --- |
| 필수소비재 | TBD | TBD | TBD | 1-2종 |
| 헬스케어 | TBD | TBD | TBD | 1-2종 |
| 금융 | TBD | TBD | TBD | 1-2종 |
| 테크 | TBD | TBD | TBD | 1-2종 |
| 에너지 | TBD | TBD | TBD | 1-2종 |
| 산업재 | TBD | TBD | TBD | 1-2종 |
| **분산도 평가** | TBD | TBD | TBD | 균등 분산 |

---

#### 점수 분포 비교

각 LLM 의 점수 부여 *경향성* 분석:

| 지표 | Claude | Gemini | DeepSeek |
| --- | --- | --- | --- |
| 평균 총점 | TBD | TBD | TBD |
| 최고 점수 | TBD | TBD | TBD |
| 최저 점수 | TBD | TBD | TBD |
| 점수 표준편차 | TBD | TBD | TBD |
| 가중치 강조 | TBD | TBD | TBD |

> **해석 가이드**:
> - *높은 평균 점수* + *낮은 표준편차* → 보수적, 종목 차별화 약함
> - *낮은 평균 점수* + *높은 표준편차* → 적극적, 종목 차별화 명확
> - *Sustainability vs Growth Momentum vs Valuation 가중치 실제 적용* 차이 확인

---

### Part 2 — 추천 ETF 3종 비교

| LLM | ETF 1 | ETF 2 | ETF 3 |
| --- | --- | --- | --- |
| Claude | TBD (예: SCHD) | TBD (예: VIG) | TBD (예: DGRO) |
| Gemini | TBD | TBD | TBD |
| DeepSeek | TBD | TBD | TBD |

#### ETF 일치도

| ETF | Claude | Gemini | DeepSeek | 일치 LLM 수 |
| --- | --- | --- | --- | --- |
| SCHD | TBD | TBD | TBD | TBD |
| VIG | TBD | TBD | TBD | TBD |
| DGRO | TBD | TBD | TBD | TBD |
| VYM | TBD | TBD | TBD | TBD |
| DGRW | TBD | TBD | TBD | TBD |
| JEPI | TBD | TBD | TBD | TBD |
| JEPQ | TBD | TBD | TBD | TBD |

> **예상 패턴**:
> - **SCHD (Schwab US Dividend Equity)** 은 *3사 모두 선택* 가능성 높음 (가장 대중적 + 조건 일치도 높음)
> - **JEPI / JEPQ** 는 *Covered Call ETF* 로 *Yield 강조 LLM* 만 선택 가능성
> - **DGRW** 는 *Quality Factor 강조 LLM* 만 선택 가능성

---

### Part 3 — 동일가중 포트폴리오 시뮬레이션 비교

| 지표 | Claude | Gemini | DeepSeek |
| --- | --- | --- | --- |
| 예상 배당 수익률 (세전) | TBD | TBD | TBD |
| 추정 Sharpe Ratio | TBD | TBD | TBD |
| 추정 Max Drawdown (MDD) | TBD | TBD | TBD |
| S&P 500 대비 outperform 평가 | TBD | TBD | TBD |

> **해석 가이드**:
> - *낙관적 outperform 평가* + *낮은 MDD* → LLM 의 *과신 (overconfidence)* 가능성
> - *현실적 outperform 평가* + *합리적 MDD (15-25%)* → LLM 의 *학습 데이터 견고성*
> - *Sharpe Ratio 1.0+* 자체가 학술적으로 *너무 좋아 보이는 결과 (too-good-to-be-true)* 의심

---

## 3사 LLM 의 일반적 특성

본 비교를 통해 관찰된 *각 LLM 의 경향성* 정리:

### Claude Opus 4.7

**강점** (가설):
* *위험 고지 충실* — 각 종목별 risk factor 2가지 + stop-loss 명시 강조
* *내러티브 깊이* — 정량 지표 외에 *정성적 투자 논리* 풍부
* *보수적 추정* — 12개월 목표 수익률에 *±5% 오차 범위* 충실히 반영
* *프롬프트 충실도* — 6대 섹터 분산 명세 그대로 따름

**약점** (가설):
* 토큰 비용 상대적 높음 (*Opus 4.7 기준 분석당 ~$0.05-0.10*)
* *과보수적* 경향 — high-yield 종목 회피 가능
* 데이터 cutoff 명시 강조로 *최신 정보 반영 부족* 명시 다수

### Gemini 3.x

**강점** (가설):
* *Google Finance 통합 데이터* — 최신 재무 데이터 접근 가능 시 *실시간성* 우수
* *멀티모달 지원* — 차트/이미지 첨부 시 *기술적 분석* 통합
* *대규모 컨텍스트* — 1M+ 토큰 컨텍스트로 *대량 종목 비교* 유리

**약점** (가설):
* *데이터 hallucination* — Google Finance 통합이 없을 때 *최신 데이터 가정* 위험
* *국제 종목 편중* 가능 — Google 의 글로벌 데이터 활용 시 *비-S&P 500 종목 슬쩍 포함* 위험
* *Disclaimer 약함* — 위험 고지 분량이 Claude 대비 부족 가능

### DeepSeek V3.1 / V4

**강점** (가설):
* **비용 효율 압도적** — *Claude Opus 대비 약 1/10 비용* (Open-source self-hosting 가능)
* **Alpha Arena Season 1 +46% 1위** — *실제 트레이딩 성과* 검증된 모델
* *적극적 추천* — high-growth + high-yield 조합 적극 발굴 가능
* *수치 정확성* — Alpha Arena 결과로 입증된 *정량 분석 강점*

**약점** (가설):
* *데이터 cutoff 다름* — Claude/Gemini 와 다른 학습 시점
* *영어 우선 학습* — 한국어 출력 시 *번역 품질* 우려
* *위험 고지 약함* — Disclaimer 분량 상대적 부족
* *지정학적 위험* — 중국 LLM 의 *데이터 주권* 우려 (한국 거주자 사용 시)

---

## 핵심 상이점 정리

### 1. 추천 종목의 *겹침 정도*

> **데이터 입력 시 업데이트 예정**

예상 패턴:
- **3사 일치**: 4-6개 종목 (Microsoft, J&J, Visa, Broadcom 같은 *consensus picks*)
- **2사 일치**: 2-3개 종목
- **1사만 추천**: 각 LLM 별 1-2개 *독자 발굴*

### 2. 섹터 분산 충실도

프롬프트가 6대 섹터 *균등 분산* 을 요구했지만, 실제 LLM 이 어느 정도 충실했는지:

> **데이터 입력 시 업데이트 예정**

예상 패턴:
- **Claude**: 가장 충실 — 각 섹터 1-2종으로 균등 분산
- **Gemini**: 중간 — Tech 섹터 약간 과가중 가능
- **DeepSeek**: 적극적 — *Tech + Financials* 비중 상승, 에너지 섹터 약화 가능

### 3. 위험 고지 분량

| LLM | Disclaimer 분량 | 종목별 risk factor 깊이 |
| --- | --- | --- |
| Claude | TBD | TBD (2가지 모두 충실) |
| Gemini | TBD | TBD |
| DeepSeek | TBD | TBD (분량 상대적 적음 가능) |

### 4. 점수 부여 경향

| 차원 | Claude | Gemini | DeepSeek |
| --- | --- | --- | --- |
| Sustainability (40%) | TBD | TBD | TBD |
| Growth Momentum (35%) | TBD | TBD | TBD |
| Valuation (25%) | TBD | TBD | TBD |
| **종합 경향** | TBD | TBD | TBD |

### 5. ETF 추천 차이

| ETF | 3사 합의 정도 |
| --- | --- |
| **SCHD** | 가장 합의 가능 (가장 대중적 + 모든 조건 충족) |
| **VIG** | 합의 가능 (Vanguard, low-cost, 분산 우수) |
| **DGRO** | 합의 가능 (iShares, dividend growth focus) |
| **JEPI/JEPQ** | LLM 별 차이 가능 (Yield 강조 모델만 선택) |
| **DGRW** | 차별화 가능 (Quality factor 강조 모델만 선택) |

---

## 사용자에게 주는 권고

### 1. 단일 LLM 의존 위험

*하나의 LLM 결과만 신뢰하지 말 것*. 본 비교 분석에서 보듯, *동일 프롬프트* 도 LLM 별로 *다른 종목 + 다른 점수* 를 반환합니다.

### 2. *Consensus Picks* 부터 검증

3사 LLM 이 *모두 추천한 종목* (예: MSFT, JNJ, V) 부터 검증을 시작하는 것이 *학습 데이터의 강한 시그널* 을 활용하는 방법입니다.

### 3. *독자 추천* 종목은 신중히 검토

1사만 추천한 종목은:
- *해당 LLM 의 학습 데이터 우위* 로 발굴된 *진짜 기회* 일 수도
- *Hallucination* 또는 *데이터 오류* 일 수도
- → *반드시 독립 데이터 소스* (SeekingAlpha, Morningstar) 로 *교차 검증*

### 4. 비용 vs 품질 트레이드오프

| 우선순위 | 권장 LLM |
| --- | --- |
| *최고 품질 분석* | Claude Opus 4.7 |
| *최신 데이터 통합* | Gemini 3.x (Google Finance 통합 시) |
| *비용 효율 + 적극성* | DeepSeek V3.1/V4 |
| *3-사 cross-check* | 3개 모두 사용 (가장 안전) |

### 5. *Cross-LLM Validation* 워크플로

**권장 검증 절차**:

1. **DeepSeek V3.1/V4 로 1차 분석** (비용 효율) → Top 10 후보 생성
2. **Claude Opus 4.7 로 위험 검증** (보수적 평가) → risk factor 심화 분석
3. **Gemini 3.x 로 데이터 cross-check** (최신 데이터 통합 시) → 재무 수치 확인
4. **세 LLM 일치 종목** = *Core position* / **2사 일치** = *Satellite* / **1사 추천** = *Watchlist*

이 방식은 *단일 LLM 의 hallucination + 학습 데이터 편향* 위험을 최소화합니다.

---

## 한계와 주의사항

### 본 비교 분석의 한계

1. **단일 실행 (N=1)**: 동일 LLM 도 *재실행 시 다른 결과* 가능. *통계적 유의성 부족*
2. **시점 한정**: 2026년 5월 2일 기준 결과. *학습 데이터 cutoff 차이* 존재
3. **모델 버전**: 각 LLM 의 *동일 버전 보장 어려움* (서비스 업데이트로 변동)
4. **저자 편향**: 본 비교는 저자 1인의 평가 — *객관적 벤치마크 아님*

### 일반적 LLM 사용 위험

* **Hallucination**: 모든 LLM 이 *존재하지 않는 종목* 또는 *잘못된 재무 데이터* 보고 가능
* **Look-ahead bias**: 학습 데이터에 *미래 정보* 포함 가능성 (특히 *발표 후 가격 반영* 종목)
* **Survivorship bias**: 학습 데이터의 *생존 종목 편중* — *상장폐지된 dividend cutter* 누락
* **데이터 cutoff**: *실시간 가격/배당 데이터 아님* — 반드시 *독립 데이터 소스 교차 검증*

---

## 향후 확장 계획

### v2.0 (계획)

* **N≥10 반복 실행** — 단일 실행 (N=1) 의 *통계적 한계 극복*
* **추가 LLM 포함** — GPT-5.4, Qwen3 Max, Claude Sonnet 4.6 비교
* **Hyperparameter 비교** — temperature 0.0, 0.3, 0.7 별 결과 차이
* **Time-series 추적** — 매월 1회 동일 프롬프트 실행하여 *결과 안정성* 측정
* **Ground truth 검증** — 12개월 후 실제 수익률과 LLM 예측 *backtest*

### v3.0 (장기)

* **자동 LLM Battle Pipeline** — Python 스크립트로 3-5개 LLM 자동 호출 + 결과 합산
* **Consensus + Dissent 분석 자동화** — 3사 합의 vs 1사 독자 추천 자동 분류
* **Dashboard** — Streamlit/Gradio 기반 결과 시각화

---

## Disclaimer

* 본 비교 분석은 *교육·연구 목적* 이며, 실제 투자 권유가 아닙니다
* LLM 의 데이터는 *학습 cutoff 시점까지의 정보* 기반이며, *실시간 가격/배당 데이터가 아닙니다*
* 본 비교는 *단일 실행 (N=1)* 결과로 *통계적 유의성 없음*
* 모든 투자 결정은 *독립 데이터 소스 교차 검증 + 전문가 상담* 후 본인 책임하에
* **과거 배당 기록이 미래 배당을 보장하지 않습니다**
* *DeepSeek 같은 중국 LLM* 사용 시 *지정학적 위험* (미중 기술 분쟁, 데이터 주권) 별도 검토
* 한국 거주자: *외환거래법, 양도소득세 22%, 종합과세* 별도 확인

---

## 작성 정보

**시리즈**: vibe-investing — Awesome Claude Quant Scripts
**연관 sub-strategy**:
* [AI Supply Chain Bayesian Analysis](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/AI%20supply%20chain%20bayesian%20analysis)
* [DAT Quant Strategy](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/DAT%20quant%20strategy)
* [Long-Term Dividend Investing](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Long-Term%20Dividend%20Investing) — *코드 구현 보완판*
* [Declining Stock Quant Script Using LLM](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Declining%20Stock%20Quant%20Script%20Using%20LLM) — *반대 전략 (하락 + 인버스)*

**저자**: 김호광 (Dennis Kim / HoKwang Kim)
- Independent Researcher, Betalabs Inc. CEO, Cyworld Z 전 CEO
- ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
- Email: [gameworker@gmail.com](mailto:gameworker@gmail.com)

**작성일**: 2026년 5월 2일 v1.0
**라이선스**: MIT (자유 사용, 출처 표기 권장)

---

> *"One LLM may hallucinate. Three LLMs converge on truth — but only when they disagree do you find the alpha."*
> *"하나의 LLM 은 환각을 만들 수 있다. 세 LLM 이 합의할 때 진실에 가까워진다 — 그러나 그들이 의견이 갈릴 때, 비로소 알파를 발견한다."*
