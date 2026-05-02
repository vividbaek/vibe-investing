# Dividend Growth Prompt — 삼중 언어 LLM 비교 실험

## 한국어 / 영문 / 중국어 프롬프트로 동일한 미국 배당 성장 종목 발굴 작업을 수행했을 때 LLM은 어떻게 다른 답을 내는가?

**실행 일자**: 2026년 5월 2일
**대상 LLM**: Claude Opus 4.7, DeepSeek V3.1/V4, Gemini 3 Flash
**총 결과물**: 9개 (3 LLM × 3 언어)
**관련 논문**: [Cross_Lingual_LLM_Accuracy_Paper.pdf](result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.pdf) (v4)

---

## 한 줄 요약

> **언어를 바꾸면 LLM의 답도 60-80% 달라진다.** 같은 LLM, 같은 질문, 다른 언어 — 결과 종목의 평균 70%가 변경되며, 이 비대칭은 통계적으로 측정 가능한 "Cross-Lingual Asymmetry" 현상이다.

---

## 디렉토리 구조

```
Dividend growth prompt/
├── README.md                                # 이 문서 (삼중 언어 통합 비교)
├── Readme.md                                # 한국어 결과 비교 (구버전)
├── Dividend Growth Prompt kr.MD             # 한국어 프롬프트 원본
├── Dividend_Growth_Prompt_EN.md             # 영문 프롬프트 원본
├── Dividend_Growth_Prompt_CN.md             # 중국어 프롬프트 원본 (참고)
└── result/
    ├── Claude_Dividend_Growth_Portfolio_Report_2026Q2.md    # KR Claude
    ├── DeepSeek Prompt Result260502.MD                       # KR DeepSeek
    ├── Gemini_Dividend_Growth_Portfolio_2026.md              # KR Gemini
    ├── ENG_Report/
    │   ├── README.md                                          # 영문 결과 비교
    │   ├── claude_dividend_growth_portfolio_2026Q2.md
    │   ├── deepseek_markdown_20260502_2c64e1.md
    │   ├── gemini_report.md
    │   └── Cross_Lingual_LLM_Accuracy_Paper.pdf              # v4 학술 논문
    └── CN_Report/
        ├── China prompt.md                                    # 중국어 프롬프트 원본
        ├── claude_dividend_growth_report.md                  # CN Claude
        ├── deepseek_markdown_20260502_9ac0e8.md              # CN DeepSeek
        └── gemini_cn_report.md                                # CN Gemini
```

---

## 9개 결과물 한눈에 보기

### Top 10 종목 매트릭스

| Rank | Claude KR | Claude EN | Claude CN | DeepSeek KR | DeepSeek EN | DeepSeek CN | Gemini KR | Gemini EN | Gemini CN |
|---|---|---|---|---|---|---|---|---|---|
| 1 | COST | MSFT | V | MSFT | COST | COST | MSFT | UNH | MSFT |
| 2 | UNH | V | MSFT | AVGO | SYK | ABT | AVGO | V | AVGO |
| 3 | ABBV | AVGO | NOC | JNJ | UNH | UNH | UNH | MSFT | MA |
| 4 | V | CTAS | CTAS | PEP | V | V | V | EOG | UNH |
| 5 | BLK | ABBV | EOG | UNH | BLK | BX | JPM | PH | COST |
| 6 | MSFT | LMT | COST | ABBV | MSFT | MSFT | LOW | AVGO | LMT |
| 7 | LRCX | NEE | ABT | CAT | ASML | AMAT | LMT | COST | V |
| 8 | OKE | BLK | AVGO | TXN | LNG | TRGP | COP | BX | TXN |
| 9 | NOC | ABT | BLK | LIN | CTAS | ADP | TMO | SYK | XOM |
| 10 | GWW | HSY | ABBV | BLK | EFX | CTAS | ADP | PEP | ELV |

---

## 동일 추천 (Universal Picks) — 빈도 순위

언어와 LLM을 모두 횡단해 **공통적으로 추천되는 종목**은 매우 적다. 9개 결과물에서 등장 횟수:

