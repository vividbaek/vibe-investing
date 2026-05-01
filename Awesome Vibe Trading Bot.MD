# Awesome Vibe Trading Bot - GitHub 오픈소스 코인 트레이딩 봇 분석 보고서 (AI 봇 확장판)

## *전통 트레이딩 봇 8종 + AI/LLM 기반 봇 6종 비교 평가*

---

## 개요

GitHub에는 수백 개의 코인 트레이딩 봇이 공개되어 있으며, 각 프로젝트는 지원 언어, 대상 거래소, 제공 전략, 커뮤니티 규모에서 뚜렷한 차이를 보입니다. 본 보고서는 다음 두 카테고리를 다룹니다.

**카테고리 A — 전통 트레이딩 봇 (8종)**: Freqtrade, Hummingbot, Superalgos, Jesse, Gekko (아카이브), PyCryptoBot, Ninjabot, Scuriolus, chrisleekr/binance-trading-bot

**카테고리 B — AI/LLM 기반 트레이딩 봇 (6종, 신규 추가)**: TradingAgents, OctoBot, qrak/LLM_trader, FinRL, Sibyl, LLM-TradeBot

각 봇은 *동일한 평가 기준* 으로 비교됩니다.

---

## 본 보고서의 한계 명시

평가 기준을 잡기 전에 짚어야 할 한계가 있습니다.

**첫째, "AI 기반"의 정의가 통일되지 않습니다.**
- 머신러닝 (Freqtrade의 FreqAI, FinRL의 RL)
- LLM 기반 (TradingAgents, qrak/LLM_trader, OctoBot의 ChatGPT 모드)
- Hybrid (Sibyl의 LSTM + LLM 통합)

본 보고서는 *세 카테고리 모두* 트레이딩으로 큰 손실을 볼 수 있습니다. 가상화폐의 변동성과 트레이딩 봇 전략, 가상화폐 거래소의 장애, 청산 문제 등이 있습니다.
또한 LLM 기반 트레이딩 봇의 경우 학습 오류 및 과도한 토큰 사용이 있을 수 있습니다. 

**둘째, GitHub stars 수치는 시점에 따라 변합니다.** 본 보고서의 stars 데이터는 2025-2026년 기준 검증된 수치이며, 일부는 추정치입니다. 정확한 현재 수치는 각 repo 페이지에서 직접 확인하시기 바랍니다.

**셋째, "성능"은 백테스트 결과이며 실거래 보장 아닙니다.** 모든 봇의 hit rate, Sharpe ratio 등은 *cherry-picked period* 가능성이 있습니다.

---

## 카테고리 A — 전통 트레이딩 봇 (8종)

### 비교 표

| 트레이딩 봇 | 언어 | GitHub Stars | 핵심 특징 | 주요 전략 |
|-------------|------|------------|---------|---------|
| Freqtrade | Python | 39,900+ | 백테스팅, Hyperopt 최적화, GUI 대시보드, Docker 지원, FreqAI ML 모듈 | 커스텀 전략, ML 전략, GPU 가속 백테스팅 |
| Hummingbot | Python/Cython | 8,000+ | 마켓 메이킹 특화, CEX/DEX 지원, 고빈도 트레이딩 | 마켓 메이킹, 크로스 익스체인지 아비트라지 |
| Superalgos | JavaScript | 5,000+ | 비주얼 전략 빌더, 소셜 트레이딩, 토큰 인센티브 | 데이터 마이닝, 백테스팅, 페이퍼 트레이딩 |
| Jesse | Python | 6,900+ | AI 트레이딩 에이전트, 간편한 구문, 플러그인 구조 | 다양한 내장 전략, 커스텀 ML 전략 |
| Gekko (아카이브) | Node.js | 10,000+ | 초창기 오픈소스 봇, 페이퍼 트레이딩 | 기술적 분석 전략, 백테스팅 |
| PyCryptoBot | Python | 2,400+ | 간단한 구조, 교육용 적합 | 트레일링 매매, 기술적 지표 |
| Ninjabot | Go | 1,200+ | 고성능, 바이낸스 특화, 경량화 | 페이퍼 트레이딩, 백테스팅 |
| Scuriolus | Rust | 신규 | 모듈형 아키텍처, 비동기 처리, 안전성 | StrictBuy, Trend Tunnel, AI 통합 계획 |
| chrisleekr/binance-trading-bot | Node.js | 한국어 지원 | 트레일링 매수/매도, MongoDB | 그리드 + 트레일링 |

