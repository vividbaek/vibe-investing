# AI Disruption Long/Short Strategy

A long/short investment thesis triggered by AI's disruption of subscription-based software, combined with the parallel concentration of value in AI hardware and physical-gateway platforms.

> 한국어 버전은 아래에 있습니다 — [한국어로 건너뛰기](#한국어-버전)

---

## English

### What this strategy is trying to do (in plain language)

The thesis has two parts:

1. **Software with no moat is in trouble.** Many SaaS and subscription products — design tools, language learning apps, stock photography, no-code website builders — can now be substantially replicated by general-purpose AI agents. When users can ask an AI to do the same job for free or near-free, paying $20–60 per month per seat becomes harder to justify.

2. **Whoever supplies AI and owns physical bottlenecks wins.** AI itself runs on a narrow set of chips, and inside that, HBM memory is the key bottleneck. The companies that control this bottleneck — Samsung, SK Hynix, TSMC — capture a disproportionate share of the value chain. The same logic applies to platforms with a physical or behavioral moat that AI cannot replicate, such as Uber's driver network.

**The trade**: short the businesses being displaced, long the businesses capturing the new value, with macro hedges (interest rates) and risk-management overlays (options, pair sizing, sector neutrality) on top.

### What's in this folder

- `strategy_note_en.md` — full English playbook (trader view + quant view + LLM extraction prompts)
- `strategy_note_ko.md` — Korean version of the same playbook
- `README.md` — this file

### How the two layers fit together

| Trader layer | Quant layer |
|---|---|
| Individual tickers, conviction-based bets | Factor portfolios, market-neutral construction |
| Discretionary entry/exit on news events | Statistical signals (cointegration, momentum breakdown) |
| Options for asymmetric payoff | NLP signals for systematic rebalancing |
| Macro overlay (rates, FX) | Risk management (beta neutrality, borrow availability) |

The two layers are complementary: the trader version suits someone running 10–20 high-conviction positions; the quant version suits someone running 100–1,000 positions on statistical edge.

### Risks — please read carefully

This strategy is **not safe** and **not guaranteed**. The risks below are not legal boilerplate — each one has destroyed real hedge-fund books before.

**1. The thesis itself could be wrong.**
"SaaS-pocalypse" is one viewpoint, not consensus. Adobe is already shipping its own AI tools (Firefly, AI Assistant). Duolingo monetizes habit and gamification, not just translation. The displacement could happen, take a decade, or never happen — and the position bleeds the whole time.

**2. Short squeeze risk.**
Heavily-shorted names can produce sudden, violent losses. One positive earnings surprise, an AI-partnership announcement, or a buyout rumor can spike a stock 20–40% overnight. Losses on a short position are theoretically unbounded.

**3. Both legs of the pair can collapse together.**
The strategy assumes SaaS shorts and semiconductor longs move in opposite directions. In a broad market crash, **both can fall together**, and the long leg often falls harder. Correlation tends to spike toward 1 precisely when you need it lowest.

**4. An AI capex pause hits the long leg directly.**
The HBM long depends on continued AI capital expenditure from hyperscalers. Any signal of slowing AI capex — an earnings miss from a major AI buyer, new export restrictions, a hyperscaler guiding capex lower — hits Samsung and SK Hynix immediately and hard.

**5. Concentration risk.**
Long exposure to Samsung + SK Hynix + TSMC concentrates the book in Korea/Taiwan equities, the AI semiconductor cycle, and US–China geopolitics. A Taiwan Strait incident or new US export controls can collapse the long leg overnight.

**6. Currency risk.**
A Korean investor going long Samsung (KRW) and short US SaaS (USD) takes on USD/KRW exposure on top of the equity thesis. A weakening dollar erodes the local-currency gain on the US short leg.

**7. Rate-regime risk.**
The strategy implicitly bets on rising long-end yields via long-duration SaaS shorts. If the Fed cuts faster than expected and yields drop, the very names you shorted can rally hard.

**8. Liquidity and borrow cost.**
Some SaaS shorts carry high stock-borrow fees. A 10–20% annual borrow rate can erase the entire short-side alpha. Borrow availability can also disappear suddenly, forcing a buy-in at the worst possible price.

**9. Options-specific risks.**
- Time decay (theta) works against long-premium positions.
- Implied volatility can collapse after the news event you positioned for, even if direction is correct.
- Early assignment on short options can break the structure.

**10. Regulatory risk.**
Short-selling rules differ across jurisdictions. Korea has imposed full short-selling bans multiple times (most recently in 2023). A ban locks new shorts out and can force unfavorable position closure.

**11. Backtest-to-live slippage.**
For the quant version: any backtest that ignores borrow cost, slippage, market impact, and stock-loan recall will overstate returns substantially. Real-world deployment routinely cuts paper-trade alpha by half or more.

**12. The source article itself can be wrong, biased, or already priced in.**
By the time a thesis appears in mainstream financial commentary, it is rarely a fresh edge.

### Disclaimer

This repository is research and educational material. It is **not investment advice**, **not a recommendation** to buy or sell any security, and **not a solicitation** of any kind. Past performance does not guarantee future returns. Securities trading, short selling, options, and leverage can produce losses exceeding the initial capital deployed. Anyone considering acting on these ideas should consult a licensed financial advisor in their jurisdiction and conduct their own independent due diligence.

The author is not a registered investment advisor. This content reflects personal research only.

---

## 한국어 버전

### 이 전략이 노리는 것 (쉽게 설명)

논제는 두 부분으로 이루어져 있습니다.

1. **해자(moat)가 없는 소프트웨어는 위험하다.** 디자인 툴, 어학 학습, 스톡 이미지, 노코드 웹빌더 같은 많은 SaaS·구독 제품은 이제 범용 AI 에이전트가 상당 부분 대체할 수 있습니다. 사용자가 무료에 가깝게 AI에게 같은 일을 시킬 수 있는데, 시트당 월 $20–60을 지불하는 것은 점점 정당화하기 어려워집니다.

2. **AI를 공급하고 물리적 병목을 가진 쪽이 이긴다.** AI는 좁은 범위의 반도체에 의존하며, 그 안에서도 HBM 메모리가 핵심 병목입니다. 이 병목을 쥔 삼성, SK하이닉스, TSMC가 가치사슬에서 불균형적으로 큰 몫을 가져갑니다. AI가 복제할 수 없는 물리적·행동적 해자를 가진 플랫폼(우버의 운전자 네트워크 등)도 같은 논리가 적용됩니다.

**거래 구조**: 밀려나는 쪽은 공매도, 새로운 가치를 가져가는 쪽은 매수. 여기에 매크로 헤지(금리)와 리스크 관리 레이어(옵션, 페어 사이징, 섹터 중립)를 얹습니다.

### 이 폴더의 구성

- `strategy_note_ko.md` — 한국어 풀 플레이북 (트레이더 + 퀀트 + LLM 추출 프롬프트)
- `strategy_note_en.md` — 동일한 내용의 영문 버전
- `README.md` — 본 문서

### 두 레이어의 역할 분담

| 트레이더 레이어 | 퀀트 레이어 |
|---|---|
| 개별 종목, 확신 기반 베팅 | 팩터 포트폴리오, 시장 중립 구성 |
| 뉴스 기반 재량 진입/청산 | 통계적 신호 (공적분, 모멘텀 붕괴) |
| 비대칭 페이오프용 옵션 | NLP 시그널 기반 체계적 리밸런싱 |
| 매크로 오버레이 (금리, 환율) | 리스크 관리 (베타 중립, 대차 가능성) |

두 레이어는 상호 보완적입니다. 트레이더 버전은 강한 확신을 가지고 10–20개 포지션을 운용하는 사람에게, 퀀트 버전은 통계적 우위에 기대 100–1,000개 포지션을 운용하는 사람에게 적합합니다.

### 리스크 — 반드시 읽어야 합니다

이 전략은 **안전하지 않으며 수익을 보장하지 않습니다.** 아래는 이 거래를 망가뜨릴 수 있는 구체적 리스크입니다. 법적 면피용 문구가 아니라, 각각 실제 헤지펀드 북을 파괴한 전례가 있는 항목들입니다.

**1. 논제 자체가 틀릴 수 있다.**
"SaaS-pocalypse"는 하나의 시각일 뿐 합의가 아닙니다. Adobe는 이미 자체 AI 도구(Firefly, AI Assistant)를 출시하고 있고, Duolingo는 단순 번역이 아니라 습관·게이미피케이션으로 돈을 법니다. 디스럽션이 일어날 수도, 10년이 걸릴 수도, 안 일어날 수도 있으며, 그 동안 포지션은 계속 비용을 흘립니다.

**2. 숏 스퀴즈 리스크.**
공매도 잔고가 높은 종목은 단기간에 급격한 손실을 안길 수 있습니다. 호실적 깜짝, AI 제휴 발표, 인수 루머 하나로 주가가 하룻밤 사이 20–40% 급등할 수 있습니다. 공매도 손실은 이론적으로 무한대입니다.

**3. 페어 트레이드의 두 다리가 같이 무너질 수 있다.**
이 전략은 SaaS 숏과 반도체 롱이 반대 방향으로 움직인다고 가정합니다. 그러나 광범위한 시장 폭락에서는 **둘 다 같이 빠지며**, 종종 롱 다리가 더 크게 빠집니다. 상관관계는 가장 낮아야 할 순간에 1로 치솟는 경향이 있습니다.

**4. AI 자본지출(CapEx) 둔화는 롱 다리를 직격한다.**
HBM 롱은 하이퍼스케일러의 AI 자본지출이 이어진다는 전제에 의존합니다. AI 자본지출 둔화 신호(주요 AI 구매자의 실적 미스, 신규 수출 통제, 하이퍼스케일러의 자본지출 가이던스 하향) 하나면 삼성과 SK하이닉스는 즉시 크게 흔들립니다.

**5. 집중 리스크.**
삼성 + SK하이닉스 + TSMC 롱은 곧 한국·대만 주식, AI 반도체 사이클, 미·중 지정학에 모두 노출된다는 뜻입니다. 대만 해협 사건이나 새로운 미국 수출 통제 한 번이면 롱 다리가 하룻밤에 무너질 수 있습니다.

**6. 환율 리스크.**
한국 투자자가 삼성(KRW) 롱 + 미국 SaaS(USD) 숏을 잡으면, 주식 논제 위에 USD/KRW 노출까지 함께 떠안게 됩니다. 달러 약세는 미국 숏 다리의 원화 환산 수익을 깎습니다.

**7. 금리 체제 리스크.**
이 전략은 장기 듀레이션 SaaS 숏을 통해 부분적으로 금리 상승에 베팅합니다. 만약 연준이 예상보다 빠르게 인하해 금리가 빠지면, 공매도했던 장기 듀레이션 종목들이 강하게 반등할 수 있습니다.

**8. 유동성 및 대차 비용.**
일부 SaaS 숏은 대차 비용이 비쌉니다. 연 10–20%의 대차료는 숏의 알파를 통째로 갉아먹을 수 있습니다. 대차 물량 자체가 갑자기 사라져 최악의 가격에 강제 청산(buy-in)을 당할 수도 있습니다.

**9. 옵션 고유 리스크.**
- 시간 감쇠(theta)는 롱 프리미엄 포지션에 불리하게 작용합니다.
- 노리던 이벤트가 지나간 뒤 내재변동성이 무너지면 방향이 맞아도 손실이 날 수 있습니다.
- 매도한 옵션의 조기 행사(early assignment)는 구조를 무너뜨립니다.

**10. 규제 리스크.**
공매도 규제는 국가마다 다릅니다. 한국은 여러 차례 전면 공매도 금지를 시행했습니다(가장 최근 2023년). 금지 조치가 발동되면 신규 숏은 막히고 기존 포지션도 불리한 가격에 청산해야 할 수 있습니다.

**11. 백테스트 ↔ 실거래 간 슬리피지.**
퀀트 버전의 경우, 대차 비용·슬리피지·시장 충격·대차 회수(stock-loan recall)를 제대로 반영하지 않은 백테스트는 수익을 크게 과대평가합니다. 실제 운용은 페이퍼 트레이드 알파를 절반 이상 깎는 게 보통입니다.

**12. 영감을 준 칼럼 자체가 틀렸거나 편향되었거나 이미 가격에 반영되어 있을 수 있다.**
어떤 논제가 주류 금융 매체에 등장할 때쯤이면, 그것이 신선한 우위인 경우는 드뭅니다.

### 면책 조항

이 저장소는 리서치 및 교육 목적의 자료입니다. **투자 권유가 아니며**, 어떤 증권에 대한 **매수·매도 추천도 아니고**, 어떤 종류의 **권유도 아닙니다**. 과거 성과는 미래 수익을 보장하지 않습니다. 증권 거래, 공매도, 옵션, 레버리지는 투입 자본을 초과하는 손실을 초래할 수 있습니다. 이 저장소의 아이디어를 실제로 실행하려는 사람은 자신의 관할 지역의 등록된 금융 자문가와 상의하고 독립적인 실사를 직접 수행해야 합니다.

저자는 등록된 투자자문업자가 아닙니다. 본 내용은 개인 리서치만을 반영합니다.
