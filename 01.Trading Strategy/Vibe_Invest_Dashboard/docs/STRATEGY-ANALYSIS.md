# 전략 분석 — ARDS · AMQS · MU_Hynix (포팅 기준 문서)

> **버전** v1.0 · 2026-06-06 · 가이드 §6.3 step 1 산출물
> **목적**: 3개 전략의 시그널 룰·입력 데이터·출력 포맷을 정리하고, 각 전략의 native 출력을
> 대시보드 통일 enum(`BUY|SELL|HOLD|SHORT_TERM_RISK|SURGE`)으로 매핑한다.
> **원칙**: 임의 로직 발명 금지. 이 문서는 *지도*이고, 실제 포팅(step 6)은 아래 인용한
> canonical 소스 파일을 **줄 단위로 대조**하며 진행한다. 상수는 소스가 최종 권위.

> 🚩 **1차 출시 범위 (2026-06-06 확정)**: **ARDS + AMQS 2개만** 포팅·노출한다.
> **MU_Hynix 는 1차에서 제외(Phase 2 보류)** — 사유: SK하이닉스(000660) KRX 무료 소스 미해결 +
> statsmodels(ADF 코인티그레이션) TS 대체 난점. 전략 카드도 1차는 2장(ARDS/AMQS).
> 단, D1 `signals.strategy` CHECK 에 `MU_HYNIX` 값은 그대로 두어 Phase 2 추가 시 마이그레이션 불필요.

---

## 0. Canonical 버전 (포팅 대상)

| 전략 | 1차 | Canonical 폴더 (상위 `01.Trading Strategy/`) | 핵심 소스 | 언어/의존성 |
|---|---|---|---|---|
| **ARDS** | ✅ | `ARDS — Adaptive Recession-Defensive Strategy for AI_QQQ/` | `quant/{config,classifier,technical,macro,rates,datafeed,run}.py` | Python · yfinance, pandas, numpy + FRED CSV |
| **AMQS** | ✅ | `Adaptive Momentum Quant Strategy (AMQS) for AI Infra/` | `script/strategy.py` (+ `backtest.py`, `Signal_Bot/`) | Python · yfinance, pandas, numpy |
| **MU_Hynix** | ⏸ Phase 2 | `Awesome claude quant scripts/MU_Hynix/` | `script/mu_hynix_pairs.py`, `Signal_Bot/signal_bot.py` | Python · yfinance, **statsmodels(ADF/OLS)** |

> 동일 계열의 다른 폴더(ARDS-Defense, ARDS 원본, AMQS/M7, AMQS 원본, AIInvestor 서비스)는
> 참고용. 포팅은 위 canonical만 기준으로 한다.

### 출력 → D1 `signals` 테이블 매핑 (공통)
세 전략 모두 일 1회(미 장마감 후) 산출되어 `signals(date, strategy, ticker, signal, score, detail_json)`에
기록된다. `strategy ∈ {ARDS, AMQS, MU_HYNIX}`, `signal`은 아래 각 절의 매핑 결과.
`detail_json`엔 근거 지표 원본을 보존(Phase 2에서 프론트 노출).

---

## 1. ARDS — 침체-방어 국면 분류기 (Regime Classifier)

**성격**: 개별 종목 BUY/SELL이 아니라 **시장 전체 국면(regime)을 1개로 판정**하는 분류기.
주 대상 = S&P500(`^GSPC`) + 나스닥100(`^NDX`). 빅테크/AI 복합체는 breadth·평균 드로다운 계산에 사용.

### 1.1 입력 데이터
- **지수**: `^GSPC`, `^NDX` (yfinance)
- **복합체 18종목** (`config.COMPLEX`): bigtech(AAPL MSFT GOOGL AMZN META TSLA) · ai_semi(NVDA AVGO AMD TSM MU ASML) · ai_infra(VRT SMCI ANET DELL ORCL CEG)
- **FRED 무료 CSV** (키 불필요): `T10Y3M, T10Y2Y, UNRATE, BAMLH0A0HYM2, NFCI, ICSA, PERMIT, DGS2, T5YIE`
- **거시 시장 프록시** (FRED 폴백, yfinance): `^TNX ^IRX ^FVX HYG LQD IEF CPER GLD XLI SPY ^MOVE`
- 룩백 `LOOKBACK_DAYS = 420` (200DMA·52주 고점·6M 모멘텀용)

