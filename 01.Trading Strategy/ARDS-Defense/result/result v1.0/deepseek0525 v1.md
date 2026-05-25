**# ARDS-Defense: Adaptive Recession-Defensive Strategy for Defense & AI-Weaponization**

**분석 기준일: 2026년 5월 25일 (최대한 최신 데이터 기준)**

---

## STEP 0 — Macro Regime Detection (5-Factor Recession Composite)

| Factor | Weight | Indicator | 현재 값 | 기준일 | 출처 | Recession Probability |
|:-------|:------:|:----------|:--------|:------:|:-----|:----------------------:|
| A. Yield Curve | 30% | 10Y-2Y Spread | **+0.49% (49bp)** | 2026-05-21 | Indexergo | **50%** |
| B. Sahm Rule | 25% | Unemployment 3M MA − 12M low | **0.47pp** | 2026-04 | FRED (SAHMREALTIME) | **0%** |
| C. ISM Manufacturing | 15% | ISM Manufacturing PMI | **52.7** | 2026-04 | ISM / Trading Economics | **0%** |
| D. LEI | 15% | Conference Board LEI 6M change rate | **-0.7%** | 2026-04 | Conference Board | **0%** |
| E. Credit Stress | 15% | HY OAS + NFCI | OAS 2.78% / NFCI -0.52 | 2026-05-21 / 2026-05 | FRED / YCharts / Gurufocus | **0%** |

### 세부 산출 내역

- **A. Yield Curve (30%)** — 10Y-2Y 금리차 +49bp로 0–50bp 구간에 해당 → **확률 50%** → 기여도 **15.0%**
- **B. Sahm Rule (25%)** — 실업률 4.0%, 12개월 저점 3.53% 기준 차이 0.47%p로 0.50%p 미만 → **확률 0%** → 기여도 **0.0%**
- **C. ISM Manufacturing (15%)** — 52.7로 45 이상 → **확률 0%** → 기여도 **0.0%**
- **D. LEI (15%)** — 6개월 변화율 -0.7%로 -2% 이상 → **확률 0%** → 기여도 **0.0%**
- **E. Credit Stress (15%)** — HY OAS 2.78%로 500bp 미만, NFCI -0.52로 0 미만 → **확률 0%** → 기여도 **0.0%**

**재무 건전성 평가:** 하이일드 OAS(2.78%)는 500bp 기준선을 크게 하회하고, NFCI(-0.52)는 완화적 유동성 환경을 나타내며 신용 스트레스는 최소 수준입니다. LEI 6개월 변화율(-0.7%)은 전기(-1.0%) 대비 낙폭이 축소되었으며, Conference Board는 2026년 GDP 성장률을 1.7%로 전망하고 있습니다.

**Composite 계산:**

| 요인 | 확률 × 가중치 | 기여도 |
|:-----|:------------:|:------:|
| A | 50% × 30% | 15.0% |
| B | 0% × 25% | 0.0% |
| C | 0% × 15% | 0.0% |
| D | 0% × 15% | 0.0% |
| E | 0% × 15% | 0.0% |

| Recession Composite | 15.0% |
|:--------------------|:-----:|

**Phase Determination:**

| Composite | Phase |
|:----------|:------|
| < 25% | **Phase 1 — Expansion** |
| 25–50% | Phase 2 — Late-Cycle |
| 50–70% | Phase 3 — Recession-Warning |
| ≥ 70% | Phase 4 — Recession |

---

## STEP 1 — Defense-Specific Overlay

### Factor F. Geopolitical risk (30%)

2026년 5월 기준, GPR 지수는 4월 129.49로 2021년 98 대비 약 32% 상승한 높은 수준을 유지하고 있습니다. 주요 분쟁 현황:

- **러시아-우크라이나 전쟁:** 4년차 지속, 전선 교착 상태
- **미국-이란 전면전:** 전쟁 발발 3주차 (2026년 4월 말 개시 추정). 이란의 2차 보복 공격(5월 23일)으로 긴장 지속
- **남중국해:** 미·필리핀 대중국 갈등 심화
- **한반도:** 북한 미사일 도발 지속, 확장 억제 논의 진행 중

→ **평가: 90/100** (극도로 높은 지정학적 위험)

### Factor G. Defense budget momentum (25%)

- 미국 2027 회계연도(2026년 10월–2027년 9월) 국방예산 요청안: **1.5조 달러** (전년 대비 **44% 증가**)
- NATO GDP 2% 방위비 목표 달성국 증가, 2025년 헤이그 정상회담에서 5% 목표 논의

→ **평가: 95/100** (역대 최대 규모의 국방예산 증가)

