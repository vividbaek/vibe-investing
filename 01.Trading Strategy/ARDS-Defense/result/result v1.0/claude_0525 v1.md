# ARDS-Defense 실행 리포트
### Adaptive Recession-Defensive Strategy — Korea + US Defense & AI-Weaponization Portfolio

**작성 기준일:** 2026-05-25 (Asia/Seoul)
**관점:** 글로벌 방산 매크로/퀀트 애널리스트
**데이터 원칙:** STEP 0·STEP 1 전 지표는 웹 검색 기반 최신 실측치. 각 지표에 값·기준일·출처 명시.

---

## 1. 5-Factor 경기침체 종합지수 (Recession Composite) + Phase 진단

각 지표를 0–100% 침체확률로 환산 후 가중합.

| Factor | 가중 | 지표 | 실측값 | 기준일 | 출처 | 침체확률 |
|--------|------|------|--------|--------|------|----------|
| A. 수익률곡선 | 30% | 10Y-2Y 스프레드 | **+48bp** (0.48%) | 2026-05-13 | FRED T10Y2Y | **50%** (0–50bp 구간) |
| B. Sahm Rule | 25% | 실업률 3M MA − 12M 저점 | **0.20pp** | 2026-03 | FRED SAHMCURRENT | **0%** (<0.50) |
| C. ISM 제조업 | 15% | ISM Manufacturing PMI | **52.7** | 2026-04 (5/1 발표) | ISM / PRNewswire | **0%** (>48, 4개월 연속 확장) |
| D. LEI | 15% | Conf. Board LEI 6M 변화율 | **−0.7%** (Oct'25–Apr'26) | 2026-04 (5/22 발표) | Conference Board | **50%** (음(−)이나 −2% 미달 → "fragile"로 부분 신호 처리) |
| E. 신용스트레스 | 15% | HY OAS + Chicago Fed NFCI | **OAS 276bp / NFCI −0.52** | 2026-05-14 / 05-15주 | FRED BAMLH0A0HYM2 / NFCI | **0%** (OAS<500, NFCI<0) |

**Composite = (0.50×0.30)+(0×0.25)+(0×0.15)+(0.50×0.15)+(0×0.15) = 22.5%**

> **Phase 진단: Phase 1 (Expansion)** — Composite 22.5% < 25%.
>
> 해석: 수익률곡선은 여전히 평탄(완만한 정상화 국면)하고 LEI는 약하지만, 노동시장(Sahm)·제조업(ISM)·신용(OAS/NFCI)이 모두 침체 신호 없음. 단, ISM 물가지수 84.6(2022년 4월 이후 최고), 미시간대 소비심리 44.8(MoM −10%)은 **인플레이션·스태그플레이션 위험**을 시사 — STEP 7 반대 시나리오에서 재론.

---

## 2. Defense Sentiment Score + Phase 조정

방산 특화 지표를 침체 Composite 위에 중첩.

| Factor | 가중 | 측정 근거 (실측) | 점수 |
|--------|------|------------------|------|
| F. 지정학 리스크 | 30% | 2026 이란전쟁(2/28 미·이스라엘 합동타격, 호르무즈 위기), 러·우 지속, 北 CFR Tier I 격상, 美中 경쟁 심화 | **95** |
| G. 국방예산 모멘텀 | 25% | NATO 헤이그 5% GDP(2035) 합의, 2025년 유럽·캐나다 국방비 +20%, 全 32개국 2% 초과 | **90** |
| H. AI-방산 수주 모멘텀 | 25% | PLTR Q1'26 매출 +85% YoY, 美 정부부문 +84%, FY 가이던스 +71% 상향 | **95** |
| I. K-방산 수출 모멘텀 | 20% | 2026E 수출 $37.7B 사상최대(전년 대비 ~3.7배), 한화에어로 수주잔고 39.7조원, 4사 합산 ~120조원 | **92** |

**Defense Sentiment = (95×0.30)+(90×0.25)+(95×0.25)+(92×0.20) = 93.2**

| 구분 | 결과 |
|------|------|
| 조정 전 Phase | **Phase 1 (Expansion)** |
| Defense Sentiment | **93.2 (≥60 → Phase level −1 적용, 단 floor=1)** |
| 조정 후 Phase | **Phase 1 (Expansion)** — 이미 최저 단계이므로 −1 적용 후에도 Phase 1 유지 |

