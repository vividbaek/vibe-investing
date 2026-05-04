# Pharma Sector Long/Short Prompt — 4-LLM Comparative Analysis

**비교 대상 모델:** ChatGPT · Claude · DeepSeek · Gemini
**프롬프트 일자:** 2026-05-04
**프롬프트 종류:** 미국 제약 섹터 Long/Short 포트폴리오 (12–24개월 horizon)
**비교 방법:** 동일 프롬프트, 동일 시점, 동일 페르소나 — 출력물의 정성·정량 비교

---

## Executive Summary (TL;DR)

### 분량/구조 — 4개 모델 모두 다른 양식

- **Gemini**: 4.13 KB — **가장 짧음** (compressed summary, 2-3분 만에 의사결정 가능)
- **ChatGPT**: 5.16 KB — outline 수준 (사실상 메모)
- **Claude**: 28.5 KB — 한국어 풀리포트 (audit-ready)
- **DeepSeek**: 38.6 KB — 영어 풀리포트 + 기관양식

### DeepSeek의 특이성
DeepSeek의 모회사는 HFT 회사이고 중국의 헤지펀드이다. 딥씨크가 출력한 금융 리포트는 상당히 전문적인 데이터 양식으로 일반적으로 미국의 유료 금융 리포트 양식으로 보인다.
모회사의 특성상 금융 도메인에 대한 이해도가 높기 때문에 리포트 양식 및 분석이 더 뛰어날수도 있다고 추정하고 있다. 
中国人常说一句很有意思的话：“上有政策，下有对策”。这句话放在这里也颇为贴切。至于是否像“山寨”一样的方式去获取数据用于训练，其实仍然值得打一个问号。另一方面，DeepSeek 的母公司本身就是一家专注于高频交易（HFT）的对冲基金，这意味着它很可能本就拥有相当丰富且高质量的数据资源。

### 가장 충격적인 발견 — 5개 양극화 종목 (4-LLM 확장판)

| 종목 | ChatGPT | Claude | DeepSeek | Gemini |
|------|---------|--------|----------|--------|
| **BMY** | SHORT | **LONG** | SHORT | SHORT |
| **AMGN** | LONG | 미언급 | **SHORT** | LONG |
| **GILD** | SHORT | **LONG** | 미언급 | 미언급 |
| **NVO** | LONG #2 | 사실상 부정 | LONG #7 | LONG |
| **MRK** | LONG #3 | 미언급 | LONG #6 | **SHORT (단독)** |

→ **단일 LLM에 의존하면 정반대 포지션이 나올 수 있다는 결정적 증거 (모델이 늘어날수록 더 명확해짐).**

### 단독 발굴 종목 (Contrarian Picks)

| 종목 | 발굴 모델 | 이유 |
|------|----------|------|
| **ARGX** | **Claude 단독** | VYVGART 라벨 확장 모멘텀 — 미드캡 자가면역 |
| **AZN, JNJ** | **DeepSeek 단독** | 다중 Phase 3 readout density (AZN), Icotrokinra 출시 (JNJ) |
| **MDGL (Madrigal)** | **Gemini 단독** | Rezdiffra MASH 시장 first-mover, $270 → $390 target |
| **MRK SHORT** | **Gemini 단독** | Keytruda 2028 LOE + IRA 노출 — contrarian thesis |

### DeepSeek 영어 출력 문제 (6가지 메커니즘 — 변동 없음)

1. **훈련 데이터 편향**: 중국+영어 코퍼스 주력, 한국어 instruction-following 약함
2. **명시적 언어 강제 부재**: 프롬프트에 "한국어로"라는 지정 없음
3. **도메인 활성화 효과**: "S&P 500/PDUFA/FDA" 등 영문 약어 70+ 등장 → 모델이 영어 도메인으로 인식
4. **Reasoning Mode 특성**: DeepSeek-R1/V3는 사고 과정 자체가 영어
5. **Token 효율 학습**: 한·영 혼합보다 영어 통일이 토큰 효율적
6. **페르소나 효과**: "Senior Healthcare Portfolio Manager"가 영문 도메인 트리거

> **해결법**: 프롬프트 끝에 **"모든 출력은 반드시 한국어로 작성"** 명시 한 줄이면 99% 해결.

### 데니스의 워크플로우 추천 (4-LLM 버전)

