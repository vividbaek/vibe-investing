# [보도자료] "개인도 헤지펀드처럼" — AI로 만든 SaaS 공매도·HBM 매수 전략, GitHub 공개

**2026년 5월 18일, 서울** — 블록체인 컴퍼니 빌더 베타랩스 김호광 대표(Dennis Kim)가 글로벌 헤지펀드 수준의 롱/숏(Long/Short) 트레이딩 전략을 GitHub에 공개했다. 시장 분석 칼럼 한 편을 입력해 대규모 언어모델(LLM)로 전략을 자동 추출한 결과물로, **"이제 개인 투자자도 헤지펀드 수준의 전략을 짤 수 있다"**는 점을 보여주는 사례다.

## 한 줄 요약

- AI가 잡아먹는 SaaS는 **공매도**, AI를 굴리는 HBM·반도체는 **매수**
- 이 전략을 짠 도구는 LLM 프롬프트 하나. 비용은 사실상 0원
- 칼럼·전략 노트·리스크 안내까지 한국어/영어로 GitHub 공개
- 저자는 **"개인 투자자가 헤지펀드처럼 일할 수 있는 시대"**가 본격적으로 열렸다고 강조

## 무슨 일이 일어났나

2026년 5월, 글로벌 자본시장은 동시다발적 충격에 휩싸였다.

- **노무라 증권**은 삼성전자 목표주가를 34만 원 → 59만 원, SK하이닉스를 234만 원 → 400만 원으로 상향했다. 메모리를 더 이상 '경기 순환형 산업'으로 보지 않고 'AI 시대의 구조적 성장 산업'으로 재평가한 것이다.
- 같은 주, **미국 30년물 국채 금리는 5.127%**까지 치솟아 19년 만의 최고치를 기록했다. 일본 생보사들의 미 국채 매도가 가속화된 결과다.
- 그 사이 SaaS 섹터에서는 **48시간 만에 2,850억 달러**가 증발했다. 일명 'SaaSpocalypse'다. Adobe(-37%), Duolingo(-46%), ServiceNow(-35%), Salesforce(-28%) 등이 줄줄이 무너졌다.
- 그러나 같은 기간 **한국의 반도체 수출은 전년 동기 대비 +139.1%**, D램은 +249.1% 폭증했다.

김 대표는 자신의 칼럼 *AI 메모리 슈퍼사이클 vs. SaaSpocalypse*에서 이 네 사건이 별개의 뉴스가 아니라 **"하나의 거대한 자본 흐름의 다른 단면"**이라고 분석했다. 시장이 매도한 '중간층 소프트웨어'의 자금은 결국 '하단의 컴퓨트·메모리'로 회수되며, 그 직접 수혜자가 HBM 과점을 형성한 한국 반도체 양강이라는 것이다.

## "그래서 어떻게 사고팔까?"를 LLM에게 묻다

흥미로운 지점은 그다음이다. 김 대표는 자신이 쓴 칼럼을 LLM에 넣고 **"이 시장 분석을 헤지펀드 트레이더와 퀀트 리서처 두 관점에서 실행 가능한 전략으로 바꿔달라"**고 프롬프트를 입력했다. 결과물은 다음과 같다.

**트레이더 관점 — 종목 단위 베팅**

- 공매도(Short): Adobe, Duolingo, Wix, Shutterstock 등 AI 대체 위험군
- 매수(Long): 삼성전자, SK하이닉스, TSMC, Uber (물리적 해자 보유)
- 페어 트레이드: SaaS 인덱스 ETF 숏 ↔ 반도체(SOX) 인덱스 롱
- 매크로 헤지: TLT(장기국채) 숏 또는 금리선물 매도로 베타 축소
- 옵션 전략: OTM 풋 매수로 테일 리스크 헤지

**퀀트 관점 — 통계적 차익거래**

- **AI 디스럽션 스코어**: 구독 매출 비중, R&D 대비 AI 특허 수, 물리적 자산 보유, 실적 콜 NLP 감성을 점수화
- 상위 20%(고위험 SaaS)는 공매도, 하위 20%(반도체·인프라)는 매수
- SaaS 지수(WCLD)와 반도체 지수(SOX)의 공적분 잔차가 2σ 이상 벌어지면 진입
- NLP 시그널: "SaaS-pocalypse", "Big Squeeze" 키워드 빈도 급증 시 숏 비중 확대