### 1.2 2축 + 오버레이 (소스: `classifier.py`, `macro.py`, `rates.py`, `technical.py`)
- **X축 = 거시 침체 Composite (0~100)**: 5팩터 가중합 (`config.RECESSION_WEIGHTS`)
  - A 수익률곡선 0.30 · B Sahm 0.25 · C ISM프록시 0.15 · D LEI프록시 0.15 · E 신용 0.15
  - 4-Phase 경계: `<25 확장 · <50 후기 · <70 침체경고 · ≥70 침체` (`config.MACRO_PHASES`)
- **Y축 = 가격 스트레스 (0~100)**: `0.6·decline_score + 0.4·min(100, -tape_dd/20%·100)` (`classifier._measure`)
- **오버레이1 과매도 score**: RSI(14)<32 + Bollinger %B<0.05 + ATR stretch 2.5 + 연속 음봉
- **오버레이2 Rate Stress (0~100, v1.1)**: R1 10Y속도 0.35 · R2 2Y/5Y경로 0.25 · R3 기대인플레 0.20 · R4 채권변동성 0.20 (`config.RATE_WEIGHTS`)

### 1.3 5상태 판정 (우선순위, `classifier.raw_classify`)
임계값은 히스테리시스 밴드 적용(진입 엄격/이탈 느슨). 기본 진입값:
```
1. RECESSION_REBALANCE  : Macro ≥ 55 AND (지수DD ≤ -5% OR trend_broken)
2. DOWNTREND_DISTRIBUTION: trend_broken AND 지수DD ≤ -12%   (Macro < 55)
3. OVERSOLD_BOUNCE       : (과매도score ≥ 55 OR 지수RSI < 30) AND DD ≤ -5%  또는 과매도+추세유지
4. CORRECTION            : DD ≤ -5% 이고 과매도 아님
5. UPTREND_HEALTHY       : 그 외
```
- `trend_broken = 지수 200일선 이탈 OR 데드크로스 OR breadth<40%`
- **히스테리시스** (`config.HYSTERESIS`): `confirm_days=2` — 새 raw 레짐이 2거래일 연속이어야 공식 전환.
  밴드: RSI 진입30/이탈38, DD조정 진입5/이탈3.5, DD깊은 진입12/이탈10, Macro침체 진입55/이탈50.
  → **상태 저장 필요**(`data/regime_state.json`). TS 포팅 시 D1 또는 R2에 `committed/since/candidate/count` 영속화.

### 1.4 하락유형 라벨 (`rates.decline_type`, 가격스트레스 ≥ 28일 때만)
- **RECESSION_DRIVEN** (Macro≥55): TLT/IEF 헤지 유효
- **RATE_DRIVEN** (RateStress≥55 & Macro<55): ⚠️ TLT 동반하락 위험 → BIL/SHV/GLD
- **VALUATION_DRIVEN** (둘 다 <55): 멀티플 압축 → 현금/인버스(SH/PSQ)

### 1.5 native 출력 (`classifier.build_verdict` → `dashboard/data/latest.json`)
```jsonc
{ "state": "CORRECTION", "state_kr": "조정",
  "action": "HOLD_ACCUMULATE",          // RISK_ON|HOLD_ACCUMULATE|BUY_DIP_TACTICAL|REDUCE|DEFENSIVE_ARDS
  "confidence": 20~95, "headline": "...", "handoff": "...",
  "decline_type": {...}, "hysteresis": {...},
  "axes": { "macro", "price_stress", "rate_stress", "decline_score", "oversold_score" },
  "evidence": { "tape_drawdown", "breadth_above_200dma", "index_min_rsi14", "trend_broken", ... } }
```

### 1.6 → 대시보드 매핑 (제안, ⚠️검토 필요)
ARDS는 종목 시그널이 아니라 국면이므로, **대표 티커 `QQQ`**(또는 `^NDX`) 1행으로 기록하고
카드의 "방어모드 on/off"는 `action == DEFENSIVE_ARDS`로 표시.

