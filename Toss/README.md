# Toss × AMQS 퀀트 대시보드 — 투자 철학을 이해하자.

> 토스증권 **Open API**로 한국인이 실제로 사고·검색하는 국내 주식·ETF에
> **Adaptive Momentum Quant Strategy (AMQS)** 의 룰을 *기계적으로* 적용해
> **매수 / 보유 / 매도** 를 한 화면에서 판단하는 대시보드.

![대시보드 히어로 — 레짐 배너와 ETF 시그널](docs/01-hero.png)

> 사용법(설치·실행·API 키 연동)은 **[사용 설명서(GUIDE.md)](./GUIDE.md)** 를 보세요.
> 이 문서는 *왜 이렇게 만들었는가* — 전략의 철학과 한계 — 를 다룹니다.

---

## 1. 왜 모멘텀인가?

> *"The trend is your friend until the end when it bends."* — Ed Seykota

모멘텀(추세 추종)은 30년간 학계와 실무 양쪽에서 살아남은 **가장 강건한 알파 팩터** 중 하나입니다
(Jegadeesh & Titman 1993, Asness·Moskowitz·Pedersen 2013). 단순합니다 —
**오르는 것은 계속 오르고, 빠지는 것은 계속 빠지는 경향**이 있다.

하지만 모멘텀에는 치명적 약점이 있습니다. **추세 전환점에서 가장 크게 깨진다**
(Daniel & Moskowitz 2016, "Momentum Crashes"). V자 반등장에서 모멘텀 팩터는
며칠 만에 −15~30% 를 토해냅니다.

그래서 AMQS의 철학은 한 문장으로 요약됩니다

> **"미래를 예측하지 않는다. 현재의 추세를 타되, 추세가 바뀌면 빠르게 빠진다."**

알파는 *추세를 맞히는 것* 이 아니라 *추세가 꺾일 때 손실을 통제하는 것* 에서 나옵니다.

시장이 좋을 때 산책을 하고 비가 오면 진창에 덜 빠지고 비를 피하는 전략이 바로 Adaptive Momentum Quant Strategy (AMQS)의 투자 퀀트 전략입니다.
이번 반도체 시장처럼 끝없이 오르는 강세장이라면 적립식 투자가 가장 큰 수익을 얻을 수 있습니다. 

---

## 2. AMQS의 3대 메커니즘

원본 전략 백테스트(미국, 2024–2026)는 QQQ·반도체·AI 바스켓을 모두 이긴
**CAGR 38.75% · MDD −16.9% · Sharpe 1.33** 을 기록했습니다. 그 핵심은 세 가지입니다.
([AMQS 원문 →](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Adaptive%20Momentum%20Quant%20Strategy%20(AMQS)))

### ① 다중 시간축 모멘텀 — 노이즈를 지운다

단일 기간 수익률은 노이즈가 큽니다. 그래서 **4개 시간축을 z-score로 합성**합니다.

```
점수 = 0.50·Z(12-1) + 0.30·Z(6-1) + 0.15·Z(3-1) + 0.05·Z(1/변동성)
```

- `12-1` = 12개월 전 → **1개월 전** 수익률. *최근 1개월을 일부러 제외* — 단기 평균회귀(되돌림)에 휩쓸리지 않기 위함.
- 변동성 항(`1/Vol`)은 *같은 추세라면 덜 흔들리는 종목* 에 가점.
- `Z()` 는 화면에 띄운 종목 집합(universe) **내부에서의 상대 순위**. 절대 수익률이 아니라 *또래 대비 얼마나 강한가* 를 봅니다.

### ② 거시 레짐 필터 — 약세장엔 자동 방어

모멘텀만 믿으면 크래시에 당합니다. 그래서 시장 국면을 먼저 봅니다.
원본은 QQQ 200일선 + VIX를, 본 대시보드는 **국내 시장에 맞게 KODEX 200(코스피200 프록시)** 으로 판정합니다.

| 레짐 | 조건(국내 적용) | 행동 |
| --- | --- | --- |
| **위험 선호 (RISK_ON)** | KODEX 200 > 200일선 · 변동성 안정 | Top 모멘텀 풀 투자 |
| **위험 회피 (RISK_OFF)** | 200일선 이탈 또는 20일 변동성 > 30% | 비중 축소 · 신규 매수 강도 하향 |
| **방어 (DEFENSIVE)** | 5일 수익률 < −8% | 신규 매수 중단 · 방어 전환 |

> VIX에 대응하는 국내 공포지수(VKOSPI)가 토스 Open API에 없어, **지수 20일 실현 변동성** 으로 대체했습니다.

### ③ 빠른 회전 — 리더십 로테이션을 잡는다

주도 섹터는 빠르게 바뀝니다(반도체 → 전력 인프라 → 방산 …). 월간 리밸런싱은 이를 놓칩니다.
AMQS는 **주간 단위**로 리더십 교체를 따라갑니다. 이 대시보드는 그 *현재 시점 스냅샷* 을 보여주는 역할입니다.

---

## 3. 이 대시보드는 무엇을 하나?

위 룰을 **한국인이 실제로 보유·검색하는 종목** 에 그대로 적용합니다.

- **섹터별 대표주 8섹터 × 10종목** — 반도체/AI · 2차전지 · 자동차 · 인터넷/게임 · 바이오 · 방산/조선 · 금융 · 엔터
- **인기 ETF 10종목** — KODEX 200 · TIGER 미국S&P500/나스닥100/필반 등
- **종목 검색** — 종목명·6자리 코드로 동일한 룰을 즉시 적용 (공유 링크 `?q=삼성전자` 지원)