전 과정에서 김 대표가 한 일은 **칼럼 작성 + 프롬프트 입력 + 검증**뿐이다. 과거에는 헤지펀드의 전략 팀이 며칠씩 매달려 만들던 결과물이, 이제는 한 사람과 LLM 한 대로 몇 분 만에 나온다.

## "Vibe Investing" — 직관과 자동화의 결합

김 대표는 이 접근법을 자신의 GitHub 저장소 이름 그대로 **'Vibe Investing'**이라고 부른다. 시장의 '결(vibe)'을 읽어내는 인간의 직관과, 그것을 즉시 정량적 전략으로 변환해주는 AI의 결합이라는 의미다.

> "한국의 서학개미 투자자들이 마주한 가장 큰 벽은 정보의 비대칭과 도구의 비대칭이었습니다. 골드만삭스 리포트, 노무라 목표가, 블룸버그 터미널 — 이 모든 게 기관에만 있었죠. 그런데 LLM은 그 벽을 단숨에 무너뜨립니다. 누구든 좋은 시장 가설만 세울 수 있다면, 그것을 헤지펀드 수준의 실행 전략으로 펼쳐낼 수 있는 시대가 됐습니다."

— Dennis Kim, 베타랩스 대표

## 무엇이 공개됐나

GitHub 저장소(`gameworkerkim/vibe-investing`)에는 다음이 함께 공개됐다.

- **원본 칼럼** (한국어·영어·중국어): *AI Memory Supercycle vs. SaaSpocalypse*
- **트레이더/퀀트 전략 노트** (한국어·영어)
- **LLM 추출용 프롬프트** (다른 산업 칼럼에도 재활용 가능)
- **README 가이드**: 비전문가도 이해할 수 있도록 평이한 언어로 전략을 설명
- **리스크 안내 12개 항목**: 숏 스퀴즈, 페어 디버전스, AI capex 둔화, 환율 리스크, 한국 공매도 금지 규제, 백테스트 슬리피지 등 실제 헤지펀드 북을 파괴해 온 시나리오들

특히 리스크 안내는 의도적으로 무겁게 작성됐다. "이 전략은 안전하지 않고 수익을 보장하지 않는다"는 점을 반복적으로 강조한다.

## 링크

- **저장소**: <https://github.com/gameworkerkim/vibe-investing>
- **전략 폴더**: [01.Trading Strategy / SaaS short HBM Long](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/SaaS%20short%20HBM%20Long)
- **원본 칼럼 (한국어)**: [AI_Memory_Supercycle_vs_SaaSpocalypse_KR.md](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/SaaS%20short%20HBM%20Long/AI_Memory_Supercycle_vs_SaaSpocalypse_KR.md)
- **원본 칼럼 (English)**: [AI_Memory_Supercycle_vs_SaaSpocalypse_EN.md](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/SaaS%20short%20HBM%20Long/AI_Memory_Supercycle_vs_SaaSpocalypse_EN.md)
- **원본 칼럼 (中文)**: [AI_Memory_Supercycle_vs_SaaSpocalypse_CN.md](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/SaaS%20short%20HBM%20Long/AI_Memory_Supercycle_vs_SaaSpocalypse_CN.md)

## 저자 정보

**Dennis Kim (김호광)**는 베타랩스(Betalabs Inc.) 대표이자 블록체인 미디어 Web3Paper 발행인이다. 전 싸이월드 Z 대표이사를 역임했고, 장기간 Microsoft Azure MVP로 활동하고 있다. 사이버 위협 인텔리전스(CTI) 독립 분석가이자 LLM 출력의 언어 간 발산 현상에 관한 학술 논문 시리즈 *"Same LLM, Different Languages"*의 저자다.