| ARDS state / action | dashboard `signal` | 근거 |
|---|---|---|
| UPTREND_HEALTHY / RISK_ON | `BUY` | 리스크온 |
| CORRECTION / HOLD_ACCUMULATE | `HOLD` | 보유+분할매수 (BUY로 볼지 검토) |
| OVERSOLD_BOUNCE / BUY_DIP_TACTICAL | `BUY` | 전술적 분할매수 |
| DOWNTREND_DISTRIBUTION / REDUCE | `SELL` | 신규매수 보류·축소 |
| RECESSION_REBALANCE / DEFENSIVE_ARDS | `SELL` (+ 방어모드 ON) | 자본보존 |
| `trend_broken==true` 인 비-침체 국면 | `SHORT_TERM_RISK` 병기 | 카드 상단 앰버 스트립 트리거 |

> **검토 포인트**: ① CORRECTION을 HOLD vs BUY 중 무엇으로 볼지. ② SHORT_TERM_RISK를 별도 행으로
> 둘지, 카드 플래그로만 쓸지. ③ ARDS score 필드엔 `confidence` 또는 `axes.macro`를 넣을지.

---

## 2. AMQS — 적응형 모멘텀 (AI 인프라)

**성격**: 유니버스를 100점으로 스코어링 → Top-N 선정 + 국면필터. **종목별 시그널 산출**.

### 2.1 입력 데이터 (소스: `script/strategy.py`)
- **유니버스 ~19종** (6 서브테마): GPU(NVDA AMD INTC AVGO MRVL TSM) · Memory(MU STX WDC PSTG) · Server(DELL SMCI HPE) · Network(ANET CSCO) · Data(SNOW ORCL PLTR) · Power(VRT)
- **국면 입력**: `QQQ`, `^VIX` (yfinance)
- 일봉 adjusted close. 룩백 252+일.

### 2.2 100점 스코어 (5차원, `strategy.py` L455-460)
`total = 0.35·momentum + 0.15·pullback + 0.25·quality + 0.15·vol_alpha + 0.10·macro`
- **momentum (35%)**: 4팩터 z합 `0.50·Z(12-1)+0.30·Z(6-1)+0.15·Z(3-1)+0.05·Z(1/vol60)` (60%) + 52주고점거리(25%) + 추세일관성(15%). 모멘텀 정의: `P(t-21)/P(t-252)-1` 등(직전 1M 제외)
- **pullback (15%)**: 4-게이트(12-1>0, 6-1>0, 가격>50MA, 5D≤-3% OR 20D≤-5%) 통과 시 `(0.7·|5D|+0.3·|20D|)·(1+min(FA,1))` + RSI 과매도 보너스
- **quality (25%)**: `0.6·(가격>200MA) + 0.4·모멘텀 가속`
- **vol_alpha (15%)**: `0.70·6M Sharpe% + 0.30·12M MDD 페널티`
- **macro (10%)**: QQQ 200MA·VIX·금리 적합도

### 2.3 종목 시그널 티어 (`strategy.py` L466-491)
```
EXCLUDED        : 사전필터 탈락
EXIT            : 12M MDD < -30% (추세 붕괴)
DIP_BUY         : score_pullback > 60 AND score_momentum > 50   ← 우선
CENTER          : total ≥ 80
SATELLITE       : total ≥ 65
TACTICAL        : total ≥ 50
REDUCE          : total < 50
```
손절: 진입가 대비 -12% (백테스트 룰). 리밸런스 월요일 시가(금요일 종가 신호).

### 2.4 국면 필터 (`strategy.py` L582-601)
```
RISK_ON   : QQQ > 200MA AND VIX < 25 AND 5D > -5%   → 100% 주식, Top-10 동일가중
RISK_OFF  : QQQ < 200MA(1주+) OR VIX > 30           → 50% 현금
DEFENSIVE : QQQ 5D < -8%                            → 방어바스켓(BRK-B WMT COST JNJ KO PG PEP)
```