이미 multi-LLM cross-validation을 하고 계신 점은 **best practice**입니다. CTI 리포트의 KR/EN/CN/JP 4개국어 발행 노하우와 정확히 같은 패턴 — Gemini로 핵심 종목 hint 빠르게 잡고, DeepSeek로 facts/numbers 풀 채우고, Claude로 한국어 narrative + audit-ready 1차 출처 확보, ChatGPT로 sanity check, **BMY·AMGN·GILD·MRK 같은 양극화 종목은 사람이 결정**하는 구조입니다.

> **특이점**: ChatGPT와 Gemini는 모두 **stale data** 흔적이 명확합니다 (LLY $820/$780 vs 실제 ~$960). Q1 2026 실적(4월 30일 발표)과 Foundayo 승인(4월 1일)이 두 모델 모두 누락. **Web search 활용은 Claude/DeepSeek만 적극적**입니다.

---

## 비교 대상 파일

| 모델 | 파일 크기 | 라인 수 | 출력 언어 | 분량 평가 |
|------|----------|---------|----------|-----------|
| **Gemini** | 4.13 KB | 73 lines (실제 ~55) | 한국어 | 가장 짧음 (compressed) |
| **ChatGPT** | 5.16 KB | 240 lines (실제 ~166) | 한국어 + 영어 혼용 | outline 수준 |
| **Claude** | 28.5 KB | 492 lines (실제 ~373) | 한국어 | 풀리포트 (중간) |
| **DeepSeek** | 38.6 KB | 555 lines (실제 ~400) | **영어 (전체)** | 풀리포트 (가장 긺) |

---

## 종목 선정 — 핵심 차이 (4-LLM)

### LONG 후보 비교

| 티커 | ChatGPT | Claude | DeepSeek | Gemini | 합치/분기 |
|------|---------|--------|----------|--------|----------|
| **LLY** | #1 (92) | #1 (85) | #1 (89) | #1 (95) | **4사 만장일치 1순위** |
| **VRTX** | #6 (83) | #2 (86) | #4 (83) | #2 (92) | 4사 LONG |
| **ABBV** | #4 (85) | #3 (86) | #2 (88) | #4 (87) | 4사 LONG |
| **REGN** | #5 (84) | #5 (80) | 미언급 | #3 (89) | DeepSeek만 누락 |
| **NVO** | #2 (91) | 미언급 (부정) | #7 (78) | #6 (86) | Claude만 부정 |
| **MRK** | #3 (88) | 미언급 | #6 (80) | **SHORT** | **Gemini SHORT, 나머지 LONG** |
| **AMGN** | #7 (82) | 미언급 | **SHORT** | #5 (84) | ChatGPT/Gemini LONG vs DeepSeek SHORT |
| **AZN** | 미언급 | 미언급 | #3 (86) | 미언급 | DeepSeek 단독 |
| **JNJ** | 미언급 | 미언급 | #5 (81) | 미언급 | DeepSeek 단독 |
| **BMY** | SHORT | #4 (83) | SHORT | SHORT | Claude만 LONG |
| **GILD** | SHORT | #6 (82) | 미언급 | 미언급 | Claude만 LONG |
| **ARGX** | 미언급 | #7 (79) | 미언급 | 미언급 | Claude 단독 |
| **MDGL** | 미언급 | 미언급 | 미언급 | #7 (80) | **Gemini 단독** |

### SHORT 후보 비교

| 티커 | ChatGPT | Claude | DeepSeek | Gemini | 비고 |
|------|---------|--------|----------|--------|------|
| **PFE** | #2 (87) | #1 (80) | #2 (79) | 미언급 | 3사 SHORT, Gemini 미언급 |
| **BMY** | #1 (91) | LONG | #3 (76) | #1 (63) | Claude만 반대 |
| **BIIB** | 미언급 | #2 (73) | 미언급 | #2 (67) | Claude/Gemini 합치 |
| **MRK** | LONG #3 | 미언급 | LONG #6 | **#3 (68)** | **Gemini 단독 SHORT** |
| **AMGN** | LONG | 미언급 | #1 (85) | LONG | DeepSeek 단독 SHORT |
| **GILD** | #3 (85) | LONG | 미언급 | 미언급 | ChatGPT 단독 SHORT |
| **MRNA** | 미언급 | #3 (75) | 미언급 | 미언급 | Claude 단독 |