> 방산 섹터는 매크로 침체 신호와 무관하게 **독립적으로 매우 강한 구조적 강세**. 그러나 Phase 1이 이미 배분 매트릭스의 최강 성장 국면이므로 추가 공격적 전환 여지는 매트릭스상 제한됨.

---

## 3. 최종 Phase + Tier별 배분

**최종 Phase: Phase 1 (Expansion)**

| Phase | Tier 1 (Core) | Tier 2 (AI) | Tier 3 (Tactical) | Cash |
|-------|---------------|-------------|-------------------|------|
| **1. Expansion (적용)** | **50%** | **30%** | **0%** (강제) | **20%** |

- Tier 3은 Phase 1에서 강제 0%.
- STEP 6.4 국가배분: 기본 한국 40% / 미국 60%. Defense Sentiment 93.2 ≥ 70 → **K-Defense +10pp → 한국 50% / 미국 50%.**
- 각 국가 최소 30% 요건 충족.

---

## 4. Tier별 추천 종목 (Score 상위 + ETF)

> STEP 3.5 규칙 적용: Tier 내 배분 = (종목 Score / Tier 포함종목 Score 합) × Tier 총배분, 단일종목 ≤ Tier의 40%, Score < 60 제외.

### Tier 1 — Core Defense (총 50%)
상위 추천(Score순): **Hanwha Aerospace(012450)**, **LIG Nex1(079550)**, **Lockheed Martin(LMT)**, **RTX(RTX)**, **Korea Aerospace(047810)**
- ETF: **PLUS K-Defense(449450)**, **TIGER US Defense TOP10(494840)**

### Tier 2 — AI-Defense (총 30%)
상위 추천(Score순): **Palantir(PLTR)**, **Kratos(KTOS)**, **AeroVironment(AVAV)**, **Hanwha Systems(272210, AI플랫폼 비중)**
- ⚠️ **STEP 5-1 발동**: PLTR fwd P/E ~46x·EV/Sales 高 → **Tier 2 내 PLTR 비중 50% 자동 감축**.
- ⚠️ **STEP 5-3**: KTOS·AVAV·BBAI 시총<$3B 조합 → Tier 2 내 합산 30% 캡.
- Anduril: 상장 전 → STEP 5-2에 따라 상장 후 락업 만료까지 보류(상장 즉시는 5% 캡 한도).
- BBAI: Score 60 미만 가능성 높아 제외 후보.

### Tier 3 — Tactical (0%)
- Phase 1이므로 **전 종목 강제 0%**. (Phase 3 이하 진입 시 최대 15% 활성화)

---

## 5. 5-Dimension Scoring 요약 (상위 10종목)

평가축: D1 방산순도(25%) · D2 AI/무인노출(25%) · D3 재무건전성(20%) · D4 밸류규율(15%) · D5 수출모멘텀(15%). 100점 만점.

| 순위 | 종목 | Tier | D1 | D2 | D3 | D4 | D5 | **종합** |
|------|------|------|----|----|----|----|----|----------|
| 1 | Palantir (PLTR) | 2 | 78 | 98 | 92 | 35 | 80 | **77.6** |
| 2 | Hanwha Aerospace (012450) | 1 | 85 | 70 | 78 | 72 | 95 | **80.0** |
| 3 | LIG Nex1 (079550) | 1 | 92 | 72 | 80 | 70 | 85 | **80.3** |
| 4 | Lockheed Martin (LMT) | 1 | 95 | 65 | 82 | 78 | 70 | **78.6** |
| 5 | Hanwha Systems (272210) | 1/2 | 80 | 85 | 75 | 60 | 78 | **76.3** |
| 6 | Kratos (KTOS) | 2 | 82 | 88 | 65 | 45 | 60 | **70.0** |
| 7 | RTX (RTX) | 1 | 88 | 60 | 80 | 75 | 72 | **74.9** |
| 8 | Korea Aerospace (047810) | 1 | 90 | 62 | 72 | 65 | 88 | **75.6** |
| 9 | AeroVironment (AVAV) | 2 | 80 | 90 | 62 | 48 | 65 | **70.0** |
| 10 | Northrop Grumman (NOC) | 1 | 92 | 66 | 80 | 74 | 60 | **75.0** |