### 2.5 → 대시보드 매핑 (제안, ⚠️검토 필요)
종목별로 행 기록(카드엔 Top-6 + 더보기). 국면(RISK_ON/OFF/DEFENSIVE)은 카드 헤더 지표로.

| AMQS 티어 | dashboard `signal` | score 필드 |
|---|---|---|
| DIP_BUY | `BUY` | total_score_100 |
| CENTER (≥80) | `BUY` | total_score_100 |
| SATELLITE (≥65) | `HOLD` | total_score_100 |
| TACTICAL (≥50) | `HOLD` | total_score_100 |
| REDUCE (<50) | `SELL` | total_score_100 |
| EXIT | `SELL` | total_score_100 |
| EXCLUDED | (미표시) | — |
| 국면 DEFENSIVE/RISK_OFF | 카드에 `SHORT_TERM_RISK` 플래그 | — |

> **검토 포인트**: SATELLITE를 HOLD vs BUY 중 무엇으로? CENTER/DIP_BUY를 둘 다 BUY로 합치면
> 강도 구분이 사라짐 → `detail_json`에 원 티어 보존 권장.

---

## 3. MU_Hynix — 리드래그 + 페어 평균회귀  ⏸ **1차 제외 (Phase 2)**

> **1차 출시에서 제외**. 아래는 Phase 2 포팅을 위한 분석 보존용. 1차 빌드(엔진/카드/시그널 잡)에는
> ARDS·AMQS만 포함하고 MU_Hynix 관련 코드는 작성하지 않는다.

**성격**: MU(마이크론)와 SK하이닉스(`000660.KS`) **2종목 페어 트레이드**. 시장 전체가 아닌 2개 티커 시그널.

### 3.1 입력 데이터 (소스: `script/mu_hynix_pairs.py`, `Signal_Bot/signal_bot.py`)
- `MU` (NASDAQ), `000660.KS` (SK하이닉스, KRX), `USDKRW=X` (환율) — 모두 yfinance
- 보조: 삼성전자 `005930.KS`, 한미반도체 등 (확장 페어, 참고용)
- statsmodels로 OLS 헤지비율 + ADF 코인티그레이션 검정

### 3.2 시그널 룰 (`signals.json` 확인)
- **Signal A — 리드래그 모멘텀**: MU(t)가 하이닉스(t+1) 선행(+1일 상관 0.4655, p<0.001).
  - 임계: MU 전일수익률 > +1σ(동적, ≈+3.7%) → 하이닉스 **익일 BUY** / < -1σ → SELL/회피
- **Signal B — 스프레드 평균회귀**: `log(HYNIX_usd) = α + β·log(MU)`, β≈1.096, ADF p=0.0266(유효, EG 경계)
  - `z > +2` → Short spread(하이닉스 SELL + MU BUY) · `z < -2` → Long spread(하이닉스 BUY + MU SELL)
  - 청산 `|z|<0.5` · 진입금지/손절 `|z|>3`
- **리스크 게이트**: MU 실적 ±3거래일 진입금지 · USD/KRW 일변동 ±1.5% 초과 시 신뢰도↓ · |z|>3 강제청산
- **레짐(전략6)**: 둘 다 60MA 위 → 모멘텀(A) 가중↑ / 엇갈림 → 평균회귀(B)↑ / 둘 다 아래 → 방어

### 3.3 native 출력 (`signals.json`)
```jsonc
{ "core": { "signal_A": {"action":"BUY","confidence":"med",...},
            "signal_B": {"action":"BUY-SPREAD",...}, "z_last": -2.11, ... },
  "recommendation": { "headline":"...", "bias":"LONG", "warnings":[] } }
```

### 3.4 → 대시보드 매핑 (제안, ⚠️검토 필요)
페어이므로 **티커 2행**(`MU`, `000660`)으로 기록. signal_A(방향) 기준 + signal_B 스프레드 보조.

| 조건 | `000660` (하이닉스) | `MU` |
|---|---|---|
| Signal A BUY (MU>+1σ) | `BUY` | `HOLD` |
| Signal A SELL (MU<-1σ) | `SELL` | `HOLD` |
| Signal B `z<-2` (Long spread) | `BUY` | `SELL` |
| Signal B `z>+2` (Short spread) | `SELL` | `BUY` |
| `\|z\|>3` 또는 실적 ±3일 | `SHORT_TERM_RISK` | `SHORT_TERM_RISK` |