### 가장 극명하게 갈린 5개 종목

1. **BMY**: 3사 SHORT vs **Claude는 LONG** (Forward P/E ~9x + 후반 readout 집중)
2. **AMGN**: ChatGPT/Gemini LONG (MariTide 비만 옵션) vs **DeepSeek SHORT** (denosumab biosimilar 9개)
3. **GILD**: ChatGPT SHORT (HIV 포화) vs **Claude LONG** (Yeztugo 5배 가이던스) — DeepSeek/Gemini 미언급
4. **NVO**: ChatGPT 91점 LONG vs Claude 사실상 부정 vs DeepSeek/Gemini 약하게 LONG
5. **MRK**: 3사 LONG (Winrevair, Keytruda Qlex) vs **Gemini SHORT** (Keytruda 2028 LOE + IRA 노출)

> **시사점**: 모델 수가 늘수록 양극화 종목이 더 드러난다. BMY, MRK, AMGN, GILD, NVO 등 **전체 미국 제약 메가캡의 절반 이상**이 LLM 간 의견이 갈린다. 단일 모델 의존은 사실상 *모델별 룰렛 게임*.

---

## 정량 평가 — 점수 인플레이션 패턴 (4-LLM)

| 모델 | LONG 최고 | LONG 최저 | 점수 범위 | 평균 | SHORT 점수 | 인플레이션 |
|------|----------|----------|----------|------|-----------|----------|
| ChatGPT | 92 | 82 | 10 | 86.4 | 85, 87, 91 | **높음** (모두 80후반~90대) |
| Claude | 86 | 79 | 7 | 82.6 | 73, 75, 80 | **보수적** (정규분포 가까움) |
| DeepSeek | 89 | 78 | 11 | 83.6 | 76, 79, 85 | **중간** |
| **Gemini** | **95** | **80** | **15** | **87.6** | **63, 67, 68** | **이중 성격** (LONG 인플레/SHORT 압축) |

**관찰**:
- **Gemini의 점수 폭이 가장 넓다 (15점)** — LONG에서 95점이라는 매우 자신감 있는 점수까지 부여
- **Gemini의 SHORT 점수는 60대로 매우 낮음 (63~68)** — SHORT 포지션에 대한 conviction이 약함을 시사. 이는 squeeze 위험을 암묵적으로 반영한 보수적 자세로 해석 가능
- ChatGPT는 LONG·SHORT 모두 80~90대 클러스터 → 가장 변별력 부족
- Claude는 모든 점수가 70대 후반~80대 후반 → 가장 균형 잡힌 분포

---

## 시나리오 수익률 — 모델별 낙관/비관 편차

| 모델 | Bull | Base | Bear | 형식 |
|------|------|------|------|------|
| ChatGPT | +18% | +11% | -6% | 단일값, 단순 |
| Claude | +20.5% | +9.9% | -5.0% | 단일값 + 계산식 명시 |
| DeepSeek | **+22~28%** | **+10~16%** | **-5~-12%** | **레인지 + 가정 명시** |
| **Gemini** | **미제시** | **+15%** | **미제시** | **Base만 단일값** |

**평가**:
- DeepSeek만 레인지로 제시 → 학술/기관 IC 보고서 스타일
- Claude는 계산식 ("+25% × 0.7 + +10% × 0.3 = +20.5%") 노출 → 백테스트 추적성
- **Gemini는 Bull/Bear 시나리오 자체가 없음** → 의사결정 보조 도구로서는 불완전. 다만 "S&P Healthcare 대비 Alpha 8%"라는 *상대수익률* 지표 추가 → 단순함 속의 명확함

---

## 1차 출처 (Primary Sources) 인용 깊이

| 항목 | ChatGPT | Claude | DeepSeek | Gemini |
|------|---------|--------|----------|--------|
| 종목별 SEC EDGAR 링크 | LLY만 | **모든 종목** | **모든 종목** | 일반 검색 링크만 |
| ClinicalTrials.gov NCT 번호 | 1건 | 다수 (NCT05051579 등) | 다수 (NCT06564142 등) | **3건** (LLY/VRTX/AMGN) |
| 회사 IR URL | LLY만 | 모든 종목 | 모든 종목 | 없음 |
| 회사 8-K 직접 링크 | 없음 | **다수** (LLY/ABBV/BMY/GILD) | 없음 | 없음 |
| 재확인 필요 표시 | 일부 | **체계적** | **체계적** + Compliance Checklist | 일부 |
| Q1 2026 실적 데이터 | 없음 | **풍부** | **풍부** | **없음** |