### Factor H. AI-Defense contract momentum (25%)

- **Palantir (PLTR):** 2026년 1분기 매출 16.33억 달러 (전년 대비 **85% 성장**), EPS 0.33달러로 예상치(0.28달러) 상회. 미국 매출 전년 대비 **104% 증가**
- **Anduril:** 2026년 5월 시리즈 H에서 50억 달러 조달, 기업가치 610억 달러로 1년 만에 2배 성장. 2025년 매출 22억 달러 기록
- **KTOS:** 무인기·드론 swarm 관련 다수 계약 체결 지속
- Kratos 2026년 1분기 KGS 부문 매출 2.884억 달러 (전년 2.395억 대비 증가)

→ **평가: 85/100** (AI-방산 섹터의 강력한 성장 모멘텀)

### Factor I. K-Defense export momentum (20%)

- 2025년 한국 방산 수출 수주: **154.4억 달러** (전년 대비 **+62.5%** )
- 2026년 전망: 폴란드 2차 이행계약(약 120억 달러), UAE, 호주, 페루 등 수출처 다변화로 **사상 최대 전망**
- K9 자주포, 천궁-II, K2 전차 등 주요 플랫폼 수출 확대

→ **평가: 90/100**

### Defense Sentiment Score 계산

| 요인 | 평가 점수 | 가중치 | 기여도 |
|:-----|:---------:|:------:|:------:|
| F. Geopolitical risk | 90 | 30% | 27.0% |
| G. Defense budget momentum | 95 | 25% | 23.75% |
| H. AI-Defense contract momentum | 85 | 25% | 21.25% |
| I. K-Defense export momentum | 90 | 20% | 18.0% |

**Defense Sentiment Score = 90.0 / 100**

### Phase Adjustment

| 구분 | 값 |
|:-----|:---:|
| Pre-adjustment Phase | Phase 1 |
| Defense Sentiment Score | 90.0 (≥ 60) → 강한 방산 독립 성장 |
| Adjustment applied | −1 (Floor to Phase 1) |
| **Post-adjustment Phase** | **Phase 1** |

---

## STEP 2 — Universe (Defense & AI-Weaponization 3-Tier)

*실시간 가격 정보는 2026년 5월 25일 기준*

### Tier 1 — Core Defense (Phase 1 Allocation: 50% of portfolio)

| 국가 | 종목명 | 티커 | 비고 |
|:----:|:-------|:-----|:-----|
| 🇰🇷 | 한화에어로스페이스 | 012450 | 글로벌 K-방산 대표, 수출 모멘텀 강력 |
| 🇰🇷 | LIG Nex1 | 079550 | 유도무기·C4I, 수출 확대 중 |
| 🇰🇷 | KAI (한국항공우주) | 047810 | 항공기·위성, 폴란드 FA-50 수출 |
| 🇰🇷 | 현대로템 | 064350 | K2전차·K9자주포, 유럽 수출 확대 |
| 🇰🇷 | 한화오션 | 042660 | 해군함정·잠수함 |
| 🇰🇷 | **한화시스템** | 272210 | **방산전자·AI·C4I (Tier 1+2 중복)** |
| 🇺🇸 | Lockheed Martin | LMT | F-35, 전략무기 핵심 |
| 🇺🇸 | RTX | RTX | 미사일·레이더·엔진 |
| 🇺🇸 | Northrop Grumman | NOC | B-21, 항공모함, 자율무기 |
| 🇺🇸 | General Dynamics | GD | 잠수함·전투차량·C4I |
| 🇺🇸 | L3Harris | LHX | 통신·전자전·우주 |
| 🇺🇸 | Boeing | BA | 방산·우주·드론 (상업용 항공 리스크 병존) |
| 🇰🇷 ETF | PLUS K-Defense | 449450 | 국내 방산 9종 구성 |
| 🇺🇸 ETF | TIGER US Defense TOP10 | 494840 | 미국 방산 대형주 10종 |

### Tier 2 — AI-Defense (Phase 1 Allocation: 30% of portfolio)

| 국가 | 종목명 | 티커 | 비고 |
|:----:|:-------|:-----|:-----|
| 🇺🇸 | Palantir | PLTR | AI 데이터 플랫폼, 1Q26 매출 85% 성장 |
| 🇺🇸 | Kratos | KTOS | 무인기·드론 swarm, 다수 계약 체결 중 |
| 🇺🇸 | AeroVironment | AVAV | 무인항공기·순항탄 |
| 🇺🇸 | BigBear.ai | BBAI | AI 의사결정 지원 (점수 미달 가능성 높음) |
| 🇰🇷 | **한화시스템** | 272210 | 방산전자·AI 플랫폼 부문만 Tier 2로 분류 |
| — | Anduril | (미상장) | 시리즈 H 완료, Pre-IPO. 락업 만료 시 편입 고려 |