> **검토 포인트**: A와 B가 충돌할 때 우선순위(레짐 가중으로 결정?). `bias`(LONG/SHORT/NEUTRAL)를
> 카드 헤더로 쓰고, score엔 `z_last` 또는 confidence를 넣을지.

---

## 4. `SURGE` 시그널의 출처
세 전략 어디에도 SURGE(급등) native 출력은 없음. SURGE는 **[D] 급등 TOP 10**(movers, 10분 크론)에서
당일 급등 종목에 부여하는 것이 자연스러움. 전략 카드에는 원칙적으로 미사용. (가이드 §B-1.2의 SURGE 배지는
movers/검색 결과 패널용으로 한정 권장.) — ⚠️ 확정 필요.

---

## 5. 포팅 리스크 & 미해결 (step 6 진입 전 점검)

1. **FRED CSV fetch in Workers** — ARDS 거시축. Worker `fetch`로 CSV 수집 가능하나 7개 시리즈 = I/O 다수.
   일 1회 크론이라 무방하나 실패 시 yfinance 프록시 폴백 로직까지 포팅 필요.
2. **yfinance 대체 → Yahoo chart API 채택(2026-06-06 확정)**. Workers엔 yfinance 없음.
   가이드는 Stooq CSV를 상정했으나 **Stooq는 현재 JavaScript proof-of-work 봇 차단**으로 Worker fetch 불가.
   → **Yahoo chart API**(`query1.finance.yahoo.com/v8/finance/chart/<sym>`, 키 불필요) 사용. 엔진이 쓰는
   `^GSPC ^NDX ^TNX ^IRX ^FVX ^VIX ^MOVE` + 종목/ETF 심볼을 **그대로** 지원, adjclose 제공.
   구현: `cron-worker/src/providers/yahoo.ts`. FRED는 best-effort(막히면 ARDS가 시장 프록시로 자동 폴백).
3. **ARDS 히스테리시스 상태 영속화** — `regime_state.json` → D1/R2. 크론 재실행 간 `committed/since/count` 유지.
4. **Python 결과 대조 fixture** — 각 전략을 특정 날짜로 고정 실행한 native JSON을 `tests/fixtures/`에 보관,
   TS 포팅 결과와 수치 대조(가이드 §6.3 step 6 + 운영 체크리스트의 1주 병행 검증).
5. **모멘텀 룩백 거래일 정의** — AMQS 252/126/63/21 거래일. Stooq/yfinance 데이터의 결측·정렬로 인덱싱이
   어긋나면 z-score가 흔들림. 영업일 정렬·forward-fill 규칙을 Python과 동일하게.

### Phase 2(MU_Hynix) 보류 사유 — 재개 시 점검
- **statsmodels(ADF/OLS) TS 대체**: OLS β는 단순 회귀로 가능하나 ADF p-value는 TS 라이브러리 부재.
  대안: ADF를 일 1회 별도 파이썬 잡으로 사전계산해 주입하고 Worker는 z-score만 계산. 또는 β 고정값.
- **SK하이닉스(000660) KRX 소스**: yfinance `000660.KS`는 지연·휴장·FX 처리 미흡. Stooq `000660.KR` 형식·
  USD/KRW 환산 검증 필요. (이 미해결이 1차 제외의 주된 사유.)

---

## 6. 요약 — 전략별 한 줄 (1차 = ARDS·AMQS)
- **ARDS** ✅ 포팅완료(`shared/strategy/ards/`, Python 골든 일치): 시장 국면 1개 판정 → QQQ 대표행 + 방어모드 플래그. 거시(FRED)+가격+금리 2축.
- **AMQS** ✅ 포팅완료(`shared/strategy/amqs.ts`, Python 골든 일치): AI인프라 ~19종 100점 스코어 → Top-N 종목 시그널 + 국면필터.
- **MU_Hynix** ⏸: MU↔하이닉스 페어(리드래그+코인티그레이션). **1차 제외** — KRX 소스/statsmodels 난점으로 Phase 2.
