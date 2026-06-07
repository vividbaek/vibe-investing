// Quant Scoring Engine - Ported from ai_super_cycle_screener.py
// 100-point scoring system: AI Exposure (35) + Capital Efficiency (30) + Valuation (20) + Momentum (15)

import { FetchMetrics } from '../data/yahoo';
import { ExtendedStockMeta, SCREENING_THRESHOLDS } from '../data/stocks';

export interface BreakdownScores {
  aiExposure: number;
  capitalEfficiency: number;
  valuation: number;
  momentum: number;
}

export interface ScoredStock {
  stock: ExtendedStockMeta;
  metrics: FetchMetrics;
  scores: BreakdownScores;
  totalScore: number;
  passesScreen: boolean;
  failReasons: string[];
  investmentThesis?: string;
  riskFactors?: string;
  actionSignal: ActionSignal;
}

export type ActionSignal = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'AVG_DOWN' | 'SELL' | 'STRONG_SELL';

function scoreAiExposure(stock: ExtendedStockMeta, _metrics: FetchMetrics): number {
  let base = Math.min((stock.aiExposurePct / 100) * 30, 30);
  let bonus = 0;

  if (stock.layer === 1 && stock.aiExposurePct >= 60) bonus = 5;
  else if (stock.layer === 2 && stock.aiExposurePct >= 30) bonus = 4;
  else if (stock.layer === 3 && stock.aiExposurePct >= 60) bonus = 4;
  else if (stock.layer === 4 && stock.aiExposurePct >= 70) bonus = 3;
  else bonus = 2;

  return Math.min(base + bonus, 35);
}

function scoreCapitalEfficiency(m: FetchMetrics): number {
  let score = 0;

  // FCF margin (0-8)
  if (m.fcfMarginPct >= 30) score += 8;
  else if (m.fcfMarginPct >= 20) score += 6;
  else if (m.fcfMarginPct >= 10) score += 4;
  else if (m.fcfMarginPct >= 5) score += 2;

  // Revenue growth (0-9)
  if (m.revenueGrowthPct >= 40) score += 9;
  else if (m.revenueGrowthPct >= 25) score += 7;
  else if (m.revenueGrowthPct >= 15) score += 5;
  else if (m.revenueGrowthPct >= 8) score += 3;

  // ROIC proxy (0-7)
  if (m.roicPct >= 30) score += 7;
  else if (m.roicPct >= 20) score += 5;
  else if (m.roicPct >= 10) score += 3;
  else if (m.roicPct >= 5) score += 1;

  // EPS growth (0-6)
  if (m.epsGrowthPct >= 30) score += 6;
  else if (m.epsGrowthPct >= 15) score += 4;
  else if (m.epsGrowthPct >= 5) score += 2;

  return Math.min(score, 30);
}

function scoreValuation(m: FetchMetrics): number {
  let score = 0;
  if (m.forwardPE <= 0) return 10;

  // PEG-style (0-12)
  if (m.epsGrowthPct > 0) {
    const peg = m.forwardPE / m.epsGrowthPct;
    if (peg <= 1.0) score += 12;
    else if (peg <= 1.5) score += 9;
    else if (peg <= 2.0) score += 6;
    else if (peg <= 3.0) score += 3;
  } else {
    if (m.forwardPE <= 25) score += 8;
    else if (m.forwardPE <= 35) score += 5;
    else if (m.forwardPE <= 50) score += 2;
  }

  // Forward PE absolute (0-8)
  if (m.forwardPE <= 20) score += 8;
  else if (m.forwardPE <= 30) score += 6;
  else if (m.forwardPE <= 40) score += 4;
  else if (m.forwardPE <= 60) score += 2;

  return Math.min(score, 20);
}

function scoreMomentum(m: FetchMetrics): number {
  let score = 0;

  // 12-month return (0-7)
  if (m.price12mPct >= 50) score += 7;
  else if (m.price12mPct >= 30) score += 5;
  else if (m.price12mPct >= 10) score += 3;
  else if (m.price12mPct >= 0) score += 1;

  // 6-month return (0-5)
  if (m.price6mPct >= 25) score += 5;
  else if (m.price6mPct >= 10) score += 3;
  else if (m.price6mPct >= 0) score += 1;

  // Distance from 52w high (0-3)
  if (m.pctFrom52wHigh >= -5) score += 3;
  else if (m.pctFrom52wHigh >= -15) score += 2;
  else if (m.pctFrom52wHigh >= -25) score += 1;

  return Math.min(score, 15);
}