**연락처**: <gameworker@gmail.com> / GitHub [@gameworkerkim](https://github.com/gameworkerkim)

## 면책 조항

본 자료에 포함된 모든 전략과 분석은 리서치 및 교육 목적입니다. **투자 권유가 아니며, 어떤 증권에 대한 매수·매도 추천도 아닙니다.** 과거 성과는 미래 수익을 보장하지 않으며, 공매도·옵션·레버리지는 투입 자본을 초과하는 손실을 초래할 수 있습니다. 저자는 등록된 투자자문업자가 아닙니다.

---

# 링크드인(LinkedIn) 게시용 짧은 버전

## 본문

며칠 전, 시장 분석 칼럼 한 편을 썼습니다.

*"AI 메모리 슈퍼사이클 vs. SaaSpocalypse"* — 노무라가 삼성전자에 59만 원, SK하이닉스에 400만 원이라는 사상 최고 목표가를 던지는 동시에, SaaS 섹터에서 48시간 만에 2,850억 달러가 증발한 그 주의 시장을 한 장의 지도로 그린 글이었습니다.

그리고 그 칼럼을 그대로 LLM에 넣고 물었습니다.

**"이 분석을 헤지펀드 트레이더와 퀀트 두 관점에서 실행 가능한 전략으로 바꿔주세요."**

몇 분 뒤 손에 들어온 결과물:

→ Adobe·Duolingo·Wix를 숏, 삼성·하이닉스·TSMC를 롱으로 가는 종목 단위 베팅
→ SaaS 인덱스 ETF 숏 ↔ SOX 반도체 인덱스 롱의 페어 트레이드
→ TLT 숏으로 매크로 베타를 줄이는 헤지 오버레이
→ 구독 매출 비중·AI 특허 수·실적 콜 NLP 감성을 결합한 AI 디스럽션 팩터 스코어
→ WCLD-SOX 공적분 잔차가 2σ 이상 벌어질 때 진입하는 통계적 차익거래

과거에는 헤지펀드 전략팀이 며칠씩 매달려야 나오던 문서입니다.

지금은 한 명과 LLM 한 대로 한 시간 안에 나옵니다.

저는 이걸 'Vibe Investing'이라고 부릅니다. 시장의 결을 읽어내는 인간의 직관과, 그것을 즉시 정량적 전략으로 변환해주는 AI의 결합. 한국의 서학개미 투자자들이 마주한 가장 큰 벽 — 기관과의 정보 비대칭, 도구 비대칭 — 이 이제 무너지고 있다는 뜻입니다.

물론 LLM이 짜준 전략을 그대로 시장에 던지면 무조건 깨집니다. 그래서 같은 저장소에 **이 거래를 망가뜨릴 수 있는 12가지 리스크 시나리오**를 같이 적었습니다. 숏 스퀴즈, 두 다리가 같이 무너지는 페어 디버전스, AI capex 둔화, 환율, 2023년 같은 공매도 금지 — 전부 실제 헤지펀드 북을 파괴한 적이 있는 항목들입니다.

칼럼·전략 노트·프롬프트·리스크 안내 모두 한국어/영어로 GitHub에 공개했습니다.

**저장소**: github.com/gameworkerkim/vibe-investing

투자 권유가 아닙니다. 다만 이 시대의 개인 투자자가 어디까지 도달할 수 있는지 보여주는 작은 실험으로 봐주시면 좋겠습니다.

---

## 해시태그 (SEO 노출용)

### 한국어 핵심 키워드
\#AI투자 #헤지펀드 #공매도 #SaaS공매도 #HBM #한국반도체 #삼성전자 #SK하이닉스 #TSMC #서학개미 #퀀트투자 #롱숏전략 #페어트레이드 #옵션전략 #매크로전략

### 영문/글로벌 키워드
\#VibeInvesting #HedgeFundStrategy #ShortSelling #SaaSpocalypse #HBMSupercycle #AIMemoryBoom #SamsungElectronics #SKHynix #QuantTrading #LongShort #PairsTrade #MacroTrading #LLMTrading #AIInvesting #FintechAI

### 인물·기관 키워드
\#DennisKim #김호광 #Betalabs #베타랩스 #Web3Paper #Nomura #노무라 #Anthropic #ClaudeCowork #Adobe #Duolingo #Salesforce #ServiceNow #Uber

### 거시·이벤트 키워드
\#FederalReserve #USTreasury #BlackMonday #검은월요일 #금리상승 #JapaneseBondCrisis #YenCarryTrade #Stargate #OpenAI #AIcapex #DataCenter #SemiconductorCycle

### 학술·연구 키워드
\#FactorModel #StatisticalArbitrage #NLPSignal #SentimentAnalysis #MarketNeutral #AlphaResearch #SSRN #OpenSourceResearch #DueDiligence #RiskManagement

---

*© 2026 Dennis Kim / Betalabs / Web3Paper. 무단 전재 및 재배포 금지. 본 자료의 인용은 출처 표기 시 자유롭게 허용됩니다.*
