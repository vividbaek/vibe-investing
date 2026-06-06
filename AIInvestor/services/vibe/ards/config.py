# -*- coding: utf-8 -*-
"""
ARDS-X Regime Classifier — Configuration
=========================================
ARDS (Adaptive Recession-Defensive Strategy) 의 확장 모듈.

목적: 미국 빅테크 + AI/인프라 복합체와 S&P500 / 나스닥100 이 지금
      (1) 조정(Correction), (2) 단기 과매도(Oversold), (3) 하락/분배(Downtrend),
      (4) 자산 리밸런싱(침체, Recession-Rebalance) 중 어느 국면인지 분류한다.

ARDS 원본이 "LLM 프롬프트 + synthetic 백테스트" 였다면, ARDS-X 는 동일한
5-Factor Recession Composite 를 **실데이터(FRED 무료 CSV + yfinance)** 로
계산하고, 여기에 가격구조(드로다운/추세/과매도) 축을 더해 2-축 레짐 맵을 만든다.

저자: 김호광 (Dennis Kim / HoKwang Kim) · Betalabs Inc. · MIT License
"""

# ---------------------------------------------------------------------------
# 1) 분석 유니버스
# ---------------------------------------------------------------------------

# 지수 (분류의 주 대상)
INDICES = {
    "^GSPC": "S&P 500",
    "^NDX":  "Nasdaq-100",
}

# 미국 빅테크 + AI / 인프라 복합체 (질문의 핵심 대상)
#   - Big Tech (M7 핵심)
#   - AI 반도체/네트워킹
#   - AI 인프라 (전력·냉각·데이터센터·네트워크)
COMPLEX = {
    # --- Big Tech / Mega-cap ---
    "AAPL":  ("Apple",        "bigtech"),
    "MSFT":  ("Microsoft",    "bigtech"),
    "GOOGL": ("Alphabet",     "bigtech"),
    "AMZN":  ("Amazon",       "bigtech"),
    "META":  ("Meta",         "bigtech"),
    "NVDA":  ("NVIDIA",       "ai_semi"),
    "TSLA":  ("Tesla",        "bigtech"),
    # --- AI 반도체 / 네트워킹 ---
    "AVGO":  ("Broadcom",     "ai_semi"),
    "AMD":   ("AMD",          "ai_semi"),
    "TSM":   ("TSMC",         "ai_semi"),
    "MU":    ("Micron",       "ai_semi"),
    "ASML":  ("ASML",         "ai_semi"),
    # --- AI 인프라 (전력·냉각·데이터센터) ---
    "VRT":   ("Vertiv",       "ai_infra"),
    "SMCI":  ("Super Micro",  "ai_infra"),
    "ANET":  ("Arista",       "ai_infra"),
    "DELL":  ("Dell",         "ai_infra"),
    "ORCL":  ("Oracle",       "ai_infra"),
    "CEG":   ("Constellation","ai_infra"),
}

# 섹터 그룹 한글 라벨
GROUP_KR = {
    "bigtech":  "빅테크",
    "ai_semi":  "AI 반도체",
    "ai_infra": "AI 인프라",
}

# ---------------------------------------------------------------------------
# 2) FRED 무료 CSV 시리즈 (API 키 불필요)
#    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>
# ---------------------------------------------------------------------------
FRED_SERIES = {
    "T10Y3M":        "10Y-3M 스프레드 (NY Fed 표준)",
    "T10Y2Y":        "10Y-2Y 스프레드 (보조)",
    "UNRATE":        "실업률 (Sahm Rule 입력)",
    "BAMLH0A0HYM2":  "HY OAS (하이일드 신용 스프레드)",
    "NFCI":          "Chicago Fed 금융상황지수",
    "ICSA":          "주간 신규 실업수당 청구 (LEI 프록시)",
    "PERMIT":        "주택 착공허가 (LEI 프록시)",
}

# 거시 시장 프록시 (yfinance) — FRED 가 막혀도 동작하도록 하는 폴백 소스.
#   ^TNX=10Y, ^IRX=3M, ^FVX=5Y 국채금리 / HYG·LQD·IEF 로 신용 스트레스
#   CPER·GLD·XLI·SPY 로 ISM(산업 펄스) 프록시
MACRO_MARKET = ["^TNX", "^IRX", "^FVX", "HYG", "LQD", "IEF", "CPER", "GLD", "XLI", "SPY"]

# ---------------------------------------------------------------------------
# 3) 5-Factor Recession Composite 가중치 (ARDS 원본과 동일)
# ---------------------------------------------------------------------------
RECESSION_WEIGHTS = {
    "A_yield_curve":  0.30,   # 수익률 곡선 역전
    "B_sahm":         0.25,   # Sahm Rule
    "C_ism_proxy":    0.15,   # ISM 제조업 (시장 프록시)
    "D_lei_proxy":    0.15,   # 선행지수 (FRED 프록시)
    "E_credit":       0.15,   # HY OAS + NFCI
}

