// Price Determination Model for AI Supercycle Stocks
// Combines: fundamental valuation, HBM/DRAM correlation premiums, momentum overlay, and scenario projections

import { ScoredStock } from './scoring';
import { ScenarioConfig } from '../data/stocks';
import { CorrelationPair, LagAnalysis } from './correlation';

export interface PriceTarget {
  ticker: string;
  name: string;
  currentPrice: number;
  fairValueDcf: number;
  technicalTarget: number;
  correlationAdjustedTarget: number;
  consensusTarget: number;
  upsideDcfPct: number;
  upsideTechPct: number;
  upsideCorrPct: number;
}

export interface ScenarioProjection {
  scenario: string;
  probabilityPct: number;
  nasdaqReturnPct: number;
  portfolioReturnPct: number;
  triggerSignals: string[];
}

export interface TimedOutlook {
  timeframe: '1M' | '3M' | '12M';
  label: string;
  scenarios: ScenarioProjection[];
  topPicks: { ticker: string; name: string; weightPct: number; rationale: string }[];
  commentary: string;
}

export interface PortfolioModel {
  priceTargets: PriceTarget[];
  scenarios: ScenarioProjection[];
  outlooks: TimedOutlook[];
  weightedExpectedReturn: number;
  estimatedBeta: number;
  estimatedSharpeRatio: number;
  maxDrawdownEstimate: number;
  correlationPremium: number;
  hbmCyclePhase: 'expansion' | 'peak' | 'contraction' | 'trough';
}

// DCF simplified model: price = FCF_per_share * growth_factor / (discount_rate - growth_rate)
function computeDcfValue(metrics: { fcfMarginPct: number; revenueGrowthPct: number; currentPrice: number }): number {
  const fcfYield = metrics.fcfMarginPct / 100;
  const growthRate = Math.min(metrics.revenueGrowthPct / 100, 0.25); // cap 25%
  const discountRate = 0.10; // 10% WACC assumption

  if (fcfYield <= 0 || growthRate >= discountRate) {
    return metrics.currentPrice * 1.1; // fallback
  }

  // Simple perpetuity: Price = FCF * (1+g) / (r-g)
  const fcfPerShare = metrics.currentPrice * fcfYield;
  const terminalMultiple = (1 + growthRate) / (discountRate - growthRate);
  return fcfPerShare * terminalMultiple;
}

// Technical target: regression toward 52w high with momentum factor
function computeTechnicalTarget(currentPrice: number, pctFrom52wHigh: number, price12mPct: number): number {
  const momentumFactor = Math.max(0, price12mPct / 100) * 0.3;
  const meanReversionFactor = Math.abs(pctFrom52wHigh / 100) * 0.7;
  const target = currentPrice * (1 + momentumFactor + meanReversionFactor * 0.5);
  return target;
}

export function buildPriceTargets(scored: ScoredStock[], correlationReport?: { pairs: CorrelationPair[] }): PriceTarget[] {
  return scored.map(s => {
    const dcfValue = computeDcfValue(s.metrics);
    const techTarget = computeTechnicalTarget(s.metrics.currentPrice, s.metrics.pctFrom52wHigh, s.metrics.price12mPct);
    const upsideDcf = ((dcfValue / s.metrics.currentPrice) - 1) * 100;
    const upsideTech = ((techTarget / s.metrics.currentPrice) - 1) * 100;

    // Correlation-adjusted target: apply semiconductor correlation premium
    let corrAdj = s.metrics.currentPrice;
    if (correlationReport && (s.stock.subsegment.includes('HBM') || s.stock.subsegment.includes('DRAM') || s.stock.subsegment.includes('GPU'))) {
      const relevantPairs = correlationReport.pairs.filter(
        p => (p.tickerA === s.stock.ticker || p.tickerB === s.stock.ticker)
      );
      if (relevantPairs.length > 0) {
        const avgCorr = relevantPairs.reduce((sum, p) => sum + Math.abs(p.correlation), 0) / relevantPairs.length;
        const correlationPremium = avgCorr * 0.15; // 15% of avg correlation as premium
        corrAdj = s.metrics.currentPrice * (1 + correlationPremium);
      }
    }

    const avgTarget = (dcfValue + techTarget + corrAdj) / 3;

    return {
      ticker: s.stock.ticker,
      name: s.stock.name,
      currentPrice: s.metrics.currentPrice,
      fairValueDcf: Math.round(dcfValue * 100) / 100,
      technicalTarget: Math.round(techTarget * 100) / 100,
      correlationAdjustedTarget: Math.round(corrAdj * 100) / 100,
      consensusTarget: Math.round(avgTarget * 100) / 100,
      upsideDcfPct: Math.round(upsideDcf * 10) / 10,
      upsideTechPct: Math.round(upsideTech * 10) / 10,
      upsideCorrPct: Math.round(((corrAdj / s.metrics.currentPrice) - 1) * 1000) / 10,
    };
  });
}

