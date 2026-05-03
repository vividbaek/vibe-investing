# 01. Trading Strategy

vibe-investing 레포의 트레이딩 전략 인덱스입니다.

→ [메인 README로 돌아가기](https://github.com/gameworkerkim/vibe-investing/blob/main/README.md)

---

## 시작 전 반드시 읽을 것

> **LLM은 엑셀이지, 정답을 알려주는 오라클(신탁)이 아니다.**

본 폴더의 모든 LLM 기반 트레이딩 전략은 *사용자의 지식 수준만큼만 작동*하는 도구입니다. 같은 LLM이라도 한국어, 영어, 중국어 입력에 따라 결과가 다르며, 학습 cutoff 이후의 실시간 시장 변화는 인지하지 못합니다.

본 인덱스에 들어가기 전, *Cross-Lingual LLM 검증 연구*와 *MSFT 11/11 사례 칼럼*을 먼저 읽으시면 모든 전략을 더 비판적으로 활용할 수 있습니다.

* [LLM 합의 vs 시장 현실 — 마이크로소프트 사례 칼럼 (PDF v2)](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Dividend%20growth%20prompt/Column_LLM_Consensus_vs_Reality_MSFT_Case_v2.pdf)
* [같은 칼럼 (Markdown)](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Dividend%20growth%20prompt/Column%20llm%20consensus%20vs%20reality%20msft%20case.md)
* [Cross-Lingual LLM Accuracy Paper v5 (학술 논문 릴리즈 예정 )]

---

## 구성

이 폴더는 네 가지 카테고리의 트레이딩 전략과 분석 자료를 담고 있습니다.

| 폴더 | 종류 | 설명 |
| --- | --- | --- |
| [AI-hedge-fund/](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/AI-hedge-fund) | **분석 리포트 (NEW)** | **virattt/ai-hedge-fund 오픈소스 헤지펀드 프레임워크 분석 + 페르소나 AI 평가** |
| [Awesome claude quant scripts/](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts) | 스크립트 모음 | Claude 기반 4종 트레이딩 전략 + Sample 템플릿 + Cross-Lingual LLM 검증 연구 |
| [Luxury investment strategy/](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Luxury%20investment%20strategy) | 단일 전략 + 칼럼 | 명품 섹터 3단계 포트폴리오 + 225건 백테스트 |
| [Investment Strategy Based on Bitcoin and Nasdaq Coupling/](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling) | 단일 전략 + 봇 | BTC-QQQ 6 regime 트레이딩 + 547줄 Python 봇 |

---

## AI-hedge-fund (NEW)

> 워런 버핏 + 찰리 멍거 + 캐시 우드가 같은 종목을 두고 토론한다면?

[virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) (GitHub 51,700+ stars, 9,000+ forks) 오픈소스 프로젝트의 **개념 분석 리포트**입니다. 14명의 전설적 투자자 페르소나(벤 그레이엄, 워런 버핏, 찰리 멍거, 빌 애크먼, 캐시 우드, 필립 피셔, 스탠리 드러켄밀러 등)와 6개 전문 분석 에이전트(Valuation, Technicals, Fundamentals, Sentiment, Risk Manager, Portfolio Manager)가 협업하는 **멀티 에이전트 헤지펀드 시뮬레이션** 프레임워크를 분석합니다.

핵심 내용:

* **다중 에이전트 협업 구조** — 각 에이전트가 독립적으로 BUY / SELL / HOLD 신호를 생성하고, Portfolio Manager가 최종 결정 통합
* **LLM 제공자 다양화** — OpenAI, Anthropic, Groq, DeepSeek, 로컬 Ollama 모두 지원
* **백테스팅 모듈** — 과거 데이터로 전략 성과 시뮬레이션
* **에이전트 추론 시각화** — `--show-reasoning` 플래그로 의사결정 과정 투명화
* **LangGraph 기반 오케스트레이션** — 복잡한 멀티 에이전트 상태 관리

페르소나 AI의 실제 성과 — *학술 검증*:

* GuruAgents 논문(arXiv:2510.01664)에서 Buffett 페르소나가 NASDAQ-100 백테스트(2023 Q4 ~ 2025 Q2)에서 **CAGR 42.2%**로 벤치마크 약 25%를 압도
* 다른 페르소나는 *varied* — 시장 regime에 의존적

→ [폴더 README](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/AI-hedge-fund/Readme.md) 참조

>  **본 프로젝트는 교육·연구 목적이며 실거래용이 아닙니다.** 가장 가치 있는 사용법은 *"내가 검토 중인 종목을 4-5명 페르소나에게 동시 분석시켜 충돌 지점을 찾는 것"* — Buffett은 valuation으로 반대, Wood는 innovation으로 찬성하는 토론이 단일 LLM 답보다 풍부한 판단 자료를 만듭니다.

---

## Awesome claude quant scripts

Claude를 활용해 만든 트레이딩 전략 스크립트 모음입니다. 4종의 전략과 1개의 Sample 템플릿, 그리고 *Cross-Lingual LLM Accuracy 학술 연구*가 포함되어 있습니다.

→ [폴더 README](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Readme.MD) 참조

수록 전략:

* AI supply chain bayesian analysis — AI 공급망 위험을 베이지안 추론으로 분석
* DAT quant strategy — DAT (Digital Asset Treasury) 기업 정량 전략
* Declining Stock Quant Script Using LLM — LLM 기반 하락주 분석 스크립트
* Long-Term Dividend Investing — 장기 배당 투자 스크립트
* **Dividend growth prompt** — 4 LLM × 3 언어 = 11개 결과물 검증 연구 + MSFT 사례 칼럼 (PDF v2)

핵심 발견 (Dividend growth prompt 연구):

* 11개 LLM 모두가 MSFT를 universal pick으로 추천했지만, 어떤 LLM도 OpenAI 의존도 45%, Calendar 2026 capex $190B, circular financing 같은 시점 의존적 위험을 인지하지 못함
* 같은 날 어닝 우위를 보인 GOOG는 0/11로 추천 누락 (프롬프트 criteria 하네스 효과)
* Cross-Lingual asymmetry 평균 Jaccard 0.297 — 동일 LLM도 언어별로 다른 결과 생성

---

## Luxury investment strategy

> 단일 종목 집중은 실패합니다. GLUX ETF 적립식이 답일 수 있습니다.

LVMH, Hermès, Kering, Richemont, Ferrari 등 13개 명품 기업·ETF의 2020-2026 데이터를 분석한 전략입니다. 225건의 백테스트로 적립식 / Buy-the-Dip / 중국 쇼크 역발상 3가지 전략을 비교합니다.

핵심 발견:

* 2020-2026 누적 복리: Ferrari +389%, Hermès +311%, Kering -42%
* 2024년 단년 수치: Kering -39.4%, Burberry -30%, LVMH -13%
* 단일 종목 집중 백테스트 모두 음수 수익률

본 전략에는 칼럼, 4종 CSV 데이터셋, 저/중/고 위험 3단계 포트폴리오가 포함됩니다.

---

## Investment Strategy Based on Bitcoin and Nasdaq Coupling

> Regime을 아는 자가 거래를 안다.

2020-2026년 BTC-QQQ 30일 rolling correlation을 26개 분기로 분석하고, 6 regime별 트레이딩 전략을 도출했습니다. Python 봇으로 실시간 신호 생성까지 end-to-end 구현되어 있습니다.

핵심 발견:

* 2026년 4월 기준 상관계수 -0.20 (10년 중 최저)
* Medium regime에서 Nasdaq이 BTC를 15-60분 선행
* 2026년 2월 -0.68 → +0.72로 2주 만의 swing 사례

본 전략에는 칼럼, 4종 CSV 데이터셋, 547줄 Python 트레이딩 봇이 포함됩니다.

---

## 본 폴더의 4가지 트랙 — 어떤 것부터 봐야 할까

| 관심 영역 | 추천 시작점 |
| --- | --- |
| **AI 멀티 에이전트 / 페르소나 투자** | AI-hedge-fund 분석 리포트 → ai-hedge-fund 오픈소스 직접 실험 |
| **LLM 프롬프트 퀀트 / 배당주** | Awesome claude quant scripts → Dividend growth prompt 칼럼 먼저 읽기 |
| **명품 섹터 / 적립식 ETF** | Luxury investment strategy 칼럼 + GLUX ETF 분석 |
| **크립토-주식 상관관계 / regime 트레이딩** | Bitcoin-Nasdaq Coupling 칼럼 + Python 봇 |

---

## 사용 시 권장 순서

1. **선행 학습** — 상단 박스의 *MSFT 사례 칼럼*과 *Cross-Lingual LLM 논문*을 먼저 읽고 LLM의 4가지 구조적 한계 인지
2. 본인의 관심 시장 확인 (AI 헤지펀드 / 주식 / 명품 / 크립토-주식 커플링)
3. 해당 폴더의 README와 칼럼 먼저 읽기
4. 스크립트 또는 봇 실행 전 "알려진 한계" 섹션 반드시 확인
5. CSV 데이터로 재현·검증
6. **Cross-LLM + 다국어 + 실시간 어닝으로 검증**
7. 페이퍼 트레이딩으로 검증 후 실거래 고려

---

## Disclaimer

각 전략은 연구·교육 목적입니다. 백테스트 결과는 이상적 시나리오 기반이며 실거래 수익률과 다릅니다. *AI-hedge-fund와 GuruAgents의 페르소나 AI 백테스트 결과(Buffett CAGR 42.2%) 등 학술/오픈소스 백테스트도 마찬가지로 시장 regime에 의존적이며 미래 수익을 보장하지 않습니다.*

자세한 내용은 [메인 README의 Disclaimer](https://github.com/gameworkerkim/vibe-investing/blob/main/README.md#disclaimer) 참조.