### A-1. Freqtrade (Python)

**장점**

종합적인 전략 개발 환경: 백테스팅, 하이퍼파라미터 최적화(Hyperopt), 실시간 모니터링을 위한 GUI 대시보드, Docker 지원 등 완전한 생태계를 제공합니다.

최신 기술 통합: 2025년 버전에서는 GPU 가속 벡터화 백테스팅을 도입했으며, *FreqAI 모듈*을 통한 머신러닝 통합이 가능합니다. 시장 데이터에 ML 모델을 학습하고 실시간으로 재학습할 수 있습니다.

활발한 커뮤니티: 2026년 현재까지 적극적으로 유지보수되고 있으며, 방대한 문서와 전략 레포지토리가 존재합니다. GitHub stars 약 *39,900*개로 카테고리 최대 규모.

**단점**

학습 곡선: 풍부한 기능에도 불구하고 초보자가 전체 시스템을 이해하는 데 시간이 필요합니다.

암호화폐 전용: 주식이나 옵션 등 다른 자산 거래는 지원하지 않습니다.

FreqAI 한계: ML 통합은 강력하나 데이터 수집과 모델 학습 파이프라인 설정이 복잡합니다. 잘못 설정 시 *모델 misbehavior 또는 overfitting* 위험이 있습니다.

리소스 요구: GPU 가속 백테스팅과 같은 고급 기능을 활용하려면 적절한 하드웨어가 필요합니다.

### A-2. Hummingbot (Python/Cython)

**장점**

전문적인 마켓 메이킹: CEX와 DEX를 모두 지원하며, *유동성 공급 전략*에 특화되어 있습니다.

고성능 아키텍처: Cython으로 구현된 핵심 구성 요소 덕분에 고빈도 트레이딩 환경에서도 안정적인 성능을 제공합니다.

플러그인 시스템: 새로운 거래소 커넥터를 쉽게 추가할 수 있는 확장 가능한 아키텍처를 갖추고 있습니다.

2025년 업데이트: 유동성 마이닝 인센티브 통합, AWS Lambda를 통한 온체인 배포 지원 등 최신 기능이 추가되었습니다.

**단점**

복잡한 설정: 마켓 메이킹 전략의 특성상 설정이 복잡하고, 적절한 설정을 위해 깊은 이해가 필요합니다.

제한된 전략 유형: 마켓 메이킹과 아비트라지에 특화되어 있어, 추세 추종과 같은 다양한 전략을 테스트하기에는 적합하지 않을 수 있습니다.

대규모 자본 필요: 마켓 메이킹 전략은 일반적으로 의미 있는 수익을 내기 위해 상당한 자본을 필요로 합니다.

### A-3. Superalgos (JavaScript)

**장점**

비주얼 전략 빌더: 드래그 앤 드롭 방식의 노드 기반 인터페이스를 통해 프로그래밍 지식 없이도 복잡한 전략을 설계할 수 있습니다.

소셜 트레이딩 생태계: SA 토큰 인센티브 시스템을 통해 커뮤니티 기여를 장려하고, 전략 공유 문화가 활성화되어 있습니다.

종합 플랫폼: 데이터 마이닝, 백테스팅, 페이퍼 트레이딩, 실전 트레이딩을 하나의 플랫폼에서 모두 수행할 수 있습니다.

광범위한 문서: 1500페이지가 넘는 상세한 문서를 제공하여 학습을 지원합니다.

**단점**

높은 시스템 요구사항: Node.js 서버, MongoDB 등 의존성이 많아 설치와 운영이 상대적으로 무겁습니다. 저사양 환경에서는 minMemo 플래그 사용이 필요할 수 있습니다.

학습 곡선: 비주얼 인터페이스에도 불구하고, 전체 플랫폼을 이해하는 데 상당한 시간이 필요합니다.

커뮤니티 의존성: 플러그인 시스템이 GitHub 토큰을 통해 커뮤니티 기여에 의존하므로, 특정 기능의 유지보수가 커뮤니티 활동에 달려 있습니다.

### A-4. Jesse (Python)

**장점**

간편한 구문: Python 기반의 직관적 구문으로 전략 개발 진입 장벽이 낮습니다.

플러그인 구조: AI/ML 전략 통합이 가능합니다.

활발한 커뮤니티: GitHub stars 약 *6,900*개, 정기 업데이트.

**단점**

문서 부족: Freqtrade 대비 상세 문서가 부족합니다.

상용 기능: 일부 고급 기능은 유료 라이선스 필요.