| 빈도 | 종목 | 평가 |
|---|---|---|
| **9/9 (100%)** | **MSFT** | **Universal Pick — 유일** 모든 LLM이 모든 언어에서 추천. *LLM 시대의 dividend growth 표준 답안* |
| **8/9 (89%)** | V | DeepSeek KR에서만 누락 (Visa) |
| **7/9 (78%)** | UNH | Claude EN/CN에서 누락 (UnitedHealth) |
| **6/9 (67%)** | AVGO | Claude KR, DeepSeek EN/CN, Gemini EN에서 누락 (Broadcom) |
| **6/9 (67%)** | COST | DeepSeek KR, Gemini KR에서 누락 (Costco) |
| **5/9 (56%)** | BLK | DeepSeek CN, Gemini 모든 언어 누락 (BlackRock) |
| **4/9 (44%)** | ABBV | Claude/DeepSeek 일부 (AbbVie) |
| **4/9 (44%)** | CTAS | Claude/DeepSeek 일부 (Cintas) |
| **3/9 (33%)** | ABT, LMT | 1-2 LLM의 일부 언어만 |

### 핵심 관찰

**38개의 distinct 종목이 9개 결과물에 등장**하지만:
- **6/9 이상의 일치도를 가진 종목은 단 5개** (MSFT, V, UNH, AVGO, COST)
- 나머지 33개 종목은 **4/9 이하의 매우 약한 신호** (low-consensus picks)

**실용적 함의**: 단일 LLM 단일 언어 추천의 56%가 "low-consensus" 카테고리에 해당하며, 후속 검증이 필수.

---

## 차이점 (Cross-Lingual Asymmetry)

### 1. Jaccard Similarity 분석

각 LLM이 자신의 3개 언어 결과 사이에 얼마나 일관성을 보이는가?

| LLM | KR-EN | KR-CN | EN-CN | 평균 $\overline{J}$ | 안정성 순위 |
|---|---|---|---|---|---|
| Claude Opus 4.7 | 0.250 | 0.429 | 0.538 | **0.406** | 1위 (가장 안정) |
| Gemini 3 Flash | 0.250 | 0.333 | 0.333 | **0.306** | 2위 |
| DeepSeek V3.1/V4 | 0.176 | **0.111** | 0.333 | **0.207** | 3위 (가장 불안정) |

**임계값**: $J<0.5$ = "강한 cross-lingual 비대칭". **9개 모든 언어 쌍이 이 임계값 미만**.

### 2. 언어 가족 가설의 부분 반증 (Surprising Finding)

| 언어 쌍 | 평균 Jaccard | 해석 |
|---|---|---|
| EN-CN | 0.401 | 가장 유사 (영문이 hub language?) |
| KR-CN | 0.291 | **같은 CJK인데도 더 비대칭** |
| KR-EN | 0.225 | 가장 비대칭 (다른 언어 가족) |

**의외의 발견**: 한국어와 중국어가 같은 동아시아 언어 가족(CJK)이지만, KR-CN($J$=0.291)이 EN-CN($J$=0.401)보다 더 비대칭. **언어 가족 동일성이 LLM 출력 유사성을 보장하지 않는다.**

### 3. Sharpe Ratio 비교 (정량 메트릭 정확도)

| LLM | KR | EN | CN | 학술적 합리성 |
|---|---|---|---|---|
| Claude | 0.82 | 0.78 | **0.56** | CN이 RFR=4.5% 명시 → 가장 학술적으로 정확 |
| DeepSeek | 1.45 (의심) | 0.92 | 0.92 | KR만 비현실적, EN/CN 정상 |
| Gemini | 1.25 | 1.14 | 1.15 | 모든 언어 "too good" 지속 (Gemini 시그니처) |

**Benchmark = 0.85** (long-only dividend growth 전략의 historical Sharpe 중간값)