각 종목은 모멘텀 점수(0~100), 12-1·6-1 모멘텀, 60일 변동성, **−12% 손절선**, 그리고 *왜 이 시그널인가* 의 근거까지 보여줍니다.

### 종목별 시그널 룰

| 조건 | 시그널 |
| --- | --- |
| 60일 고점 대비 **−12% 이탈** (트레일링 스탑) |  **매도** |
| composite z ≥ **+0.5** (또래 상위권) | **매수** |
| composite z ≤ **−0.5** (또래 하위권, 추세 약화) |  **매도** |
| 그 외 |  **보유** |

레짐이 **방어/위험회피** 면 매수 후보는 보유·회피로 자동 강등됩니다. *방어가 공격보다 먼저* — 이것이 철학의 핵심입니다.

![종목 검색 결과 — 모멘텀 점수·손절선·근거](docs/02-search.png)

![전체 개요 — 레짐·ETF·섹터](docs/03-overview.png)

---

## 4. 반드시 읽어야 할 주의점

> **이 대시보드는 투자 권유나 수익 보장이 아닙니다. 모든 투자 판단과 책임은 전적으로 본인에게 있습니다.**
> 저자는 면허가 있는 투자자문업자가 아니며, 어떤 종목의 매수·매도도 권유하지 않습니다.

1. **기계적 룰일 뿐, 정답이 아니다.** 시그널은 위 공식을 그대로 계산한 결과입니다. 펀더멘털·뉴스·실적·수급을 전혀 보지 않습니다.

2. **모멘텀 크래시 위험.** 모멘텀은 *추세 전환점* 에서 단기 −15~30% 손실이 구조적으로 발생할 수 있습니다(2009·2020·2025 DeepSeek 쇼크 등). 손절 룰이 *실거래에서도 작동* 하는지가 가장 중요합니다.

3. **국내 백테스트 결과 — 강세장에선 단순보유에 뒤졌다.** 국내 3년 백테스트([backtest/BACKTEST.md](./backtest/BACKTEST.md))를 돌려보니, *폭락 없는 강세장* 구간에서는 **AMQS가 KODEX 200 단순보유에 수익·낙폭·Sharpe 모두 뒤졌습니다.** 모멘텀 종목선택 자체는 동일가중 보유 대비 초과수익을 냈지만, 방어 오버레이가 상승을 깎았습니다. AMQS의 가치는 *급락·전환장의 낙폭 통제* 에 있습니다. (원본의 미국 38.75% CAGR·−16.9% MDD는 미국 2024–2026 수치이며, 본 국내 백테스트의 데이터 한계도 리포트에 명기.)

4. **세금·거래비용.** 국내 주식 회전율 250% 환경에서는 거래비용·세금이 수익을 크게 잠식합니다. 백테스트 수익률은 실효 수익률과 다릅니다.

5. **MOCK 모드 데이터는 가짜다.** 토스 API 키가 없으면 종목코드 해시 기반 **합성 가격** 으로 동작합니다(상단 노란 배너로 표시). 이 가격·시그널은 **실제 시세와 무관** 하며 *UI·로직 시연용* 입니다.

6. **토스 Open API는 사전 신청 단계.** 2026년 6월 기준 정식 출시 전이라 응답 필드명이 바뀔 수 있고, 키 발급에 시간이 걸립니다. 발급 절차는 [GUIDE.md](./GUIDE.md) 참고.

7. **종목 구성은 예시 큐레이션.** 섹터/ETF 종목은 개인 선호·증권사 톱픽을 참고한 *예시* 이며, 시장 변화에 맞게 직접 교체해야 합니다([src/universe.js](./src/universe.js)).

---

## 5. 시작하기

```bash
cd Toss
npm install
npm start          # http://localhost:3000 (키 없으면 MOCK 모드로 즉시 실행)
```

토스 Open API 키 연동, 서버 API, 종목 교체 방법은 **→ [사용 설명서(GUIDE.md)](./GUIDE.md)**.

---

## 관련 문서

| 문서 | 내용 |
| --- | --- |
| [GUIDE.md](./GUIDE.md) | **사용 설명서** — 설치 · API 키 연동 · 서버 API · 종목 교체 |
| [backtest/BACKTEST.md](./backtest/BACKTEST.md) | **국내 3년 백테스트 리포트** — AMQS vs KODEX 200 vs 동일가중, 정직한 성과 분석·데이터 한계 |
| [docs/Toss_OpenAPI_Guide.md](./docs/Toss_OpenAPI_Guide.md) | **토스증권 Open API 기술 분석** — 인증·토큰 정책, 20개 엔드포인트, 6가지 활용 시나리오(트레이딩 봇·LLM 연동·백테스트), 설계 제약, 정보 검증 등급 |
| [docs/Toss_OpenAPI_Analysis.pdf](./docs/Toss_OpenAPI_Analysis.pdf) | 위 분석 문서의 **PDF 버전** |
| [docs/](./docs/readme.md) | 문서·스크린샷 인덱스 |

---

## 링크

-  **GitHub**: [github.com/gameworkerkim/vibe-investing](https://github.com/gameworkerkim/vibe-investing)
-  **이 프로젝트 소스**: [/Toss](https://github.com/gameworkerkim/vibe-investing/tree/main/Toss)
-  **AMQS 전략 원문**: [Adaptive Momentum Quant Strategy (AMQS)](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Adaptive%20Momentum%20Quant%20Strategy%20(AMQS))

---

**전략 원작자**: 김호광 (Dennis Kim / HoKwang Kim) · Independent Researcher, Betalabs Inc. CEO
[ORCID](https://orcid.org/0009-0002-0962-2175) · [@gameworkerkim](https://github.com/gameworkerkim) · MIT License

> *"In momentum, you don't predict the future. You ride the present and exit fast when the present changes."*