### A-5. Gekko (Node.js, 아카이브)

**장점 (역사적)**

접근성: Node.js 기반으로 웹 개발자에게 친숙한 환경을 제공합니다.

다양한 전략: 수십 개의 기본 제공 전략과 커스텀 전략 개발이 가능합니다.

**단점 (결정적)**

**2020년 이후 유지보수 중단**: 가장 큰 한계로, 최신 시장 환경과 거래소 API 변경 사항을 반영하지 못합니다.

보안 취약성: 업데이트되지 않은 오래된 의존성 패키지로 인해 보안 위험이 존재합니다.

거래소 호환성 문제: 바이낸스, 비트파이넥스 등 주요 거래소의 API 변경으로 정상 작동하지 않을 가능성이 높습니다.

**권고**: *사용하지 마십시오*. 학습 자료로만 참조.

### A-6. PyCryptoBot (Python)

**장점**

교육적 가치: 간단한 구조로 알고리즘 트레이딩의 기본 개념을 학습하기에 적합합니다.

점진적 개발: 트레일링 매수/매도 같은 기본 전략부터 시작해 점차 고급 기능을 추가할 수 있습니다.

낮은 진입 장벽: Python 기반이며 소규모 코드베이스로, 초보자도 쉽게 분석하고 수정할 수 있습니다.

**단점**

제한된 기능: 전문적인 백테스팅, 최적화, 다양한 전략 등을 지원하지 않습니다.

소규모 커뮤니티: Stars 2,400여 개로, 문제 해결을 위한 리소스가 제한적입니다.

확장성 부족: 대규모 포트폴리오나 복잡한 전략을 구현하기에는 기술적 한계가 명확합니다.

### A-7. Ninjabot (Go)

**장점**

고성능: Go 언어로 작성되어 빠른 실행 속도와 효율적인 리소스 사용을 자랑합니다.

경량화: CLI 기반으로 최소한의 리소스로 고성능 트레이딩이 가능합니다.

명확한 결과 제공: 백테스팅에서 승률, 수익률, SQN 등 상세한 트레이딩 지표를 제공합니다.

**단점**

바이낸스 특화: 현재 바이낸스 거래소만 지원하므로, 다른 거래소를 이용하려면 별도의 커넥터를 개발해야 합니다.

전략 개발의 복잡성: Go 언어의 특성상 Python에 비해 전략 개발이 상대적으로 까다롭습니다.

제한된 커뮤니티: Stars 1,200개 미만으로, 참고할 수 있는 커뮤니티 전략과 문서가 부족합니다.

### A-8. Scuriolus (Rust)

**장점**

안전성과 성능: Rust의 메모리 안전성과 비동기 처리(Tokio)를 통해 높은 성능을 제공합니다.

모듈형 아키텍처: Market, Provider, Strategy 모듈이 분리되어 있어 확장성이 뛰어납니다.

임베디드 데이터베이스: SurrealDB를 통해 신뢰성 있는 데이터 지속성을 보장합니다.

AI 통합 계획: 향후 AI 기반 전략을 통합할 예정입니다.

**단점**

초기 개발 단계: 2025년 5월 첫 릴리스 이후 약 170회의 다운로드를 기록한 신규 프로젝트로, 프로덕션 환경에서 검증되지 않았습니다.

제한된 거래소 지원: 현재는 MEXC와 시뮬레이션 모드만 지원합니다.

높은 진입 장벽: Rust 언어의 특성상 Python이나 JavaScript에 비해 학습 곡선이 가파릅니다.

### A-9. chrisleekr/binance-trading-bot (Node.js, 한국어 지원)

**장점**

한국어 지원: 국내 사용자를 위한 완벽한 한글 문서화가 되어 있습니다.

트레일링 매수/매도 전략: 그리드 트레이딩과 트레일링 기법을 결합한 자동화된 전략을 구현할 수 있습니다.

MongoDB 기반: 지속적인 데이터베이스로 MongoDB를 사용하여 안정적인 데이터 관리를 지원합니다.

라즈베리파이 지원: 저사양 기기에서도 구동 가능합니다.

**단점**

바이낸스 전용: 다른 거래소는 지원하지 않습니다.

제한된 전략: 트레일링 매수/매도 전략만 내장되어 있어, 다른 전략을 구현하려면 직접 개발해야 합니다.

소규모 개인 프로젝트: 주의 사항에서도 밝히듯이 개인 테스트 목적의 프로젝트로, 전문적인 트레이딩 도구로는 부족할 수 있습니다.