# ---------------------------------------------------------------------------
# 4) 거시 레짐 4-Phase 경계 (Composite 0~100)
# ---------------------------------------------------------------------------
MACRO_PHASES = [
    # (상한, 코드, 한글)
    (25,  "EXPANSION",         "확장기"),
    (50,  "LATE_CYCLE",        "후기 사이클"),
    (70,  "RECESSION_WARNING", "침체 경고"),
    (101, "RECESSION",         "침체"),
]

# ---------------------------------------------------------------------------
# 5) 가격 구조 임계값 (조정/하락 분류용)
# ---------------------------------------------------------------------------
TECH = {
    # 드로다운(52주 고점 대비) 버킷 경계, %
    "dd_correction":   5.0,    # -5% 이상 → 조정 시작
    "dd_deep":         12.0,   # -12% 이상 → 깊은 조정/하락 의심
    "dd_bear":         20.0,   # -20% 이상 → 기술적 약세장

    # 과매도 지표
    "rsi_oversold":    32.0,   # RSI(14) 과매도
    "rsi_deep_os":     25.0,   # 극단 과매도
    "bb_oversold":     0.05,   # Bollinger %B 하단
    "atr_stretch":     2.5,    # 20일선 아래로 ATR 몇 배까지 이탈했나

    # 추세 무결성
    "breadth_weak":    40.0,   # 200일선 위 종목 비중(%) < 40 → 추세 약화
    "breadth_strong":  60.0,   # > 60 → 추세 양호
}

# ---------------------------------------------------------------------------
# 6) 분류 임계값 (거시 축 vs 가격 축 결합)
# ---------------------------------------------------------------------------
DECISION = {
    "macro_elevated":  45.0,   # 이 이상이면 거시 경계 모드
    "macro_recession": 55.0,   # 이 이상 + 가격 약세 → 침체 리밸런싱
}

# ---------------------------------------------------------------------------
# 7) Rate Stress 서브컴포지트 (금리/인플레 축, v1.1 신규)
#    "침체형 하락 vs 금리형 하락" 을 구분하기 위한 축.
#    침체 Composite 가 낮은데도 주가가 빠지는 '금리 쇼크' 를 잡아낸다.
#    → 하락유형 라벨(침체형/금리형/밸류형) 산출 + ARDS Tier2 TLT/IEF 조건부 게이팅.
# ---------------------------------------------------------------------------
RATE_WEIGHTS = {
    "R1_long_yield_vel":  0.35,   # 10Y 금리 20일 변화 (bp)
    "R2_rate_path":       0.25,   # 2Y(또는 5Y) 금리 20일 변화 — 정책경로 재가격
    "R3_breakeven":       0.20,   # 5Y 기대인플레(브레이크이븐) 20일 변화
    "R4_bond_vol":        0.20,   # MOVE 지수(또는 10Y 실현변동성) 수준
}

RATE = {
    "yield_vel_bp_hi":   60.0,    # 20일 +60bp → 100점 (금리 급등)
    "path_vel_bp_hi":    50.0,    # 2Y/5Y 20일 +50bp → 100점
    "bei_vel_bp_hi":     30.0,    # 브레이크이븐 20일 +30bp → 100점 (인플레 재가속)
    "stress_high":       55.0,    # 이 이상이면 '금리형' 하락 후보
    "label_min_stress":  28.0,    # 가격 스트레스가 이 이상일 때만 하락유형 라벨 부여
}

# 거시 시장(금리) 프록시 추가 — FRED 가 막혀도 yfinance 로 동작
RATE_MARKET = ["^MOVE"]          # 채권 변동성 (실패 시 ^TNX 실현변동성으로 폴백)
RATE_FRED = {
    "DGS2":   "2년 국채 금리 (정책경로)",
    "T5YIE":  "5Y 기대인플레 (브레이크이븐)",
}

# ---------------------------------------------------------------------------
# 8) 히스테리시스 (레짐 핑퐁/휩쏘 방지, v1.1 신규)
#    진입/이탈 임계값 분리(밴드) + N일 확인 후에만 공식 레짐 전환.
# ---------------------------------------------------------------------------
HYSTERESIS = {
    "confirm_days":      2,       # 새 raw 레짐이 N거래일 연속 유지돼야 공식 전환
    # 과매도 진입/이탈 밴드 (RSI)
    "rsi_enter":         30.0,    # 과매도 진입은 엄격
    "rsi_exit":          38.0,    # 이탈은 느슨 → 30~38 핑퐁 방지
    # 드로다운 진입/이탈 밴드 (%, 양수 절댓값)
    "dd_corr_enter":     5.0,
    "dd_corr_exit":      3.5,
    "dd_deep_enter":     12.0,
    "dd_deep_exit":      10.0,
    # 거시 침체 진입/이탈 밴드
    "macro_rec_enter":   55.0,
    "macro_rec_exit":    50.0,
}

# 히스테리시스 상태 저장 파일 (재실행 간 레짐 기억)
STATE_JSON = "data/regime_state.json"

# 출력 파일 경로 (대시보드가 읽음)
OUTPUT_JSON = "../dashboard/data/latest.json"

# 가격 데이터 룩백
LOOKBACK_DAYS = 420   # 약 14개월 (200DMA, 52주 고점, 6M 모멘텀 계산용)
