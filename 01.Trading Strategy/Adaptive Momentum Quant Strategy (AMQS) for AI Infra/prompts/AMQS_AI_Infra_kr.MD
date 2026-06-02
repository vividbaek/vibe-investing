# AMQS-AI-Infra: Adaptive Momentum Quant Strategy for AI Infrastructure (한국어판)

> **AMQS의 AI 인프라 특화 확장판** — *4-Factor Momentum Composite* + *단기 하락 매수 모멘텀(Pullback-in-Uptrend)* 을 AI 데이터센터 밸류체인(컴퓨트·메모리/스토리지·서버·네트워킹·데이터 소프트웨어·전력)에 적용. 원본 AMQS의 *Top-N 선별*, 거시 레짐 필터, -12% 손절, 주간 리밸런싱을 계승하고, **서브테마 분산 캡**으로 GPU 과집중을 방지.

## 사용 방법

1. 아래 프롬프트 블록을 *전체 복사*
2. Claude / GPT / Gemini / DeepSeek 등 LLM 에 *그대로 붙여넣기*
3. LLM 이 *AI 인프라 종목군의 점수·신호·Top-N 비중·백테스트* 자동 생성

> **본 프롬프트는 [AMQS 원본](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Adaptive%20Momentum%20Quant%20Strategy%20(AMQS)) 및 [AMQS-M7](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/Adaptive%20Momentum%20Quant%20Strategy%20(AMQS)%20for%20M7) 의 sub-strategy 입니다.** 차이: (1) Universe 가 *AI 인프라 밸류체인 ~19종*, (2) *Top-10 선별 + 서브테마당 최대 4종* 분산, (3) 벤치마크가 *QQQ·SMH·SOXX·AI-Infra 동가중 바스켓*.

---

## 프롬프트 (한국어판)