---

## 카테고리 B — AI/LLM 기반 트레이딩 봇 (6종, 신규 추가)

### 비교 표

| 트레이딩 봇 | 언어 | GitHub Stars | 핵심 특징 | 주요 AI 방법론 |
|-------------|------|------------|---------|--------------|
| TradingAgents | Python | 매우 높음 | UCLA/MIT 학술 backed, 7개 LLM 역할 분담, arXiv 2412.20138 | 멀티에이전트 LLM (GPT-5.x/Gemini 3.x/Claude 4.x/Grok 4.x) |
| OctoBot | Python | 5,500+ | ChatGPT/Ollama 통합, 15+ 거래소, AI + Grid + DCA | LLM + 기술적 분석 hybrid |
| qrak/LLM_trader | Python | 신규/중간 | Vision AI 차트 분석, ChromaDB 벡터, RAG 엔진 | LLM + Vision + RAG (Gemini, OpenRouter, BlockRun.AI, LM Studio) |
| FinRL | Python | 14,900+ | AI4Finance Foundation, 12+ RL 알고리즘 | Deep Reinforcement Learning (DQN, DDPG, PPO, SAC) |
| Sibyl | Python | 신규 | LLM Oracle 어시스턴트, RAG, 커스텀 LSTM | LLM + LSTM + ARIMA hybrid |
| LLM-TradeBot | Python | 신규 | 8 LLM 제공자, 멀티에이전트 채팅룸, Web Dashboard | 멀티에이전트 LLM (GPT-4o/Claude/DeepSeek 등) |

### B-1. TradingAgents (TauricResearch)

**핵심 특징**

UCLA + MIT 연구진이 개발한 멀티에이전트 LLM 트레이딩 프레임워크. arXiv 2412.20138 논문 동반. 7개 역할 (Fundamental Analyst, Sentiment Analyst, News Analyst, Technical Analyst, Researcher, Trader, Risk Manager) 의 *LLM 에이전트가 토론*하여 매매 결정 도출.

지원 LLM: OpenAI GPT-5.x, Google Gemini 3.x, Anthropic Claude 4.x, xAI Grok 4.x, DeepSeek, Qwen, GLM, Ollama (로컬). LangGraph 기반.

**장점**

학술적 backing: arXiv 논문 + 7번 버전 업데이트 + ICLR 2026 후속 논문 (Trade in Minutes).

Bull/Bear debate 메커니즘: 단일 LLM의 편향을 *대립적 토론*으로 완화.

Cumulative Returns, Sharpe Ratio, MDD 모두 baseline 대비 개선 실증.

11개 LLM provider 지원 — vendor lock-in 회피.

Docker, structured output, checkpoint resume 등 production-grade 기능.

**단점**

크립토 주식 둘 다 가능하나 *주식 중심* — 크립토 특화 기능 부족.

비용 상당: analysis당 11 LLM call + 20+ tool call로 *$0.10+ 추정*.

3개월 backtest 한정 (2024년 6-11월) — *survivorship period* 위험.

저자 본인이 인정: *"highest SR exceeds expected empirical range"* — Sharpe Ratio 결과가 *too good to be true* 가능성.

저자 권고: *"research purposes only"* — 실거래 적용 비권장.

**적합 사용자**: LLM 기반 멀티에이전트 트레이딩을 *학술적 정확성*으로 학습하려는 사람.

### B-2. OctoBot (Drakkar-Software)

**핵심 특징**

오픈소스 크립토 트레이딩 봇 (2018년 출시). 2025년 *ChatGPT 트레이딩 모드* 추가로 LLM 통합. 로컬 LLM (Ollama) 또는 OpenAI API 양쪽 지원. Grid trading, DCA, 마켓 메이킹, Crypto basket (ETF형) 등 다양한 전략.

15+ 거래소 지원: Binance, Coinbase, MEXC, Hyperliquid 등.

**장점**

*전통 트레이딩 봇 + AI* hybrid의 모범 사례. AI를 안 쓰고도 grid/DCA로 작동.

활발한 커뮤니티: GitHub stars 약 *5,500*+ , 2018년 출시 이후 정기 업데이트.

ChatGPT 트레이딩 모드: LLM에게 시장 컨텍스트를 주고 *opinion*을 받아 매매. 기존 트레이딩 봇 사용자가 *점진적으로* AI 도입 가능.

Crypto basket 기능: ETF처럼 *다수 코인에 분산 투자* 자동화.