> 주의: 위 점수는 공개 재무·수주 정황에 기반한 **애널리스트 판단 추정치**이며, D3·D4의 정밀 수치(FCF/매출, fwd P/E 5년평균 대비)는 종목별 최신 재무제표로 재검증 필요. PLTR은 D4(밸류규율)에서 극히 낮은 점수(35) — 고밸류 리스크가 점수에 반영됨.

---

## 6. 실행 계획 (Scale-in 일정)

전체 자본을 5주에 걸쳐 주당 20%씩 분할 진입 (STEP 6-1).

| 주차 | 누적 진입 | 우선 집행 대상 |
|------|-----------|----------------|
| W1 (20%) | 20% | Tier 1 Core 한국(한화에어로·LIG넥스원) + 美(LMT·RTX) 핵심 |
| W2 (20%) | 40% | Tier 1 ETF(449450·494840) + Tier 1 잔여 |
| W3 (20%) | 60% | Tier 2 진입 개시 — PLTR(감축분), Hanwha Systems |
| W4 (20%) | 80% | Tier 2 잔여(KTOS·AVAV, 30% 캡 내) |
| W5 (20%) | 100% | 비중 미세조정 + Cash 20% 확정 |

**상시 리스크 룰**
- **VIX > 35**: 신규매수 전면 중단, 기존 포지션 50%만 유지·잔여 현금화 (STEP 6-3).
- Tier 3: 본 Phase에서 미보유 → 30일 강제 리밸런싱 룰 비활성.
- 국가배분 한국 50% / 미국 50% 유지, 각국 최소 30% 준수.
- ETF-only 대안: Tier1 ETF 70% + Tier2 ETF 20% + Cash 10% (Tier3 ETF는 Phase 3 이하에서만).

---

## 7. 반대 시나리오 (Why This Time Could Be Different)

본 전략(방산·AI무기화 강세 전제)이 **실패할 수 있는 구체적 조건**:

1. **전쟁 종결發 예산 급감** — 러·우 또는 이란 전선의 급격한 휴전·종전 시, 유럽 재무장 모멘텀과 K-방산 수주 파이프라인의 핵심 가정이 흔들림. 특히 한화에어로 수주잔고(매출 3.5~4년치)는 "이미 가격에 반영"된 상태라, 신규 수주 둔화 시 멀티플 디레이팅 위험.

2. **스태그플레이션 / 원자재 마진 압박** — ISM 물가지수 84.6(2022년 이후 최고), 미시간대 소비심리 44.8(급락), 호르무즈發 유가 상승은 방산 제조업체 **원가·마진을 직접 압박**. 동시에 Fed가 인플레 대응으로 긴축 전환 시 PLTR 등 고밸류 AI 종목의 최대폭 드로다운 위험(STEP 4가 Phase 4에서 Tier 2를 0%로 강제하는 근거와 동일한 메커니즘).

3. **AI 자율무기 규제** — 국제 규범·수출통제 강화로 자율무기·MUM-T 개발이 지연되면 Tier 2(AI-방산)의 구조적 성장 서사 자체가 훼손. PLTR·Anduril·Kratos 밸류에이션의 핵심 전제(AI 계약 가속) 붕괴 가능.

4. **고밸류 집중 리스크** — PLTR fwd ~46x revenue는 S&P500 최고 수준. 실적이 강해도 이미 가격 반영. "멀티플로 성장을 따라잡는 데 18~24개월" 필요하다는 시장 평가 → 단기 변동성 확대 시 Tier 2 전체 견인.

---

## 8. Disclaimer

> **This output is an LLM-based simulation result and is not investment advice. All investment decisions and responsibility rest with the investor.**
> 본 결과물은 LLM 기반 시뮬레이션이며 투자자문이 아닙니다. 모든 투자 판단과 책임은 투자자 본인에게 있습니다. 종목별 5-Dimension 점수의 일부(재무·밸류 정밀치)는 애널리스트 추정으로, 실제 집행 전 최신 재무제표·수주공시로 재검증이 필요합니다.