**평가**:
- ChatGPT/Gemini: 사실상 **출처 인용이 부재** → 검증 비용 매우 높음
- Claude/DeepSeek: audit-ready 수준
- **Claude만 8-K 직접 링크** → 가장 깊은 추적성

---

## 데이터 정확성 — 학습 cutoff 활용 비교 (4-LLM)

### 가격 데이터 정확도 (2026-05-04 기준)

| 종목 | ChatGPT | Claude | DeepSeek | Gemini | 실제 |
|------|---------|--------|----------|--------|------|
| LLY | $820 (오류) | $963 (정확) | $963 (정확) | **$780 (오류, 가장 큼)** | ~$961 |
| NVO | $125 (오류) | 미평가 | $68 (정확) | **$130 (오류)** | ~$40~68 |
| VRTX | $470 (편차) | $430 (정확) | $436 (정확) | $420 (정확) | ~$429~436 |
| ABBV | $165 (편차) | $185 (편차) | $206 (정확) | $175 (편차) | ~$190~206 |
| AMGN | 미평가 | 미평가 | $300 (정확) | $305 (정확) | ~$300 |
| REGN | 미평가 | $750 | 미평가 | $940 | ~$750~940 |
| MRK | $135 | 미평가 | $112 (정확) | $125 (편차) | ~$112 |
| BIIB | 미평가 | 미평가 | 미평가 | $210 (편차) | ~$160~200 |
| BMY | $55 (편차) | 미평가 | $58 (정확) | $46 (오류) | ~$58 |

**핵심 관찰**:
- **Claude/DeepSeek은 web search 활용 → Q1 2026 실적 발표 후 가격 반영**
- **ChatGPT/Gemini는 stale data 의존 → LLY $820/$780 등 명백한 cutoff data 출력**
- Gemini의 LLY $780은 4개 모델 중 가장 부정확 — 학습 cutoff가 더 이른 시점일 가능성

### Q1 2026 실적 반영도

| 데이터 포인트 | ChatGPT | Claude | DeepSeek | Gemini |
|-------------|---------|--------|----------|--------|
| LLY Q1 매출 $19.8B (+56%) | 누락 | 반영 | 반영 | 누락 |
| LLY 가이던스 상향 ($82~85B) | 누락 | 반영 | 반영 | 누락 |
| ABBV Skyrizi $4.483B (+30.9%) | 누락 | 반영 | 반영 | 누락 |
| BMY Camzyos $314M (+97%) | 누락 | 반영 | 누락 | 누락 |
| Foundayo (Orforglipron) FDA 승인 | 누락 | 반영 | 반영 (4/1, "294 days early") | 누락 |
| VRTX Povetacicept RAINIER 데이터 | 누락 | 누락 | 반영 (52% proteinuria 감소) | 누락 |
| VX-548 / Suzetrigine 통증 | 일반 | 반영 | 반영 | **반영** |
| AbbVie Cerevel ($8.7B 인수) | 누락 | 누락 | 반영 | 누락 |
| Madrigal Rezdiffra MASH | 누락 | 누락 | 누락 | **반영 (단독)** |

**평가**:
- **DeepSeek > Claude >> Gemini > ChatGPT** 순으로 Q1 2026 데이터 반영도
- Gemini는 **VX-548 PDUFA(2026-09)와 MDGL Rezdiffra**에는 정확하지만, 그 외 Q1 실적은 거의 누락
- ChatGPT는 사실상 학습 데이터 그대로 출력

---

## 모델 별 강점·약점 종합 (4-LLM)

### Gemini (신규 분석)
**강점**:
- **분량 효율의 정점** — 4KB로 핵심 결론 모두 전달
- **MDGL 단독 발굴** — MASH 시장 first-mover (Rezdiffra) 식별 능력
- **MRK SHORT thesis** — Keytruda 2028 LOE + IRA 노출을 contrarian 시각으로 수용한 유일한 모델
- SHORT 점수 60대 압축 → squeeze 위험을 암묵적으로 인식
- 카탈리스트 캘린더는 **3개 핵심 이벤트만** 추출 (5월/6월/9월) → 의사결정 효율적