라즈베리파이/소형 기기 지원.

**단점**

LLM 사용은 *추가 옵션*이며, 핵심은 여전히 전통 전략.

상용 cloud 서비스 (octobot.cloud) 존재 — 일부 고급 기능 유료.

마켓 메이킹은 별도 *상용 라이선스* 필요.

ChatGPT 모드의 *백테스트 검증 부족* — 라이브 결과 공개 적음.

**적합 사용자**: 전통 트레이딩 봇 사용자가 *AI 점진 도입*을 원할 때.

### B-3. qrak/LLM_trader (qrak)

**핵심 특징**

*가장 순수한 LLM 기반 크립토 트레이더*. Vision AI로 차트 직접 분석. ChromaDB 벡터 스토어로 *과거 거래 기억*. RAG 엔진으로 CryptoCompare 뉴스 + DefiLlama 펀더멘털 통합.

지원 LLM: Google Gemini, OpenRouter, BlockRun.AI, LM Studio (로컬). Multi-provider with fallback.

지원 거래소: Binance, KuCoin, Gate.io, MEXC, Hyperliquid (ccxt 통합).

**장점**

Vision AI 차트 분석: *차트 이미지를 LLM이 직접 읽어* 패턴 인식. 인간 트레이더처럼 차트 해석.

Adaptive Memory: *과거 거래 회상 + 자동 reflection loop* 로 학습.

Live Dashboard: semanticsignal.qrak.org 에서 실시간 *neural trading brain* 가시화.

X402 micropayments (BlockRun.AI): pay-per-request AI 액세스로 *비용 효율적*.

asyncio-first: 비동기 처리로 고성능.

**단점**

*신규 프로젝트*: 공식 stars 데이터 부족. 검증된 트랙 레코드 짧음.

LLM 비용: Vision AI는 *텍스트 LLM 대비 비용 높음*.

복잡성: Vector DB + RAG + Vision AI 통합으로 *설정 복잡*.

5개 거래소 지원하나 한국 거래소 (Upbit, Bithumb) 직접 지원 없음.

**적합 사용자**: LLM의 *vision 능력*을 활용한 차트 분석을 실험하려는 사람.

### B-4. FinRL (AI4Finance Foundation)

**핵심 특징**

Deep Reinforcement Learning 트레이딩의 *오픈소스 표준*. AI4Finance Foundation (FinGPT의 모기관) 운영. 12+ RL 알고리즘 (DQN, DDPG, PPO, SAC) + Stable-Baselines3, RLlib, ElegantRL 통합.

크립토 (FinRL_Crypto), 주식 양쪽 지원. 2017년 시작, 2026년 현재 *14,900+ stars, 3,284 forks*.

**장점**

학술적 신뢰성: AI4Finance Foundation, NYU/Columbia 연구진. 다수 학술 논문 backed.

12+ RL 알고리즘: 다양한 RL 접근 동시 실험 가능.

크립토 특화 모듈 (FinRL_Crypto): 크립토 시장 환경 별도 지원.

활발한 커뮤니티: 2,805 forks (FinGPT 기준).

MIT 라이선스: 자유로운 사용/수정.

**단점**

*RL은 LLM이 아닙니다*: 본 보고서의 다른 AI 봇들과 *접근 방식이 다름*. 학습 곡선 가파름.

*프롬프트가 아닌 reward function 설계*: 일반 사용자에게 진입 장벽.

학습 시간 길음: RL 모델 학습은 *수일~수주* 소요 가능.

오버피팅 위험: *backtest에서 작동하나 실거래에서 실패*하는 RL 모델의 흔한 문제.

거래소 직접 통합 없음: FinRL은 *환경 제공*에 집중. 실거래 연결은 별도 구현.

**적합 사용자**: Deep RL 연구자 또는 *학술 backed RL 실험* 원하는 사람.

### B-5. Sibyl (nMaroulis)

**핵심 특징**

LLM + 전통 ML hybrid. *Oracle* 이라는 LLM 어시스턴트가 시장 분석/뉴스 요약/전략 제안 통합. *Chronos* 모듈은 커스텀 TensorFlow Bi-Directional LSTM, GTU, ARIMA 모델로 가격 예측 (non-LLM).

RAG 엔진: 수천 개 크립토 publication, 책, 논문 임베딩. ChromaDB 사용. Hybrid similarity (cosine + BM25 + FAISS).

**장점**

*LLM + 전통 ML* 통합: 한 가지 접근에 의존하지 않음.