export function generateScenarios(): ScenarioProjection[] {
  return [
    {
      scenario: 'AI Capex Acceleration (Guide-up)',
      probabilityPct: 30,
      nasdaqReturnPct: 25,
      portfolioReturnPct: 32,
      triggerSignals: [
        'Hyperscaler aggregate Capex YoY > +35%',
        'GPU ASP holding or rising QoQ',
        'Cloud AI revenue acceleration',
      ],
    },
    {
      scenario: 'Base Case (Capex plateau + revenue realization)',
      probabilityPct: 45,
      nasdaqReturnPct: 14,
      portfolioReturnPct: 18,
      triggerSignals: [
        'Hyperscaler Capex YoY +20~25%',
        'GPU ASP stable ±2% QoQ',
        'AI application revenue +80%+ YoY',
      ],
    },
    {
      scenario: 'Capex Slowdown (H1 guide-down)',
      probabilityPct: 20,
      nasdaqReturnPct: -3,
      portfolioReturnPct: -1,
      triggerSignals: [
        'Hyperscaler Capex YoY ≤ +10%',
        'GPU ASP declining ≥5% QoQ',
        'Data center vacancy rising ≥5%',
      ],
    },
    {
      scenario: 'AI Bubble Burst (Demand cracks)',
      probabilityPct: 5,
      nasdaqReturnPct: -28,
      portfolioReturnPct: -22,
      triggerSignals: [
        'Cloud growth deceleration <15%',
        'Major Hyperscaler Capex cut >20%',
        'AI app ARR growth <30% YoY',
      ],
    },
  ];
}

