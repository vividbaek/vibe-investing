// Semiconductor Correlation Engine
// Analyzes relationships between Samsung, SK Hynix, Micron and broader AI plays

import { fetchHistoricalData } from '../data/yahoo';
import * as math from 'mathjs';

export interface CorrelationPair {
  tickerA: string;
  nameA: string;
  tickerB: string;
  nameB: string;
  correlation: number;
  strength: 'strong_positive' | 'moderate_positive' | 'weak' | 'moderate_negative' | 'strong_negative';
}

export interface LagAnalysis {
  leader: string;
  follower: string;
  bestLagWeeks: number;
  peakCorrelation: number;
  description: string;
}

export interface SemiCorrelationReport {
  pairs: CorrelationPair[];
  lagAnalysis: LagAnalysis[];
  hbmCorrelationMatrix: number[][];
  dramPriceIndex: number[];
  timestamp: string;
}

function computePearsonCorrelation(a: number[], b: number[]): number {
  const minLen = Math.min(a.length, b.length);
  if (minLen < 10) return 0;
  const x = a.slice(-minLen);
  const y = b.slice(-minLen);

  const meanX = math.mean(x) as number;
  const meanY = math.mean(y) as number;
  const diffX = x.map(v => v - meanX);
  const diffY = y.map(v => v - meanY);
  const sumXY = math.sum(diffX.map((v, i) => v * diffY[i])) as number;
  const sumX2 = math.sum(diffX.map(v => v * v)) as number;
  const sumY2 = math.sum(diffY.map(v => v * v)) as number;
  const denom = Math.sqrt(sumX2 * sumY2);

  return denom === 0 ? 0 : sumXY / denom;
}

function computeReturns(prices: number[]): number[] {
  const returns: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    if (prices[i - 1] > 0) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }
  }
  return returns;
}

function findBestLag(leaderPrices: number[], followerPrices: number[], maxWeeks = 12): LagAnalysis {
  const followerReturns = computeReturns(followerPrices);
  let bestLag = 0;
  let peakCorr = -1;

  for (let lag = 0; lag <= maxWeeks; lag++) {
    const leaderReturns = computeReturns(leaderPrices.slice(0, -lag || undefined));
    const followerSliced = computeReturns(followerPrices.slice(lag));

    const minLen = Math.min(leaderReturns.length, followerSliced.length);
    if (minLen < 10) continue;

    const corr = computePearsonCorrelation(
      leaderReturns.slice(-minLen),
      followerSliced.slice(-minLen)
    );
    if (corr > peakCorr) {
      peakCorr = corr;
      bestLag = lag;
    }
  }

  return { leader: '', follower: '', bestLagWeeks: bestLag, peakCorrelation: peakCorr, description: '' };
}

function interpretCorrelation(corr: number): CorrelationPair['strength'] {
  if (corr >= 0.7) return 'strong_positive';
  if (corr >= 0.4) return 'moderate_positive';
  if (corr >= -0.4) return 'weak';
  if (corr >= -0.7) return 'moderate_negative';
  return 'strong_negative';
}

export async function runCorrelationAnalysis(): Promise<SemiCorrelationReport> {
  // Key semiconductors: Korean + US
  const semis = [
    { ticker: '005930.KS', name: 'Samsung Electronics' },
    { ticker: '000660.KS', name: 'SK Hynix' },
    { ticker: 'MU', name: 'Micron Technology' },
    { ticker: 'NVDA', name: 'NVIDIA' },
    { ticker: 'TSM', name: 'TSMC' },
    { ticker: 'ASML', name: 'ASML' },
    { ticker: 'AVGO', name: 'Broadcom' },
    { ticker: 'AMD', name: 'AMD' },
  ];

  const tickers = semis.map(s => s.ticker);
  const priceMap = await fetchHistoricalData(tickers, '2y');

  // Compute correlation matrix
  const pricesList = tickers.map(t => priceMap.get(t) || []);
  const n = tickers.length;
  const hbmMatrix: number[][] = Array.from({ length: n }, () => Array(n).fill(0));

  // Correlation pairs
  const pairs: CorrelationPair[] = [];
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const returnsA = computeReturns(pricesList[i]);
      const returnsB = computeReturns(pricesList[j]);
      const corr = computePearsonCorrelation(returnsA, returnsB);
      hbmMatrix[i][j] = corr;
      hbmMatrix[j][i] = corr;

      pairs.push({
        tickerA: semis[i].ticker,
        nameA: semis[i].name,
        tickerB: semis[j].ticker,
        nameB: semis[j].name,
        correlation: Math.round(corr * 1000) / 1000,
        strength: interpretCorrelation(corr),
      });
    }
  }

  // Lag analysis: which semiconductor leads?
  const lagResults: LagAnalysis[] = [];
  const keyRelations = [
    { leader: semis[2], follower: semis[0] },  // Micron -> Samsung
    { leader: semis[3], follower: semis[1] },  // NVIDIA -> SK Hynix
    { leader: semis[3], follower: semis[2] },  // NVIDIA -> Micron
    { leader: semis[3], follower: semis[0] },  // NVIDIA -> Samsung
    { leader: semis[0], follower: semis[1] },  // Samsung -> SK Hynix
    { leader: semis[2], follower: semis[1] },  // Micron -> SK Hynix
    { leader: semis[5], follower: semis[0] },  // ASML -> Samsung
    { leader: semis[5], follower: semis[3] },  // ASML -> NVIDIA
  ];

  for (const rel of keyRelations) {
    const leaderPrices = priceMap.get(rel.leader.ticker) || [];
    const followerPrices = priceMap.get(rel.follower.ticker) || [];

    if (leaderPrices.length < 20 || followerPrices.length < 20) continue;

    const lag = findBestLag(leaderPrices, followerPrices, 12);
    lag.leader = rel.leader.name;
    lag.follower = rel.follower.name;
    lag.peakCorrelation = Math.round(lag.peakCorrelation * 1000) / 1000;

    if (lag.bestLagWeeks === 0) {
      lag.description = `${rel.leader.name} and ${rel.follower.name} move simultaneously (concurrent)`;
    } else {
      lag.description = `${rel.leader.name} leads ${rel.follower.name} by ${lag.bestLagWeeks} week(s) (corr: ${lag.peakCorrelation})`;
    }

    lagResults.push(lag);
  }

  // Sort by peak correlation descending
  lagResults.sort((a, b) => b.peakCorrelation - a.peakCorrelation);

  // DRAM price index: proxy from average of Samsung + SK Hynix + Micron
  const samsungPrices = priceMap.get('005930.KS') || [];
  const skhynixPrices = priceMap.get('000660.KS') || [];
  const micronPrices = priceMap.get('MU') || [];
  const minLen = Math.min(samsungPrices.length, skhynixPrices.length, micronPrices.length);

  const dramIndex: number[] = [];
  for (let i = 0; i < minLen; i++) {
    const avg = (samsungPrices[i] + skhynixPrices[i] + micronPrices[i]) / 3;
    dramIndex.push(Math.round(avg * 100) / 100);
  }

  return {
    pairs,
    lagAnalysis: lagResults,
    hbmCorrelationMatrix: hbmMatrix,
    dramPriceIndex: dramIndex,
    timestamp: new Date().toISOString(),
  };
}