Context-aware: UI 위치에 따라 LLM이 *적응적 도움* 제공.

Local LLM 옵션: 비용 + privacy 측면 유리.

RAG 기반 educational 콘텐츠: 크립토 *학습 도구*로도 활용 가능.

Senator stock portfolio insights, U.S. STOCK Act 통합 — *대안적 데이터 소스*.

**단점**

*신규 프로젝트*: 공식 stars 데이터 부족.

복잡성: LSTM + LLM + RAG + 거래소 API 통합으로 *설정 복잡*.

ChromaDB embeddings 별도 다운로드: 초기 설정 부담.

LSTM 모델의 *학습 데이터 의존성*: 7개 features (BTC, S&P500, Gold, USD, Oil, VIX, 금리) — features engineering 한정.

거래소 통합 적음: 프로토타입 단계.

**적합 사용자**: LLM과 전통 ML *통합 architecture* 를 실험하려는 사람.

### B-6. LLM-TradeBot (EthanAlgoX)

**핵심 특징**

*완성도 높은* 멀티에이전트 LLM 트레이딩 시스템. 8개 LLM provider 지원 (GPT-4o, Claude, DeepSeek 등). Agent Chatroom 으로 *에이전트 간 대화* 가시화. Web Dashboard 내장.

테스트 모드 (가상 자본 $1,000) 지원. Multi-Account Architecture로 다중 거래소 계정 관리.

**장점**

*프로덕션 지향* 설계: Web Dashboard, ML probability display, robust scrollbars 등 UX 정성.

테스트 모드 안전: 100% 가상 자본으로 *위험 없는 학습* 가능.

8 LLM 제공자: 다양한 모델 비교 가능.

Multi-Account: 여러 거래소 동시 운영.

Docker compose 지원: 1-click 시작.

CLI mode: headless 서버 운영 가능.

**단점**

*신규 프로젝트*: 검증된 트랙 레코드 짧음. 공식 stars 적음.

*Perception First* 접근: *"IF we should trade"* 판단 후 *"HOW to trade"* — 흥미로우나 *backtest 검증 부족*.

LLM 비용 누적: 다중 에이전트 사용 시 *비용 빠르게 증가*.

문서 영어 + 일부 중국어 혼재.

거래소 통합 명세 불명확.

**적합 사용자**: *멀티에이전트 LLM* 을 실전에 가까운 환경에서 실험하려는 사람.

---

## 통합 평가 매트릭스

```
                    학술 신뢰성 ↑
                       |
   FinRL *             |    * TradingAgents
   (DRL standard)      |       (UCLA/MIT)
                       |
   ----------------------------------- 인지도 →
   Freqtrade *         |
   (FreqAI ML)         |    * Hummingbot
                       |
   OctoBot *           |    * Jesse
   (LLM hybrid)        |    
                       |
   qrak/LLM_trader *   |    * LLM-TradeBot
   Sibyl *             |    
                       |
                       |    * Gekko (deprecated)
                       |
                    학술 신뢰성 ↓
```

---

## 용도별 추천 가이드 (확장판)

### 초보자 및 학습 목적

- **PyCryptoBot**: 간단한 구조로 알고리즘 트레이딩 기본 학습
- **Superalgos**: 비주얼 전략 빌더로 코딩 지식 없이 설계
- **OctoBot**: AI 기능 점진적 도입 가능 (선택형)
- **LLM-TradeBot**: 100% 안전한 가상 자본 모드로 LLM 트레이딩 학습

### 전문 트레이더 및 전략 개발

- **Freqtrade**: 종합적인 백테스팅, 최적화, 실전 트레이딩 환경. 활발한 커뮤니티
- **Jesse**: AI 기반 트레이딩 에이전트 + 간편 구문. ML 전략 빠른 개발
- **OctoBot**: 전통 + AI hybrid

### 고빈도 / 마켓 메이킹 전략

- **Hummingbot**: CEX/DEX 마켓 메이킹과 아비트라지에 특화

### 성능 중시

- **Ninjabot**: Go 언어의 고성능, 경량화, CLI 기반
- **Scuriolus**: Rust의 안전성과 성능. 최신 아키텍처

### 한국어 사용자

- **chrisleekr/binance-trading-bot**: 완벽한 한글 문서화 + 트레일링 매매 전략. 국내 바이낸스 사용자에게 적합

### LLM 기반 멀티에이전트 트레이딩 (신규)