| 언어 | 평균 \|MD\| (Sharpe Deviation) | 정확도 |
|---|---|---|
| 영문 (EN) | **0.143** | 가장 정확 |
| 중국어 (CN) | **0.220** | 중간 |
| 한국어 (KR) | **0.343** | 가장 비합리적 |

**EN > CN > KR** 정확도 순서 — H₅ 가설(학습 코퍼스의 학술 자료 밀도) 패턴 일관 관찰.

### 4. 컨텍스트 통합 차이

각 언어가 *자국 투자자의 시각*을 자동 통합:

| 컨텍스트 | KR | EN | CN |
|---|---|---|---|
| 한국 외환거래법, 양도소득세 22%, 종합과세 | **자동 포함** | 누락 | 누락 |
| 미국 거주자 401(k)/Roth IRA 가이드 | 부분 | **자동 포함** | 누락 |
| 중국 본토/홍콩 시각, 지정학적 위험 | 누락 | 누락 | **자동 포함** (특히 DeepSeek CN) |

**해석**: LLM은 *프롬프트 언어에 맞는 거주자 시각*을 자동 활성화. 영문은 미국 시각, 한국어는 한국 거주자 시각, 중국어는 중국/홍콩 시각.

---

## 발견한 특이점 (Unique Findings)

### 특이점 1: Universal Pick은 단 1개 (MSFT)

3 LLM × 3 언어 = 9개 셀에서 **모든 셀에 등장한 종목은 MSFT 단 하나**. 이는:
- Microsoft가 "dividend growth"의 LLM 학습 코퍼스 인코딩에서 가장 강한 신호
- 22년 연속 배당 증가, 25% payout ratio, 10%+ CAGR이라는 specs가 *어느 언어로 표현되어도* 동일하게 인식
- 정성적으로 "**MSFT는 LLM 시대의 dividend growth 표준 답안**"

### 특이점 2: Gemini AVGO 분할 전 가격 hallucination의 *언어 불변성*

Gemini가 **EN과 CN 두 언어에서 동일하게** AVGO 분할 전 가격을 사용:
- Gemini EN: AVGO Yield 1.44%, **Price $1,695**
- Gemini CN: AVGO **Price $1,410**

두 가격 모두 2024년 7월 10:1 분할 *전*의 가격 범위 ($1,500~1,700). 분할 후 정상 가격은 $130~180.

**의미**: Hallucination이 학습 데이터의 무작위 노이즈가 아니라 *모델 가중치에 인코딩된 구조적 결함*. 언어를 바꿔도 해결되지 않는다. 본 연구의 가장 강한 "Hallucination Signature" 증거.

### 특이점 3: BX (Blackstone) Cross-LLM Cross-Language Hallucination

서로 다른 두 LLM이 서로 다른 두 언어로 **동일한 사실 오류**를 발생:
- **Gemini EN**: BX 5Y CAGR 11.5%, dividend growth 카테고리
- **DeepSeek CN**: BX 5Y CAGR 14.8%, "派息基于可分配利润"

**검증된 사실**: Blackstone은 변동 분배 (variable distribution) 모델 — 2022 $1.27 → 2023 $0.91 (-28%) → 2024 $0.82 (-10%). "5+ consecutive years of dividend increases" 조건 명백히 위반.

**의미**: *학습 코퍼스의 공통 편향이 모든 frontier LLM에 동시 영향*. Cross-lingual validation도 universal hallucination은 잡지 못함.

### 특이점 4: Claude CN의 학술적 정확성 역설

Claude CN의 Sharpe = 0.56이 다른 결과보다 낮지만, **학술적으로는 가장 정확**:
- Claude CN은 명시적으로 RFR = 4.5% (현재 10년물 미국채 수준) 적용
- Claude KR/EN은 암묵적으로 더 낮은 RFR 사용
- **결과적으로 Claude CN이 가장 보수적이고 학술적으로 정확한 계산**

**역설**: 표면적으로 보면 Claude CN의 Sharpe가 가장 "낮아 보이지만", 실제로는 가장 정직한 보고.

### 특이점 5: SCHD Top 5 Cross-LLM Holdings Hallucination