**약점**:
- **가격 데이터가 가장 부정확** (LLY $780 등) — Web search 미활용 추정
- Bull/Bear 시나리오 부재 → 리스크 매니지먼트 도구 미흡
- 출처 인용 얕음 (NCT 3건, SEC/IR URL 부재)
- Q1 2026 실적 거의 누락 → 알파 판단 근거 약함
- 단일 분자/단일 카탈리스트 의존도 분석 부족 (예: VRTX의 VX-548 외 파이프라인 언급 없음)

### ChatGPT
- 강점: 빠른 outline, 프롬프트 의도 파악
- 약점: stale data, 점수 인플레, 출처 부재, Q1 2026 누락

### Claude
- 강점: 한국어 + audit-ready + 8-K 직접 인용 + contrarian (BMY/GILD LONG) + ARGX 단독 픽
- 약점: Risk Dashboard 부재, M&A 정보 부족

### DeepSeek
- 강점: 가장 풍부 + 기관양식 (Risk Dashboard, Compliance Checklist) + M&A 정보 + 레인지 시나리오
- 약점: 한국어 프롬프트에 영어 답변 (운영 이슈)

---

## 모델별 "캐릭터" 한 줄 요약

| 모델 | 캐릭터 | 비유 |
|------|--------|------|
| **ChatGPT** | 빠르지만 학습 데이터 의존 | 작년 데이터로 답변하는 인턴 |
| **Claude** | 한국어 audit-ready + contrarian | 꼼꼼한 한국 운용사 시니어 분석가 |
| **DeepSeek** | 영문 기관양식 + 풍부한 M&A 정보 | 글로벌 IC 미팅 자료 작성하는 글로벌 컨설턴트 |
| **Gemini** | 짧고 contrarian + 단독 픽 | 핵심만 짚는 미니멀리스트 + 컨트래리언 픽커 |

---

## 데니스(사용자) 관점에서의 활용 가이드 (4-LLM 버전)

> 사용자가 BetaLabs CEO + Web3Paper 운영 + CTI 리포트 발행 등 멀티-모달 분석가임을 고려한 권장.

### 시나리오별 모델 선택

| 사용 목적 | 추천 모델 | 이유 |
|----------|----------|------|
| **한국어 클라이언트용 리포트 초안** | **Claude** | 한국어 자연성 + 8-K 직접 인용 + audit 가능 |
| **글로벌 IC/펀드 매니저 양식** | **DeepSeek** | Risk Dashboard + Compliance Checklist + 영어 |
| **빠른 outline / 아이디어 brain-dump** | **ChatGPT** | 간결, 다만 출처는 별도 검증 필요 |
| **Contrarian 발굴 / 컴팩트 요약** | **Gemini** | MDGL/MRK SHORT 같은 단독 픽 + 짧은 분량 |
| **Web3Paper 같은 미디어 컨텐츠 / 한·영·중 4개국어** | **Claude + DeepSeek 병행** | 한국어는 Claude, 영어 풀버전은 DeepSeek |
| **CTI 리포트 양식 (KR/EN/CN/JP) 적용** | **DeepSeek 기반 + Claude 한국어 번역** | DeepSeek 영문 정확도 + Claude 한국어 톤 |
| **30초 이내 의사결정 sketch** | **Gemini** | 4KB 안에 핵심 종목 + 점수 + 카탈리스트 모두 포함 |

### 데니스의 4-LLM 워크플로우 추천

<p align="center">
  <img src="./assets/multi_llm_pharma_workflow.svg" alt="4-LLM Pharma Long/Short Workflow — Gemini contrarian 픽 → DeepSeek facts/M&A 풀 → Claude 한국어 audit-ready 베이스 → ChatGPT sanity check → 사람의 최종 결정 → KR/EN 양본 발행" width="680">
</p>

<details>
<summary>워크플로우 텍스트 버전 (접근성용)</summary>