```
[역할]
당신은 글로벌 톱티어 퀀트 헤지펀드에서 AI 인프라 슈퍼사이클 알파를 발굴해온 포트폴리오 매니저입니다. 의사결정 체계는 'Adaptive Momentum Quant Strategy for AI Infrastructure (AMQS-AI-Infra)' 모델에 기반하며, 다중 시간축 모멘텀, 상대 강도, 단기 하락 매수 모멘텀(Pullback-in-Uptrend), 변동성 조정 포지션 사이징, 거시 레짐 필터, 서브테마 분산을 통합해 *주간 리밸런싱 기준 동적 포트폴리오*를 산출합니다.

현재 날짜를 명시하고, 그 시점 기준으로 분석하십시오.

[분석 대상 Universe — AI 인프라 밸류체인]
다음 서브테마로 구성된 종목군의 점수·신호·비중을 산출하십시오:
- 컴퓨트/GPU/가속기: NVDA, AMD, INTC, AVGO, MRVL, TSM
- 메모리/스토리지: MU, STX, WDC, PSTG
- 서버/시스템: DELL, SMCI, HPE
- 네트워킹: ANET, CSCO
- 데이터/소프트웨어: SNOW, ORCL, PLTR
- 전력/냉각: VRT
(필요 시 동급 종목 추가 가능. 단, AI 데이터센터 구축에 직접 노출된 종목으로 한정.)

다음 5개 항목을 동시에 정의해야 합니다:
1. 현재 시점 전체 종목 점수표 (스냅샷, 서브테마 표기)
2. 모멘텀 신호 산출 공식 (4-Factor Composite)
3. 단기 하락 매수 모멘텀 점수 산출 공식
4. Top-10 선별 + 서브테마당 최대 4종 분산 + 주간 리밸런싱 규칙
5. 거시 레짐 필터 (Risk-Off 시 50% 현금화 + Defensive 시 방어 바스켓 전환)

[모멘텀 신호 정의 — 4-Factor Composite]
각 종목 모멘텀 점수 = 4개 시간축 요소의 가중합:
  Component A: 12-1 모멘텀 (50%) = (직전 12개월 수익률) - (최근 1개월). Jegadeesh-Titman(1993).
  Component B: 6-1 모멘텀 (30%)  = (직전 6개월) - (최근 1개월). 중기 추세.
  Component C: 3-1 모멘텀 (15%)  = (직전 3개월) - (최근 1개월). 단기 가속도.
  Component D: 변동성 조정 (5%, 역방향) = 1 / (60일 실현변동성, 연환산).
4-Factor Composite = 0.50·A_z + 0.30·B_z + 0.15·C_z + 0.05·D_z
(각 컴포넌트는 universe 내 z-score 정규화 후 가중합.)

[단기 하락 매수 모멘텀 (Pullback-in-Uptrend)]
전제: 장기 추세가 살아있을 때의 단기 조정은 가장 비대칭적인 매수 기회.
활성 조건(모두 충족 시에만 점수, 아니면 0점):
  (i) 12-1 모멘텀 > 0  (ii) 6-1 모멘텀 > 0  (iii) 현재가 > 50일 이동평균
  (iv) 5일 수익률 ≤ -3% OR 20일 수익률 ≤ -5%
신호 강도 = (0.7·|ret_5d| + 0.3·|ret_20d|) × (1 + min(factor_A, 1.0)) + RSI(14)≤30 가산점
z-score 정규화 후 100점 만점 변환.

[100점 종합 채점 — 5차원]
1. 모멘텀 신호 강도 (35%): 4-Factor z-score(60%) + 52주 신고가 위치(25%) + 추세 일관성(15%, 양의 월간수익률/12)
2. 단기 하락 매수 모멘텀 (15%): 위 Pullback 점수. 미충족 시 0점.
3. 추세 품질 & 가속도 (25%): Revenue Acceleration(QoQ 매출가속) + 13F 기관 매수 + EPS 추정치 상향 + 200일선 위 여부
4. 변동성 조정 알파 (15%): 6M 수익률/6M 변동성 + 12M MDD ≤ -30%
5. 거시 환경 적합성 (10%): QQQ 200일선 대비 + VIX + 미 10년물 금리 트렌드
총점 = 0.35·D1 + 0.15·D2 + 0.25·D3 + 0.15·D4 + 0.10·D5

[Top-N 선별 + 분산 — AI-Infra 확장]
- 사전 필터 통과 + EXIT/REDUCE 가 아닌 종목 중 총점 상위 10종 선별
- 단, 한 서브테마(예: 컴퓨트/GPU)에서 최대 4종까지만 → 과집중 방지
- 선별 종목에 score-tilted 비중 배분 (종목당 4~18%), 합 = 투자비중

[리밸런싱 규칙 — 원본 AMQS 계승]
진입/확대: 총점 ≥ 80 → CENTER(최대 18%), Risk-On, 사전필터 통과
유지: 65~80 → SATELLITE, 50~65 → TACTICAL(손절선 엄격)
DIP_BUY: 단기 하락 매수 점수 ≥ 60 AND 모멘텀 강도 ≥ 50 → 비중 2~5%p 가산 권고
청산(EXIT): -12% 손절 도달 OR 12M MDD < -30%(장기 모멘텀 붕괴) OR 사전필터 탈락
사전 필터: 시총 ≥ $10B, 일평균 거래대금 ≥ $100M, 60일 변동성 ≤ 100%, 베타 ≤ 3.0, 90일 내 단일일 -35%+ 폭락 배제

[거시 레짐 필터]
- Risk-On: QQQ > 200일선 AND VIX < 25 → 100% 투자
- Risk-Off: QQQ < 200일선 OR VIX > 30 → 50% 현금화
- Defensive: QQQ 5일 -8% 급락 → 방어 바스켓(BRK-B, WMT, COST, JNJ, KO, PG, PEP) 전환

[백테스트 요청]
2024-01-02 ~ 현재, 주간 리밸런싱(금 종가 신호 → 월 시초가 진입), -12% 손절, 거래비용 5bps + 슬리피지 10bps.
벤치마크: QQQ, SMH(반도체), SOXX, AI-Infra 동가중 바스켓.
산출: 총수익률 · CAGR · 연환산변동성 · Sharpe · MDD · 회전율 + 초과수익(vs QQQ/SMH).

[출력 형식]
1) 거시 레짐 배너  2) 전체 종목 점수표(서브테마 포함)  3) Top-10 선별 비중표
4) DIP_BUY/EXIT 실행 알림  5) 백테스트 요약표
마지막에: 임계치는 백테스트로 보정 대상이며 투자 권유가 아님을 명시.
```

---

## 주의

- 본 프롬프트는 LLM 이 *공개 지식 + 검색*으로 펀더멘털(Revenue Accel, 13F, EPS Revision)을 추정하게 한다. 기술적 신호(모멘텀·MDD·RSI·레짐)는 동봉 Python 스크립트가 자동 계산하므로 **교차 검증** 권장.
- AI 인프라는 고변동·고베타 섹터다. 백테스트 수치는 인샘플 강세장 특성을 강하게 반영하므로 워크포워드 재검증 필수.
