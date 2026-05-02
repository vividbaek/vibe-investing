# 01. Trading Strategy

vibe-investing 레포의 트레이딩 전략 인덱스입니다.

→ [메인 README로 돌아가기](../README.md)

---

## 구성

이 폴더는 세 가지 카테고리의 트레이딩 전략을 담고 있습니다.

| 폴더 | 종류 | 설명 |
|---|---|---|
| [Awesome claude quant scripts/](Awesome%20claude%20quant%20scripts/) | 스크립트 모음 | Claude 기반 4종 트레이딩 전략 + Sample 템플릿 |
| [Luxury investment strategy/](Luxury%20investment%20strategy/) | 단일 전략 + 칼럼 | 명품 섹터 3단계 포트폴리오 + 225건 백테스트 |
| [Investment Strategy Based on Bitcoin and Nasdaq Coupling/](Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling/) | 단일 전략 + 봇 | BTC-QQQ 6 regime 트레이딩 + 547줄 Python 봇 |

---

## Awesome claude quant scripts

Claude를 활용해 만든 트레이딩 전략 스크립트 모음입니다. 4종의 전략과 1개의 Sample 템플릿이 포함되어 있습니다.

→ [폴더 README](Awesome%20claude%20quant%20scripts/README.md) 참조

수록 전략:
- AI supply chain bayesian analysis — AI 공급망 위험을 베이지안 추론으로 분석
- DAT quant strategy — DAT (Digital Asset Treasury) 기업 정량 전략
- Declining Stock Quant Script Using LLM — LLM 기반 하락주 분석 스크립트
- Long-Term Dividend Investing — 장기 배당 투자 스크립트

---

## Luxury investment strategy

> 단일 종목 집중은 실패합니다. GLUX ETF 적립식이 답일 수 있습니다.

LVMH, Hermès, Kering, Richemont, Ferrari 등 13개 명품 기업·ETF의 2020-2026 데이터를 분석한 전략입니다. 225건의 백테스트로 적립식 / Buy-the-Dip / 중국 쇼크 역발상 3가지 전략을 비교합니다.

핵심 발견:
- 2020-2026 누적 복리: Ferrari +389%, Hermès +311%, Kering -42%
- 2024년 단년 수치: Kering -39.4%, Burberry -30%, LVMH -13%
- 단일 종목 집중 백테스트 모두 음수 수익률

본 전략에는 칼럼, 4종 CSV 데이터셋, 저/중/고 위험 3단계 포트폴리오가 포함됩니다.

---

## Investment Strategy Based on Bitcoin and Nasdaq Coupling

> Regime을 아는 자가 거래를 안다.

2020-2026년 BTC-QQQ 30일 rolling correlation을 26개 분기로 분석하고, 6 regime별 트레이딩 전략을 도출했습니다. Python 봇으로 실시간 신호 생성까지 end-to-end 구현되어 있습니다.

핵심 발견:
- 2026년 4월 기준 상관계수 -0.20 (10년 중 최저)
- Medium regime에서 Nasdaq이 BTC를 15-60분 선행
- 2026년 2월 -0.68 → +0.72로 2주 만의 swing 사례

본 전략에는 칼럼, 4종 CSV 데이터셋, 547줄 Python 트레이딩 봇이 포함됩니다.

---

## 사용 시 권장 순서

1. 본인의 관심 시장 확인 (주식 / 명품 / 크립토-주식 커플링)
2. 해당 폴더의 README와 칼럼 먼저 읽기
3. 스크립트 또는 봇 실행 전 "알려진 한계" 섹션 반드시 확인
4. CSV 데이터로 재현·검증
5. 페이퍼 트레이딩으로 검증 후 실거래 고려

---

## Disclaimer

각 전략은 연구·교육 목적입니다. 백테스트 결과는 이상적 시나리오 기반이며 실거래 수익률과 다릅니다. 자세한 내용은 [메인 README의 Disclaimer](../README.md#disclaimer) 참조.