### Tier 3 — Tactical (Phase 1 Allocation: 0% of portfolio)

*Phase 1 (Expansion)에서는 Tier 3 할당이 0%입니다. Tier 3은 Phase 3 이상에서만 활성화됩니다.*

---

## STEP 3 — 5-Dimension Scoring

### 평가 기준

| Dimension | Weight | 평가 기준 |
|:----------|:------:|:----------|
| D1. Defense revenue purity | 25% | 방산 매출 비중 (>70% = 만점, <30% = 0) |
| D2. AI/unmanned exposure | 25% | AI·자율무기·무인체계 관련 매출/계약 비중 |
| D3. Financial resilience | 20% | FCF/매출, 부채비율, 이자보상배율 |
| D4. Valuation discipline | 15% | Forward P/E vs 5년 평균 (할인 시 가산) |
| D5. Export/overseas momentum | 15% | 해외 매출 비중 + 최근 12개월 해외 수주 성장률 |

### 5-Dimension Scoring Summary (Top 10 names)

| Rank | 종목명 | 티어 | D1(25%) | D2(25%) | D3(20%) | D4(15%) | D5(15%) | **종합 점수** |
|:----:|:-------|:----:|:-------:|:-------:|:-------:|:-------:|:-------:|:-------------:|
| 1 | **LIG Nex1** | T1 | 100 | 75 | 85 | 80 | 85 | **84.0** |
| 1 | **Hanwha Aerospace** | T1 | 100 | 75 | 80 | 75 | 95 | **84.0** |
| 3 | **Lockheed Martin** | T1 | 95 | 70 | 95 | 85 | 70 | **83.0** |
| 4 | **RTX** | T1 | 90 | 65 | 90 | 85 | 65 | **80.0** |
| 5 | **Northrop Grumman** | T1 | 95 | 65 | 90 | 80 | 60 | **79.8** |
| 6 | **KAI (Korea Aerospace)** | T1 | 95 | 60 | 75 | 70 | 85 | **78.5** |
| 7 | **General Dynamics** | T1 | 90 | 55 | 95 | 85 | 65 | **78.0** |
| 8 | **한화시스템** | T1/T2 | 85 | 80 | 75 | 70 | 80 | **77.0** |
| 9 | **Palantir (PLTR)** | T2 | 70 | 100 | 85 | 50 (조정) | 75 | **76.8** |
| 10 | **현대로템** | T1 | 90 | 55 | 70 | 75 | 85 | **75.0** |