DeepSeek EN과 Claude CN 모두 SCHD Top 5에 **historical holdings를 current로 오인**:

**실제 SCHD Top 5** (Stockanalysis.com 2026-04-30 기준):
1. TXN (Texas Instruments) — 5.29%
2. UNH (UnitedHealth) — 5.07%
3. QCOM (QUALCOMM) — 4.16%
4. CVX (Chevron) — 4.09%
5. KO (Coca-Cola) — 4.05%

| LLM/언어 | 보고한 SCHD Top 5 | Hit Rate |
|---|---|---|
| DeepSeek EN | Amgen, Cisco, **Chevron**, BlackRock, PepsiCo | 1/5 (20%) |
| Claude CN | HD, AMGN, **KO**, PEP, ABBV | 1/5 (20%) |

두 다른 LLM, 두 다른 언어, **공통적으로 historical holdings를 current로 오인**.

### 특이점 6: 외국계 ADR을 미국 종목으로 처리 (DeepSeek)

- DeepSeek KR: **LIN** (Linde, 영국 본사)
- DeepSeek EN: **ASML** (Veldhoven, 네덜란드 본사)
- DeepSeek CN: 외국계 ADR 없음 (가장 깨끗)

**의미**: NASDAQ-100 ADR 종목을 "미국 dividend grower"로 혼동. 한국 거주자가 ASML/LIN ADR 보유 시 *네덜란드/영국 원천징수세 + 미국 ADR fee + 한국 종합과세*로 사용자 의도와 명백히 다름.

### 특이점 7: Gemini의 점수 인플레이션 (언어 무관)

Gemini의 평균 점수: KR 90, EN 85, CN 89/92 — 다른 LLM (Claude 81-87, DeepSeek 82-88) 대비 **모든 언어에서 일관되게 인플레이션**.

**의미**: RLHF 학습에서 "높은 점수 = 유용한 답변"으로 학습된 *언어 무관 구조적 결함*.

---

## 실용 권고 — Trilingual Cross-Model Validation Workflow

본 실험 결과에 기반한 한국 투자자용 실용 워크플로:

### Step 1. 영문 프롬프트로 1차 분석 (정량 정확도 확보)
- Sharpe Ratio, Metric Deviation 추출
- 학술적 톤 + 정량 메트릭의 가장 정확한 결과

### Step 2. 한국어 프롬프트로 2차 분석 (한국 투자자 컨텍스트)
- 외환거래법, 양도소득세, 종합과세 자동 통합
- KRW 환율 hedge 분석

### Step 3. 중국어 프롬프트로 3차 cross-validation (추가 신호)
- 지정학적 위험 인지 (DeepSeek CN 특히)
- EN과 다른 종목 추천으로 cross-check

### Step 4. 9개 결과물의 빈도 기반 합의 추출
- **9/9 universal pick**: MSFT (강한 신호)
- **8/9 strong**: V
- **7/9 robust**: UNH
- **6/9 likely**: AVGO, COST
- 그 외는 단일 LLM 단일 언어 추천 → 검증 강화

### Step 5. 단독 추천 종목 검증 강화
- **외국계 ADR 식별**: SEC EDGAR 20-F 파일링으로 본사 위치 확인 (ASML, LIN 등)
- **분할/병합 이벤트 확인**: SEC 8-K 공시로 가격 정합성 검증 (AVGO 같은 케이스)
- **변동 분배 모델 식별**: Form 10-K로 dividend policy 검증 (BX 같은 케이스)

### Step 6. 외부 데이터 소스 교차 검증 (필수)
- **SEC EDGAR**: 펀더멘털, ADR 식별
- **Schwab/Vanguard fact sheet**: ETF holdings (Stockanalysis.com 등도 활용)
- **Morningstar / Sharadar**: 배당 history
- **Yahoo Finance / Google Finance**: 시점별 가격 검증

### 비용 vs 효과
- **추가 비용**: LLM API 비용 약 3배 (3개 언어로 실행)
- **위험 감소**: 단일 언어 단일 모델 의존의 hallucination 위험 약 70% 감소 (정성적 추정)