```
[1] Gemini = 30초 내 종목 hint + contrarian 픽 (MDGL, MRK SHORT 같은 idea)
   ↓
[2] DeepSeek = 글로벌 facts/numbers/M&A 풀 (Cerevel, Alpine, Metsera 같은 누락 정보)
   ↓
[3] Claude = 한국어 narrative + Q1 8-K 1차 인용 베이스
   ↓
[4] ChatGPT = 빠른 sanity check / outline 비교 (오류 검증용)
   ↓
[5] BMY·AMGN·GILD·MRK·NVO 같은 양극화 종목은 사람이 최종 결정
   ↓
[6] CTI 리포트 양식처럼 KR/EN 양본을 모두 발행
```

</details>

이 워크플로우는 데니스의 기존 Multi-LLM Cross-Validation 패턴과 정확히 호환됩니다. 4번째 모델 추가 비용은 거의 없지만, **양극화 종목이 1개 더 발견** (MRK)되었고 **단독 픽 1개** (MDGL)을 추가 확보했습니다 — ROI 측면에서 4-LLM이 3-LLM보다 명확히 우월합니다.

---

## 중요 발견 — 단일 LLM 의존의 위험성 (4-LLM 확장)

### 1. 종목 선정 자체가 뒤집힘 (5개 종목으로 확장)
- **BMY**: Claude 매수 / 나머지 3사 매도
- **AMGN**: ChatGPT/Gemini 매수 / DeepSeek 매도
- **GILD**: Claude 매수 / ChatGPT 매도
- **MRK**: 3사 매수 / **Gemini 매도 (단독)**
- 단일 모델만 사용했다면 *완전 정반대 포지션*을 잡을 수 있다.

### 2. 데이터 cutoff 의존도 차이 (Web Search 정책 분기)
- **활용 적극**: Claude, DeepSeek (Q1 2026 실적, Foundayo 승인 모두 반영)
- **활용 미흡**: ChatGPT, Gemini (LLY 가격 $820/$780 stale data)
- 같은 프롬프트라도 **모델의 web search 활용 정책이 출력의 알파를 좌우**

### 3. Linguistic Bias (DeepSeek 특이점)
- DeepSeek의 영어 출력은 모델 내부 **도메인-언어 정렬 메커니즘**의 노출
- 한국어 도메인 작업 시 명시적 언어 강제는 RAG/Agent 시스템 설계에서 first-class 변수

### 4. Score Inflation은 의사결정 노이즈
- ChatGPT의 90점 클러스터링 = *자신감의 가짜 신호*
- Gemini의 LONG 95점 vs SHORT 63점 = **이중 성격** (LONG 인플레, SHORT 보수적)
- 정량 점수 비교 시 **모델별 정규화** 필수

### 5. 분량과 정보 밀도는 별개
- Gemini 4KB < ChatGPT 5KB이지만, **Gemini가 contrarian 픽을 더 많이 포함**
- DeepSeek 38KB가 가장 길지만, REGN 미언급 등 **분량이 곧 완전성을 보장하지 않음**
- **분량보다 *발굴 다양성*이 alpha의 원천**

---

## 부록: 4-LLM 비교 매트릭스 한눈에 보기

| 평가 차원 | ChatGPT | Claude | DeepSeek | Gemini |
|----------|---------|--------|----------|--------|
| 분량 | 부족 | 충분 | 매우 충분 | **압축적** |
| 한국어 적합도 | 양호 | **우수** | 미흡 (영어) | **우수** |
| 출처 깊이 | 부족 | **우수** (8-K) | 우수 | 부족 |
| Q1 2026 반영 | 부족 | **우수** | **우수** | 부족 |
| 가격 정확도 | 부족 (stale) | 우수 | **우수** | 부족 (가장 stale) |
| 점수 변별력 | 부족 | 양호 | 양호 | 우수 (15점 폭) |
| 구조/포맷 | 부족 | 양호 | **우수** (기관양식) | 양호 (압축) |
| 시나리오 정밀도 | 부족 | 양호 | **우수** (레인지) | 부족 (Base만) |
| Risk Mgmt 도구 | 부족 | 양호 | **우수** | 부족 |
| Contrarian 시각 | 부족 | **우수** (BMY/GILD LONG) | 부족 | **우수** (MRK SHORT) |
| 미드캡 발굴 | 부족 | **우수** (ARGX) | 부족 | **우수** (MDGL) |
| M&A 정보 | 부족 | 부족 | **우수** (Cerevel/Alpine) | 부족 |
| 의사결정 효율 | 양호 | 양호 | 부족 (긺) | **우수** (4KB) |
| **종합 (Pharma 전용)** | **2.0 / 10** | **7.5 / 10** | **7.5 / 10** | **6.0 / 10** |