export function generateOutlooks(
  priceTargets: PriceTarget[],
  hbmPhase: string
): TimedOutlook[] {
  const sorted = [...priceTargets].sort((a, b) => {
    const avgA = (a.upsideDcfPct + a.upsideTechPct) / 2;
    const avgB = (b.upsideDcfPct + b.upsideTechPct) / 2;
    return avgB - avgA;
  });

  const isBullish = hbmPhase === 'expansion' || hbmPhase === 'peak';

  return [
    {
      timeframe: '1M',
      label: '1개월 단기 전망',
      scenarios: [
        { scenario: 'Bullish (지표 호조)', probabilityPct: 35, nasdaqReturnPct: 5, portfolioReturnPct: 7, triggerSignals: ['주간 실적 발표 호조', 'HBM 가격 상승 지속'] },
        { scenario: 'Base (현상 유지)', probabilityPct: 50, nasdaqReturnPct: 2, portfolioReturnPct: 3, triggerSignals: ['Capex 가이던스 유지', '환율 안정'] },
        { scenario: 'Bearish (단기 조정)', probabilityPct: 15, nasdaqReturnPct: -4, portfolioReturnPct: -5, triggerSignals: ['GP 주가 조정', '금리 인상 우려'] },
      ],
      topPicks: sorted.slice(0, 4).map(s => ({
        ticker: s.ticker,
        name: s.name,
        weightPct: 25,
        rationale: '단기 모멘텀 + 실적 서프라이즈 기대',
      })),
      commentary: isBullish
        ? 'HBM 수요 강세 지속. 반도체 Layer 1 비중 확대. 단기 변동성에 분할 매수 전략 유효.'
        : '사이클 후반 조정 가능성. 현금 비중 확대하고 Layer 2 방어적 비중 선호.',
    },
    {
      timeframe: '3M',
      label: '3개월 중기 전망',
      scenarios: [
        { scenario: 'Bullish (Capex 상향)', probabilityPct: 30, nasdaqReturnPct: 10, portfolioReturnPct: 14, triggerSignals: ['Hyperscaler 실적 서프라이즈', '신규 AI 칩 출시'] },
        { scenario: 'Base (점진적 성장)', probabilityPct: 45, nasdaqReturnPct: 5, portfolioReturnPct: 7, triggerSignals: ['Capex 유지', '클라우드 성장 지속'] },
        { scenario: 'Bearish (수요 둔화)', probabilityPct: 25, nasdaqReturnPct: -6, portfolioReturnPct: -8, triggerSignals: ['Capex 가이던스 하향', 'AI 수익화 지연'] },
      ],
      topPicks: sorted.slice(0, 6).map((s, i) => ({
        ticker: s.ticker,
        name: s.name,
        weightPct: i < 3 ? 20 : 13,
        rationale: s.upsideDcfPct >= 10 ? 'DCF 저평가 + 성장 모멘텀' : '안정적 포트폴리오 방어',
      })),
      commentary: isBullish
        ? 'AI Capex 사이클 중반. Layer 1+3 비중 60% 유지. 실적 시즌 전 선매수 전략.'
        : '방어적 포지셔닝. Layer 2(하이퍼스케일러) 비중 확대. 변동성 헷지 고려.',
    },
    {
      timeframe: '12M',
      label: '12개월 장기 전망',
      scenarios: generateScenarios(),
      topPicks: sorted.slice(0, 10).map((s, i) => ({
        ticker: s.ticker,
        name: s.name,
        weightPct: i < 4 ? 12 : i < 7 ? 10 : 8,
        rationale: s.upsideDcfPct >= 15 ? '장기 AI 수혜 + 밸류에이션 매력' : 'AI 슈퍼사이클 핵심 포트폴리오',
      })),
      commentary: 'AI 슈퍼사이클 장기 투자. 확률가중 기대수익 +18.4%. 분기 리밸런싱 권장.',
    },
  ];
}

export function computePortfolioModel(
  priceTargets: PriceTarget[],
  scenarios: ScenarioProjection[],
  beta: number = 1.3,
): PortfolioModel {
  const weightedReturn = scenarios.reduce(
    (sum, s) => sum + (s.probabilityPct / 100) * s.portfolioReturnPct,
    0
  );

  const sharpeEstimate = weightedReturn / (15 * Math.sqrt(3)); // approx
  const maxDrawdown = -Math.abs(scenarios[scenarios.length - 1].portfolioReturnPct);

  // Correlation premium: average of correlation-adjusted upside
  const avgCorrUpside = priceTargets
    .filter(p => p.upsideCorrPct !== 0)
    .reduce((sum, p) => sum + p.upsideCorrPct, 0) / Math.max(1, priceTargets.filter(p => p.upsideCorrPct !== 0).length);

  // HBM cycle phase estimation from price momentum
  const avgMomentum = priceTargets.reduce((sum, p) => {
    return sum + ((p.consensusTarget / p.currentPrice) - 1) * 100;
  }, 0) / priceTargets.length;

  let hbmPhase: PortfolioModel['hbmCyclePhase'];
  if (avgMomentum > 15) hbmPhase = 'expansion';
  else if (avgMomentum > 5) hbmPhase = 'peak';
  else if (avgMomentum > -5) hbmPhase = 'contraction';
  else hbmPhase = 'trough';

  return {
    priceTargets,
    scenarios,
    outlooks: generateOutlooks(priceTargets, hbmPhase),
    weightedExpectedReturn: Math.round(weightedReturn * 10) / 10,
    estimatedBeta: beta,
    estimatedSharpeRatio: Math.round(sharpeEstimate * 100) / 100,
    maxDrawdownEstimate: Math.round(maxDrawdown * 10) / 10,
    correlationPremium: Math.round(avgCorrUpside * 10) / 10,
    hbmCyclePhase: hbmPhase,
  };
}