---

## 학술 논문 (v4)

본 비교 데이터는 다음 학술 논문의 기초 자료:

**김호광 (2026). 같은 LLM, 다른 언어, 다른 답 (v4): 한국어, 영문, 중문 프롬프트가 LLM의 정확도와 데이터 이해에 미치는 영향에 관한 실증 비교 - 삼중 언어 통제 실험 확장판.** vibe-investing GitHub Repository.

- **PDF**: [result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.pdf](result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.pdf)
- **Markdown**: [result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.md](result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.md)
- **LaTeX**: [result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.tex](result/ENG_Report/Cross_Lingual_LLM_Accuracy_Paper.tex)

### 논문 버전 진화

| 버전 | 일자 | 데이터 | 핵심 변화 |
|---|---|---|---|
| v1 | 2026-05-03 | 6 결과물 (KR+EN) | 초판 — qualitative case study |
| v2 | 2026-05-03 | 6 결과물 | 4가지 리뷰 비판 (N=1, 단일 평가자, 토큰 비통제, 환각 검증) 명시 인정 |
| v3 | 2026-05-03 | 6 결과물 | Related Work, 정량 메트릭 (Jaccard/HR/MD), Contributions 박스, 핵심 용어 정의 추가 (학술 paper급 구조) |
| **v4** | **2026-05-04** | **9 결과물 (KR+EN+CN)** | **다국어 확장 가설을 실증으로 전환, B.1 hallucination 공식 출처 검증 (Stockanalysis.com)** |

---

## 가설과 검증 결과

| 가설 | 내용 | v4 검증 결과 |
|---|---|---|
| **H₁** | 영문 프롬프트가 정량 메트릭 정확도를 향상 | 패턴 일관 관찰 (EN $|MD|$=0.143 vs KR 0.343) |
| **H₂** | 한국어 프롬프트가 한국 투자자 컨텍스트 통합 | 패턴 일관 관찰 (5/5 항목 KR 우위) |
| **H₃** | 동일 LLM이라도 언어 변경 시 50%+ 종목 변경 | **패턴 일관 관찰** (평균 trilingual $\overline{J}$=0.306) |
| **H₄** | LLM별 hallucination이 언어 무관 고유 시그니처 | **강하게 관찰됨** (Gemini AVGO 영문/중국어 동일 오류, Claude 1.1% vs Gemini 10.0%) |
| **H₅ (v4)** | 정량 정확도: EN > CN > KR (학술 자료 밀도 비례) | **패턴 일관 관찰** (|MD| 0.143/0.220/0.343 단조 순서) |
| **H₆ (v4)** | Hallucination signature는 언어 가족 초월 | **부분 지지** (Gemini AVGO EN/CN 동일 오류는 강한 증거이나, KR-CN Jaccard가 EN-CN보다 낮은 것은 부분 반증) |

**모든 가설은 N=1 한계로 통계적 유의성 미확보**이며, N≥10 후속 연구에서 검증 예정.

---

## 라이선스 및 인용

**라이선스**: MIT License (자유 사용·수정·배포 가능)

**저자**: 김호광 (Dennis Kim / HoKwang Kim)
- Independent Researcher, Betalabs Inc., CEO, Cyworld Z 전 CEO
- ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
- Email: gameworker@gmail.com

**인용 권장 형식**:

```
Kim, D. (2026). Same LLM, Different Languages, Different Answers (v4):
An Empirical Comparison of Korean, English, and Chinese Prompts on
LLM Accuracy and Data Understanding. vibe-investing GitHub Repository.
https://github.com/gameworkerkim/vibe-investing
```

---

> *"우리는 LLM을 **언어 모델**이라 부르지만, 다른 언어로 같은 질문을 하면 다른 답을 얻는다는 사실은 잊는다.*
> *언어가 곧 컨텍스트이며, 컨텍스트가 곧 답이다."*
> — 본 연구의 핵심 발견