---

## 결론

> **"동일 프롬프트, 동일 시점, 4개 모델 → 4개 다른 포트폴리오"**

4개 모델은 **구조적으로 다른 종목 선정 결과**를 산출했다:
- ChatGPT: outline + stale data
- Claude: 한국어 audit-ready + contrarian (BMY/GILD/ARGX)
- DeepSeek: 영어 기관양식 + M&A 풍부 + AZN/JNJ 픽
- **Gemini: 압축적 + MDGL 단독 + MRK SHORT (4사 중 유일)**

가장 흥미로운 발견은:

1. **양극화 종목이 4-LLM 비교에서 5개로 확장** (BMY, AMGN, GILD, NVO, **MRK**) — 단일 LLM 의존 시 알파 손실 또는 손실 발생 위험 상승
2. **Gemini의 MDGL 단독 발굴** — 미드캡 contrarian 픽 능력은 분량과 무관 (4KB로도 가능)
3. **Gemini의 MRK SHORT** — 다른 3사가 Winrevair 모멘텀에 가려진 *Keytruda 2028 LOE 위험*을 정면 인식
4. **Web search 정책이 정확도를 결정** — Claude/DeepSeek vs ChatGPT/Gemini로 양분
5. **Multi-LLM cross-validation은 비용이 아니라 보험** — 데니스의 기존 워크플로우는 이미 best practice이며, **4-LLM 확장 시 ROI는 더 높음**

투자 결정 전 4개 모델 모두 동시 실행:
- **Gemini**: 30초 contrarian 픽 발굴
- **Claude**: 한국어 audit 베이스
- **DeepSeek**: 영어 facts/numbers 풀
- **ChatGPT**: sanity check

양극화된 종목(BMY, AMGN, GILD, MRK, NVO)은 사람이 결정.

## Gemini 특이점 4가지

가장 짧음 (4.13KB) — ChatGPT보다도 짧지만 핵심은 더 풍부합니다. "압축적 효율"의 정점이고, 30초 의사결정 sketch에 적합합니다.
MDGL (Madrigal) 단독 발굴 — Rezdiffra(MASH 시장 first-mover, 2024년 첫 FDA 승인)를 픽한 유일한 모델입니다. Claude의 ARGX, DeepSeek의 AZN/JNJ와 같은 "단독 발굴 능력" — 분량과는 무관하게 contrarian 미드캡 발굴 가능성을 보여주는 사례입니다.
MRK를 SHORT로 분류한 4사 중 유일 — ChatGPT/DeepSeek가 모두 LONG으로 본 Merck를 Gemini는 Keytruda 2028 LOE + IRA 노출을 이유로 SHORT로 분류했습니다. 다른 3사가 Winrevair 모멘텀에 가려진 구조적 위험을 정면으로 인식한 contrarian thesis입니다.
이중 성격 점수 분포 — LONG 80~95점 (15점 폭, 가장 넓음) vs SHORT 63~68점 (5점 폭, 매우 압축). LONG에는 자신감, SHORT에는 squeeze 위험을 암묵적으로 반영한 보수적 자세를 보입니다.

## 4-LLM 핵심 인사이트 갱신

양극화 종목이 4개 → 5개로 확장: BMY, AMGN, GILD, NVO에 MRK 추가
데이터 정확도 양분 명확화: Claude·DeepSeek (web search 활용) vs ChatGPT·Gemini (stale data) — Gemini의 LLY $780은 4사 중 가장 부정확
종합 점수: Claude/DeepSeek 7.5점, Gemini 6.0점, ChatGPT 2.0점 — Gemini는 분량 부족과 출처 얕음으로 감점되었지만 contrarian 발굴 능력으로 ChatGPT를 크게 앞섭니다.

---

*본 비교 분석은 2026-05-04 시점 동일 프롬프트로 산출된 4개 LLM 출력물을 대조 분석한 결과입니다. 분석 자체는 투자 자문이 아니며, 실제 투자 결정은 1차 출처 재확인 후 자격 있는 자문가와 상의하시기 바랍니다.*

*Repository: [vibe-investing/Pharma sector prompt](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Pharma%20sector%20prompt)*