**Palantir Valuation Adjustment (Special Rule #1):** PLTR의 Forward P/E는 현재 약 100배 이상으로 추정되어 현저한 고평가 상태입니다. 이에 따라 D4 점수를 기준치 대비 **50 → 50으로 조정**하였으며, Special Rule #1 적용 시 Tier 2 내 배분이 50% 감축됩니다.

---

## STEP 3.5 — Intra-Tier Weighting (Score-linked)

### Tier 1 (Core Defense) — 총 50% 배분 기준

| 종목명 | 종합 점수 | Tier 1 내 점수 비율 | Tier 1 내 배분 (%) | 최종 포트폴리오 비중 (%) |
|:-------|:---------:|:------------------:|:------------------:|:-----------------------:|
| LIG Nex1 | 84.0 | 15.7% | 7.85% | 3.93% |
| Hanwha Aerospace | 84.0 | 15.7% | 7.85% | 3.93% |
| Lockheed Martin | 83.0 | 15.5% | 7.75% | 3.88% |
| RTX | 80.0 | 15.0% | 7.50% | 3.75% |
| Northrop Grumman | 79.8 | 14.9% | 7.45% | 3.73% |
| KAI | 78.5 | 14.7% | 7.35% | 3.68% |
| General Dynamics | 78.0 | 14.6% | 7.30% | 3.65% |
| **합계** | **535.3** | **100.0%** | **50.00%** | **50.00%** |

※ 한화시스템은 STEP 2에 따라 **Tier 2로 재분류**하여 Tier 1 계산에서 제외하였습니다.

### Tier 2 (AI-Defense) — 총 30% 배분 기준

| 종목명 | 종합 점수 | Tier 2 내 점수 비율 | 특별 규칙 적용 후 (%) | 최종 포트폴리오 비중 (%) |
|:-------|:---------:|:------------------:|:---------------------:|:-----------------------:|
| 한화시스템 (AI) | 77.0 | 31.8% | 9.5% | 2.85% |
| Palantir (PLTR) | 76.8 | 31.7% | **4.8% (50% 감축)** | 1.44% |
| Kratos (KTOS) | 65.0 (추정) | 26.9% | 8.1% | 2.43% |
| AeroVironment (AVAV) | 60.0 (추정) | 24.8% | 7.4% | 2.22% |
| BigBear.ai (BBAI) | **<60 (부적격)** | — | **제외 (0%)** | 0.00% |
| **합계** | **242.6** | **100.0%** | **29.8%** | **8.94%** |

※ BBAI는 종합 점수 60 미달로 제외. PLTR(50% 감축)로 인한 감축분(1.44%)은 Tier 1에 재배분합니다. Tier 2 미배분 잔여분(0.2%)도 Tier 1에 재배분합니다.

### Tier 2 → Tier 1 재배분

| 항목 | 비중 (%) |
|:-----|:--------:|
| Tier 1 본배분 | 50.00% |
| PLTR 감축분 재배분 | +1.44% |
| Tier 2 미배분 재배분 | +0.20% |
| **최종 Tier 1 비중** | **51.64%** |
| Tier 2 최종 비중 | 8.94% |
| Cash | 39.42% |

※ Tier 2 특별 규칙 #4는 Tier 2 총 비중 0% 시에만 적용되므로, 현재 미적용.

---

## STEP 4 — Per-Phase Asset Allocation Matrix

**최종 Phase: 1 (Expansion)**

| Phase | Tier 1 | Tier 2 | Tier 3 | Cash |
|:------|-------:|-------:|-------:|-----:|
| 1. Expansion | **50%** | **30%** | 0% | 20% |
| 2. Late-Cycle | 55% | 20% | 5% | 20% |
| 3. Recession-Warning | 60% | 10% | 10% | 20% |
| 4. Recession | 70% | 0% | 15% | 15% |

### 본 포트폴리오 최종 배분 (STEP 3.5 조정 반영)

| 구성 요소 | 매트릭스 기준 (%) | 최종 적용 (%) |
|:----------|:----------------:|:-------------:|
| Tier 1 (Core) | 50% | **51.64%** |
| Tier 2 (AI-Defense) | 30% | **8.94%** |
| Tier 3 (Tactical) | 0% | **0%** |
| Cash | 20% | **39.42%** |

### 국가별 분할 (STEP 6, Rule 4)

Base split: **Korea 40% / US 60%**

Defense Sentiment Score = 90.0 (≥ 70) → **Korea +10pp**

| 국가 | 최종 포트폴리오 내 비중 |
|:----:|:----------------------:|
| 🇰🇷 한국 | **50%** |
| 🇺🇸 미국 | **50%** |

※ 국가별 30% 미방지 규칙 충족.

---

## STEP 5 — AI-Defense Special Rules (종합 적용)

| 규칙 | 내용 | 적용 결과 |
|:----:|:-----|:----------|
| **#1** | PLTR Forward P/E > 50x 또는 EV/Sales > 20x → Tier 2 내 비중 50% 감축 | PLTR Forward P/E 100배 이상 → **Tier 2 배분 50% 감축** |
| **#2** | Anduril IPO 후 90일 락업 만료 전까지 최대 5% cap, 그 이후 정규 편입 | Anduril 2026년 5월 시리즈 H 완료, Pre-IPO 단계 유지 → **편입 보류** |
| **#3** | KTOS, AVAV, BBAI 시총 < 30억 달러 시 Tier 2 내 병합 cap 30% | KTOS(∼105억)·AVAV(∼45억) 조건 미충족, BBAI(∼20억)는 조건 충족하나 점수 부족으로 **미포함** |
| **#4** | Tier 2 총 비중 0% 시 → 해당 비중 Tier 1으로 이동 | Tier 2 총 비중 8.94% → 규칙 미적용 |

---

## STEP 6 — Execution Rules

### 1. Scale-in Schedule
> "20% of total allocation per week over 5 weeks"

| 주차 | 누적 배분 (%) | 신규 투입 (%) |
|:----:|:-------------:|:-------------:|
| Week 1 | 20% | 20% |
| Week 2 | 40% | 20% |
| Week 3 | 60% | 20% |
| Week 4 | 80% | 20% |
| Week 5 | 100% | 20% |

※ 각 주차별 목표 배분 비중은 최종 포트폴리오 기준으로 유지하며, 시장 여건에 따라 유연하게 조정 가능합니다.

### 2. Tier 3 Rebalancing
Phase 1에서는 Tier 3 = 0% → 해당 규칙 적용 대상 아님

### 3. VIX Halt 조건

**Current VIX (2026-05-22 마감): ~16-17**

| 조건 | 판정 | 조치 |
|:-----|:----:|:-----|
| VIX ≤ 35 | ✅ **정상 영역** | 모든 포지션 유지, 신규 매수 지속 |

※ VIX 35 초과 시 절반 포지션 축소 및 현금 전환 지침은 현재 적용되지 않음

### 4. Country Diversification

| 국가 | 포트폴리오 비중 | 최소 요건 | 충족 여부 |
|:----:|:--------------:|:---------:|:----------:|
| 🇰🇷 | **50%** | 30% | ✅ 충족 |
| 🇺🇸 | **50%** | 30% | ✅ 충족 |

※ Defense Sentiment 90.0으로 +10pp K-방산 프리미엄 적용

### 5. ETF-only Construction (옵션)

본 포트폴리오는 개별 종목 중심으로 구성되어 있습니다. ETF 구축 옵션은 상황에 따라 병행 가능하며, Tier 1: 70% (ETF 중심), Tier 2: 20%, Cash: 10%로 단순화할 수 있습니다.

---

## STEP 7 — Counter-Scenario (Why This Time Could Be Different)

본 ARDS-Defense 전략이 실패할 수 있는 구체적 조건:

### 1. 급격한 방산 예산 삭감
- **현재 가정:** 미국 국방예산 44% 증액, NATO 5% 목표
- **실패 조건:** 이란 전쟁 조기 종결 또는 미·러 간 대타협으로 군축 국면 돌입 시 방산 섹터 전반 매출 성장률 둔화
- **파급 효과:** 특히 고평가된 AI-방산 종목(PLTR, KTOS 등)이 가장 큰 폭으로 재평가될 가능성 높음

### 2. AI 규제 강화로 인한 자율무기 개발 제한
- **현재 가정:** AI 무기체계가 방산 혁신의 핵심 동력
- **실패 조건:** 유엔(UN) 또는 주요국 간 자율살상무기(LAWS) 규제 협상 급진전 시 PLTR, Anduril, KTOS의 AI-방산 매출 성장 궤도 이탈
- **파급 효과:** 국제 여론이 AI 무기화에 대한 강력한 규제로 기울 경우, Tier 2 성장 가정 붕괴

### 3. 원자재 가격 급등에 따른 방산 마진 압박
- **현재 가정:** 방산 기업들의 안정적 수익성 유지
- **실패 조건:** 니켈·구리·희토류 등 방산 원자재 가격 급등 (2022년 수준 재현)
- **파급 효과:** 고정가 계약 비중이 높은 대형 방산업체(LMT, NOC, GD)의 수익성 직접적 타격, 자금 조달 여력이 취약한 AI-방산 기업의 성장 동력 둔화

### 4. K-방산 수출 의존도 및 환율 리스크
- **현재 가정:** K-방산 수출 성장 지속 (2025년 154억 달러, 2026년 전망 증가)
- **실패 조건:** 원·달러 환율 급락 시 한국 방산업체 수익성 악화, 폴란드·UAE 등 주요 수출처 재정 악화로 계약 축소 또는 지연
- **파급 효과:** 높은 수출 의존도가 리스크로 전환, 방산 업종 내 한국 비중 축소 필요

### 5. 사이클 전환 조기 진입
- **현재 가정:** Phase 1 (Expansion) 지속
- **실패 조건:** LEI 추가 하락, 신용 스트레스 확대, 또는 ISM PMI 45 이하 급락으로 Phase 2(Late-Cycle) 조기 전환
- **파급 효과:** 현재 Tier 1 중심 전략은 여전히 유효하나, Tier 2(AI-Defense) 비중 유지 필요성 재평가 필요

---

## 📋 Disclaimer

> **This output is an LLM-based simulation result and is not investment advice. All investment decisions and responsibility rest with the investor.**
>
> 본 보고서는 ARDS-Defense v1.2 프롬프트에 따라 생성된 LLM 기반 시뮬레이션 결과입니다. 제시된 데이터, 분석 및 배분 비중은 2026년 5월 25일 기준 수집 가능한 공개 정보에 근거하며, 시장 상황, 기업 펀더멘털 및 거시 경제 지표는 수시로 변동됩니다. 모든 실제 투자 결정은 투자자 본인의 판단과 책임 하에 이루어져야 하며, 과거 실적이나 분석 결과가 미래 성과를 보장하지 않습니다.

---

**분석 완료일: 2026년 5월 25일**

**프롬프트 버전: ARDS-Defense_EN_v1.2**

**모델: DeepSeek (2026년 5월 25일 실행)**