- **TradingAgents**: 학술적 정확성 + 7개 역할 LLM 토론. UCLA/MIT backed
- **LLM-TradeBot**: 멀티에이전트 + Web Dashboard. 프로덕션 지향
- **qrak/LLM_trader**: Vision AI 차트 분석. *가장 순수한 LLM 기반*

### Deep Reinforcement Learning (신규)

- **FinRL**: DRL 트레이딩 표준. 학술 backed. 12+ RL 알고리즘

### LLM + 전통 ML Hybrid (신규)

- **Sibyl**: LSTM + LLM + RAG 통합 architecture
- **OctoBot**: 전통 전략 + ChatGPT 모드 옵션

---

## AI/LLM 봇 사용 시 추가 위험 신호 (Red Flags)

전통 봇과 달리 AI/LLM 봇에는 다음 *추가 위험* 이 있습니다.

### Red Flag 1: Hallucination 위험

LLM은 *환각*을 만들 수 있습니다. 매매 결정에서 *존재하지 않는 패턴* 을 보고하거나 *잘못된 가격 데이터*를 사용할 수 있습니다.

**완화**: 다른 LLM으로 교차 검증. 결정 후 사람이 검토. 결정 reasoning trail 저장.

### Red Flag 2: 비용 폭증

LLM API 호출은 *분당/초당 비용 누적*. 멀티에이전트 봇은 *분당 $1+ 비용* 가능. 24/7 운영 시 *월 $1,000+ 비용*.

**완화**: 로컬 LLM (Ollama) 사용 또는 호출 빈도 제한.

### Red Flag 3: 모델 deprecation

LLM은 *6-12개월마다 새 버전*. 기존 모델이 deprecated 되면 *전체 시스템 재학습* 필요.

**완화**: 다중 provider 지원하는 봇 선택. 단일 vendor lock-in 회피.

### Red Flag 4: Backtest 어려움

LLM 결정은 *비결정적* — random seed/temperature 제어가 어려움. *동일 입력 → 다른 출력* 가능.

**완화**: temperature=0 고정. 다수 실행 후 *평균* 사용.

### Red Flag 5: Look-ahead bias

LLM 학습 데이터에 *미래 정보* 포함 가능. 예: GPT-4 학습 데이터가 2023년이면, *2022년 backtest는 무효*.

**완화**: LLM 학습 cutoff 이후 데이터로만 backtest. *Walk-forward validation* 필수.

### Red Flag 6: Regulation 위험

AI 자동매매는 미국 SEC, 한국 금감원, EU MiCA 모두 *규제 적용 가능*. 본인 자산은 가능하나 *타인 자금 운용은 라이선스 필요*.

**완화**: 본인 자산만 운용. 규제 명확화 까지 보수적 접근.

---

## 한국 거주자 관점

### 한국 거주자가 사용 시 고려사항

**기술적 측면**
- 대부분 봇이 *바이낸스/Coinbase 등 글로벌 거래소* 중심
- *Upbit, Bithumb* 직접 지원하는 봇 적음
- chrisleekr/binance-trading-bot 만 한국어 문서

**법적 측면**
- *외환거래법*: 연 $50,000 초과 송금 시 신고
- *양도소득세 22%*: 가상자산 매매 차익 과세 (2025년 시행)
- *가상자산이용자보호법* (2024년 7월 시행)
- *AI 자동매매가 영업으로 간주 시* 투자자문업 등록 필요

**문화적 측면**
- 한국 학자가 만든 LLM 트레이딩 봇 거의 없음
- 한국 trading firm (NHN, 카카오, 토스 등) 의 *오픈소스 기여 거의 없음*

### 한국에서 *비어 있는 카테고리*

다음 영역은 *한국에서 진입자가 거의 없습니다*.

1. *한국어 LLM 트레이딩 봇 큐레이션*
2. *Upbit/Bithumb LLM 통합 트레이딩*
3. *KOSPI/KOSDAQ 멀티에이전트 LLM 트레이딩*
4. *한국 거주자 외환거래법 준수 자동매매 도구*
5. *한국 시장 특화 RAG 엔진* (DART 공시, 한국은행 ECOS 등)

향후 *한국인 개발자/연구자 niche* 입니다.

---

## 결론

오픈소스 코인 트레이딩 봇 선택 시 가장 중요한 기준은 *활발한 유지보수 상태와 본인의 트레이딩 스타일과의 일치 여부* 입니다.

**전통 봇 권장 순위**