function computeActionSignal(score: number, pctFrom52wHigh: number, revenueGrowth: number): ActionSignal {
  if (score >= 90 && pctFrom52wHigh >= -10) return 'STRONG_BUY';
  if (score >= 80) return 'BUY';
  if (score >= 70) return 'HOLD';
  if (score >= 55 && pctFrom52wHigh <= -20 && revenueGrowth >= 10) return 'AVG_DOWN';
  if (score >= 55) return 'HOLD';
  if (score >= 40) return 'SELL';
  return 'STRONG_SELL';
}

function generateThesis(stock: ExtendedStockMeta, metrics: FetchMetrics): string {
  const theses: string[] = [];
  if (stock.layer === 1 && stock.subsegment.includes('GPU')) theses.push('GPU cycle beneficiary');
  if (stock.layer === 1 && stock.subsegment.includes('HBM')) theses.push('HBM memory demand surge');
  if (stock.layer === 1 && stock.subsegment.includes('Foundry')) theses.push('Advanced process node monopoly');
  if (stock.layer === 2) theses.push('Hyperscaler cloud AI revenue growth');
  if (stock.layer === 3 && stock.subsegment.includes('Power')) theses.push('Data center power infrastructure');
  if (stock.layer === 3 && stock.subsegment.includes('Network')) theses.push('AI cluster networking demand');
  if (stock.layer === 4) theses.push('Enterprise AI application adoption');
  if (metrics.revenueGrowthPct >= 30) theses.push(`Revenue growth ${metrics.revenueGrowthPct.toFixed(1)}%`);
  if (metrics.fcfMarginPct >= 30) theses.push(`Strong FCF margin ${metrics.fcfMarginPct.toFixed(1)}%`);
  return theses.join('; ') || 'AI supercycle exposure';
}

function generateRisks(stock: ExtendedStockMeta, _metrics: FetchMetrics): string {
  const risks: string[] = [];
  if (stock.layer === 1) risks.push('Capex cycle peak risk');
  if (stock.region === 'Taiwan') risks.push('Geopolitical risk');
  if (stock.region === 'Korea') risks.push('Geopolitical risk (Korea peninsula)');
  if (stock.market === 'KR') risks.push('KRW/USD FX volatility');
  if (stock.subsegment.includes('HBM')) risks.push('HBM oversupply risk');
  if (stock.layer === 4) risks.push('Valuation overhang');
  return risks.join('; ') || 'Market cycle risk';
}

export function scoreStock(stock: ExtendedStockMeta, metrics: FetchMetrics): ScoredStock {
  const scores: BreakdownScores = {
    aiExposure: round(scoreAiExposure(stock, metrics)),
    capitalEfficiency: round(scoreCapitalEfficiency(metrics)),
    valuation: round(scoreValuation(metrics)),
    momentum: round(scoreMomentum(metrics)),
  };

  const totalScore = round(scores.aiExposure + scores.capitalEfficiency + scores.valuation + scores.momentum);

  const failReasons: string[] = [];
  if (metrics.marketCapB < SCREENING_THRESHOLDS.minMarketCapB) failReasons.push('market_cap');
  if (metrics.revenueGrowthPct < SCREENING_THRESHOLDS.minRevenueGrowthPct) failReasons.push('rev_growth');
  if (metrics.fcfMarginPct < SCREENING_THRESHOLDS.minFcfMarginPct) failReasons.push('fcf_margin');
  if (stock.aiExposurePct < SCREENING_THRESHOLDS.minAiExposurePct) failReasons.push('ai_exposure');
  if (metrics.avgDollarVolumeM < SCREENING_THRESHOLDS.minAvgDollarVolumeM) failReasons.push('liquidity');

  return {
    stock,
    metrics,
    scores,
    totalScore,
    passesScreen: failReasons.length === 0,
    failReasons,
    investmentThesis: generateThesis(stock, metrics),
    riskFactors: generateRisks(stock, metrics),
    actionSignal: computeActionSignal(totalScore, metrics.pctFrom52wHigh, metrics.revenueGrowthPct),
  };
}

function round(n: number): number {
  return Math.round(n * 10) / 10;
}
