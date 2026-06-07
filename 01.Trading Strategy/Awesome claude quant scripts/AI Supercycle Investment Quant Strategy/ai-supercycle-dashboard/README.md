# AI Supercycle Investment Quant Strategy Dashboard

> **인공지능 슈퍼 사이클 투자 퀀트 대시보드**  
> Node.js + TypeScript 기반 웹 애플리케이션  
> Claude / DeepSeek LLM 분석 통합

Based on [vibe-investing](https://github.com/gameworkerkim/vibe-investing) by Dennis Kim (김호광).

---

## Features

- **4-Layer AI Value Chain Model** — Foundation (반도체/장비) → Infrastructure (하이퍼스케일러) → Enablers (전력/냉각/네트워크) → Application (기업 AI SW)
- **Real-time Quant Scoring** — 100점 만점 (AI Exposure 35% + Capital Efficiency 30% + Valuation 20% + Momentum 15%)
- **Korean Semiconductor Correlation** — 삼성전자(005930.KS), SK하이닉스(000660.KS), 마이크론(MU) 포함 상관관계 + 리드-래그 분석
- **Price Determination Model** — DCF + Technical + Correlation-Adjusted 3중 가격 타겟
- **4 Investment Scenarios** — Conservative(보수) / Moderate(중도) / Aggressive(공격) / Destructive(파괴)  
- **Backtesting Engine** — 시나리오별 Buy/Sell/Hold/Averaging Down 전략 백테스트
- **LLM Analysis** — Claude (Anthropic) + DeepSeek API 통합 (API 키 없으면 Rule-Based 자동 폴백)
- **HBM/DRAM Cycle Detection** — Expansion/Peak/Contraction/Trough 자동 판별

---

## Quick Start

```bash
cd ai-supercycle-dashboard
npm install
npm run dev
```

Open http://localhost:3000

### LLM 설정 (선택)

API 키 없이도 Rule-Based 엔진으로 모든 기능 사용 가능.  
API 키를 입력하면 Claude 또는 DeepSeek가 더 정교한 분석을 제공:

```bash
cp .env.example .env
# .env 파일에 CLAUDE_API_KEY 또는 DEEPSEEK_API_KEY 입력
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | 서버 상태 확인 |
| `/api/stocks` | GET | 전체 종목 스코어 + 매매 시그널 |
| `/api/stocks?layer=1` | GET | Layer별 필터링 (1/2/3/4) |
| `/api/stocks/refresh` | POST | 실시간 데이터 강제 갱신 |
| `/api/correlation` | GET | 반도체 상관관계 + 리드-래그 분석 |
| `/api/price-targets` | GET | 가격 결정 모델 + 시나리오 투영 |
| `/api/scenarios` | GET | 투자 시나리오 + 리스크 프로필 |
| `/api/strategy/:profile` | GET | 프로필별 투자 전략 (conservative/moderate/aggressive/destructive) |
| `/api/backtest` | GET | 히스토리컬 백테스트 실행 |
| `/api/llm/analyze` | POST | LLM 분석 요청 (body: `{ provider, apiKey }`) |

---

## Project Structure

```
ai-supercycle-dashboard/
├── src/
│   ├── server.ts              # Express 서버 진입점
│   ├── routes/
│   │   └── api.ts             # 모든 API 엔드포인트
│   ├── data/
│   │   ├── stocks.ts          # 28종목 4-Layer 유니버스 + 시나리오 설정
│   │   └── yahoo.ts           # Yahoo Finance 실시간 데이터 페칭
│   ├── quant/
│   │   ├── scoring.ts         # 100점 퀀트 스코어링 엔진
│   │   ├── correlation.ts     # 반도체 상관관계 + 리드-래그 분석
│   │   ├── pricing.ts         # 가격 결정 모델 + 시나리오 투영
│   │   └── backtest.ts        # 매매 전략 백테스팅
│   └── llm/
│       └── provider.ts        # Claude / DeepSeek / Rule-Based LLM 프로바이더
├── views/
│   └── dashboard.ejs          # 대시보드 UI
├── public/                    # 정적 파일
├── dist/                      # TypeScript 컴파일 출력
├── package.json
└── tsconfig.json
```

---

## Scoring System

| Dimension | Weight | Key Metrics |
|---|---|---|
| **AI Revenue Exposure** | 35% | AI 직접 매출 비중, 데이터센터 매출 성장, RPO 가시성 |
| **Capital Efficiency & Momentum** | 30% | FCF 마진, 매출 성장률, ROIC, EPS 성장률 |
| **Valuation (GARP)** | 20% | PEG, Forward P/E, EV/Sales |
| **Momentum & Supply** | 15% | 6M/12M 가격 모멘텀, 52주 신고가 근접도 |

### Action Signals

| Signal | Score Range | Meaning |
|---|---|---|
| **STRONG_BUY** | ≥ 90 | 핵심 포지션. 12-15% 비중 |
| **BUY** | 80-89 | 매수. 8-10% 비중, 분기 리뷰 |
| **HOLD** | 70-79 | 보유. 포지션 유지 |
| **AVG_DOWN** | 55-69 + ≥ -20% from 52w high + rev growth ≥ 10% | 물타기 기회 |
| **SELL** | 40-54 | 매도 검토 |
| **STRONG_SELL** | < 40 | 전량 매도 |

---

## AI Supercycle Universe (28 Stocks)

### Layer 1: Foundation (반도체/장비) — 13 종목
NVDA, AVGO, TSM, ASML, AMD, MU, LRCX, AMAT, KLAC, MRVL, INTC  
**🇰🇷 삼성전자 (005930.KS)** · **🇰🇷 SK하이닉스 (000660.KS)**

### Layer 2: Infrastructure (하이퍼스케일러) — 5 종목
MSFT, GOOGL, META, AMZN, ORCL

### Layer 3: Enablers (전력/냉각/네트워크) — 6 종목
VRT, ANET, ETN, GEV, NVT, SMCI

### Layer 4: Application (기업 AI SW) — 5 종목
PLTR, NOW, CRM, CRWD, ADBE

---

## Investment Scenarios

| Profile | Stop Loss | Position Size | Rebalance | Min Score | Cash | Leverage |
|---|---|---|---|---|---|---|
| **Conservative** (보수) | -10% | 8% | 90d | 85 | 20% | No |
| **Moderate** (중도) | -15% | 10% | 60d | 75 | 10% | No |
| **Aggressive** (공격) | -22% | 14% | 30d | 65 | 5% | No |
| **Destructive** (파괴) | -30% | 16% | 14d | 0 | 0% | Yes (Layer 1) |

---

## HBM/DRAM Cycle Strategy

| Phase | Signal | Strategy |
|---|---|---|
| **Expansion** | Momentum > 15% | HBM 노출 종목 적극 매수 (MU, SK하이닉스, 삼성전자) |
| **Peak** | Momentum 5-15% | HBM 비중 축소. 손절라인 타이트하게 |
| **Contraction** | Momentum -5~5% | Layer 2(하이퍼스케일러), Layer 4(앱)으로 로테이션 |
| **Trough** | Momentum < -5% | HBM 리더 분할 매수. 2-3년 보유 호라이즌 |

---

## 12-Month Scenario Projections

| Scenario | Probability | NASDAQ-100 | Portfolio | Alpha |
|---|---|---|---|---|
| AI Capex Acceleration | 30% | +25% | **+32%** | +7pp |
| Base Case | 45% | +14% | **+18%** | +4pp |
| Capex Slowdown | 20% | -3% | **-1%** | +2pp |
| AI Bubble Burst | 5% | -28% | **-22%** | +6pp |
| **Probability-Weighted** | 100% | +13.6% | **+18.4%** | **+4.8pp** |

---

## Tech Stack

- **Runtime**: Node.js 18+
- **Language**: TypeScript 5.x
- **Framework**: Express.js 4.x
- **Data**: yahoo-finance2 (실시간 시세), mathjs (통계)
- **LLM**: Claude (Anthropic) / DeepSeek / Rule-Based Fallback
- **Templating**: EJS
- **Dev Server**: tsx (watch mode)

---

## Commands

```bash
npm run dev      # 개발 서버 (tsx watch, auto-reload)
npm run build    # TypeScript 컴파일
npm run start    # 컴파일된 JS 실행
npm run lint     # TypeScript 타입 체크
```

---

## Risk Disclaimer

- 본 애플리케이션은 **교육·연구 목적의 가상 시뮬레이션**이며, 실제 투자 권유가 아닙니다
- AI 슈퍼사이클은 닷컴버블(2000) 대비 펀더멘털이 강하지만 **-50% drawdown 가능성**을 인지해야 합니다
- Yahoo Finance 데이터는 ±5% 오차 가능. 실거래 전 반드시 크로스체크 필요
- 한국 거주자: 양도소득세 22% + 원천징수 15% 검토 필요
- LLM 분석 결과는 참고용이며, 최종 투자 결정은 본인 판단 + 전문가 상담 필수

---

## Related

- [vibe-investing 원본 레포](https://github.com/gameworkerkim/vibe-investing) — Dennis Kim의 AI Supercycle Quant Strategy 원문
- AI Super Cycle Prompt EN.MD / KR.MD / CN.MD
- Dividend Growth Prompt
- DAT Quant Strategy

## License

MIT — [gameworkerkim/vibe-investing](https://github.com/gameworkerkim/vibe-investing)

---

> *"In the AI super cycle, the picks and shovels matter more than the gold."*
