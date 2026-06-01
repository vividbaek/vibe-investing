파일	내용

backtest_daily.csv	날짜별 가격/수익률/z-score/포지션/에쿼티

trades.csv	평균회귀 전략 트레이드 로그 (21건)

summary_metrics.csv	전략별 성과·통계 유의성·판정

leadlag_corr.csv	리드-래그 교차상관표

mu_hynix_charts.png	누적수익/z-score/에쿼티 차트

run_console_output.txt	콘솔 출력 로그

핵심 결과 요약
리드-래그: MU가 1일 선행할 때 상관 0.466 (p<0.0001) — 가장 강한 신호
공적분: beta=1.096, ADF p=0.027 (valid=O), 현재 z-score = −2.14 (하이닉스가 스프레드 기준 저평가 구간)
전략 평가: LeadLag_LongShort가 Sharpe 4.54 / t_HAC 6.62로 가장 우수, 네 전략 모두 "유의미" 판정

참고로 이 백테스트는 인샘플 결과이며, 스크립트 자체 경고대로 임계치는 워크포워드로 검증해야 하고 투자 권유가 아닙니다.