1. **Freqtrade** — 카테고리 최대 stars (39,900+), FreqAI ML 통합, 활발한 커뮤니티
2. **Hummingbot** — 마켓 메이킹/아비트라지 표준
3. **Jesse** — AI/ML 통합 + 간편 구문
4. **chrisleekr/binance-trading-bot** — 한국 거주자 최적

**AI/LLM 봇 권장 순위 (신규)**

1. **TradingAgents** — 학술 backed 멀티에이전트 LLM. UCLA/MIT
2. **OctoBot** — 전통 + AI hybrid. 점진적 AI 도입에 최적
3. **FinRL** — DRL 표준. AI4Finance Foundation
4. **qrak/LLM_trader** — Vision AI 차트 분석. 가장 순수 LLM 기반
5. **LLM-TradeBot** — 프로덕션 지향 멀티에이전트 + Web Dashboard
6. **Sibyl** — LLM + LSTM + RAG hybrid

**피해야 할 봇**

- **Gekko** — 2020년 이후 유지보수 중단. 보안 취약.

모든 봇은 실제 자금을 투입하기 전에 반드시 *페이퍼 트레이딩으로 충분히 테스트* 하고, 각 프로젝트의 경고 사항을 숙지하시기 바랍니다.

특히 *AI/LLM 기반 봇*은 추가로:
- LLM hallucination 위험
- 비용 누적 (월 $1,000+ 가능)
- 모델 deprecation 위험
- Backtest 어려움 (비결정적 결정)
- Look-ahead bias 가능성

이 5가지 위험을 사전에 인지하고 *본인 자산의 5-10% 이내* 로 시작할 것을 강력 권장합니다.

---

## References

### 검증된 GitHub Repos (전통)

- Freqtrade: github.com/freqtrade/freqtrade
- Hummingbot: github.com/hummingbot/hummingbot
- Superalgos: github.com/Superalgos/Superalgos
- Jesse: github.com/jesse-ai/jesse
- Gekko (아카이브): github.com/askmike/gekko
- PyCryptoBot: github.com/whittlem/pycryptobot
- Ninjabot: github.com/rodrigo-brito/ninjabot
- Scuriolus: github.com/0xOlias/scuriolus
- chrisleekr/binance-trading-bot: github.com/chrisleekr/binance-trading-bot

### 검증된 GitHub Repos (AI/LLM 기반, 신규)

- TradingAgents: github.com/TauricResearch/TradingAgents (arXiv 2412.20138)
- OctoBot: github.com/Drakkar-Software/OctoBot
- qrak/LLM_trader: github.com/qrak/LLM_trader
- FinRL: github.com/AI4Finance-Foundation/FinRL
- Sibyl: github.com/nMaroulis/sibyl
- LLM-TradeBot: github.com/EthanAlgoX/LLM-TradeBot

### 시리즈 연계

- vibe-investing 시리즈: github.com/gameworkerkim/vibe-investing
- SSRN 6632838 — The 72-Hour Shock
- Awesome Vibe Invest — Crypto & DeFi Edition
- Awesome AI Quant Prompt GitHub Repos Evaluation

---

## Disclaimer

본 보고서는 **연구·교육 목적**입니다.

- 본 보고서는 *투자 권유가 아닙니다*
- 각 repo 의 stars/forks 수치는 *시점에 따라 변동*
- *"신뢰성"* 평가는 일반적 기준이며, 본인 use case 에 따라 다를 수 있음
- 모든 LLM/AI 도구는 *backtest 결과가 실거래 수익을 보장하지 않음*
- 한국 거주자: *외환거래법*, *양도소득세 22%*, *가상자산이용자보호법* 별도 확인 필요
- AI/LLM 봇 사용 시 *hallucination*, *비용 누적*, *backtest 어려움*, *look-ahead bias*, *regulation 위험* 사전 인지
- 본 보고서를 기반으로 한 투자 결정의 책임은 본인에게 있음
- *unlicensed financial advice*: 한국에서 AI 자동매매를 *영업*으로 간주하면 투자자문업 등록 필요
- LLM은 학습 오류가 있을 수 있으며 과도한 토큰 사용으로 비용 통제에 실패할 수 있음.

> *Past performance does not guarantee future results.*

---

## 작성 정보

**작성일**: 2026년 5월 1일
**저자**: 김호광 (Dennis Kim / HoKwang Kim) — Independent Researcher · Cyworld CEO Betalabs Inc. CEO
**시리즈**: vibe-investing — Investment Idea Column
**ORCID**: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
**GitHub**: [vibe-investing](https://github.com/gameworkerkim/vibe-investing)
