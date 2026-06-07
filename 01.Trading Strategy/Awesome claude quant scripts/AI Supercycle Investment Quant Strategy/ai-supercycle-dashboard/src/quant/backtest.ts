// Backtesting Engine for AI Supercycle Strategy
// Tests buy/sell/hold/averaging-down strategies across historical data

import { fetchHistoricalData } from '../data/yahoo';
import { ScenarioConfig, SCENARIOS, type RiskProfile } from '../data/stocks';

export interface BacktestTrade {
  date: string;
  ticker: string;
  action: 'BUY' | 'SELL' | 'HOLD' | 'AVG_DOWN';
  price: number;
  shares: number;
  cashChange: number;
  reason: string;
}

export interface BacktestResult {
  scenario: string;
  riskProfile: RiskProfile;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalValue: number;
  totalReturnPct: number;
  cagr: number;
  maxDrawdownPct: number;
  sharpeRatio: number;
  beta: number;
  winRatePct: number;
  avgWinPct: number;
  avgLossPct: number;
  trades: BacktestTrade[];
  equityCurve: { date: string; value: number }[];
  holdings: { date: string; tickers: string[]; weights: number[] }[];
}

interface BacktestState {
  cash: number;
  positions: Map<string, { shares: number; avgCost: number }>;
  equity: number[];
  trades: BacktestTrade[];
  holdings: { date: string; tickers: string[]; weights: number[] }[];
  peak: number;
  maxDrawdown: number;
  wins: number;
  losses: number;
  totalWins: number;
  totalLosses: number;
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

function computeMaxDrawdown(equity: number[]): number {
  let peak = equity[0];
  let maxDD = 0;
  for (const val of equity) {
    if (val > peak) peak = val;
    const dd = (val - peak) / peak;
    if (dd < maxDD) maxDD = dd;
  }
  return maxDD * 100;
}

function computeSharpe(returns: number[]): number {
  if (returns.length < 2) return 0;
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((sum, r) => sum + (r - mean) ** 2, 0) / returns.length;
  const std = Math.sqrt(variance);
  return std === 0 ? 0 : (mean / std) * Math.sqrt(52); // annualized
}

function computeBeta(portfolioReturns: number[], benchmarkReturns: number[]): number {
  const minLen = Math.min(portfolioReturns.length, benchmarkReturns.length);
  const pRet = portfolioReturns.slice(-minLen);
  const bRet = benchmarkReturns.slice(-minLen);

  const meanP = pRet.reduce((a, b) => a + b, 0) / minLen;
  const meanB = bRet.reduce((a, b) => a + b, 0) / minLen;

  let cov = 0, varB = 0;
  for (let i = 0; i < minLen; i++) {
    cov += (pRet[i] - meanP) * (bRet[i] - meanB);
    varB += (bRet[i] - meanB) ** 2;
  }
  return varB === 0 ? 1 : cov / varB;
}

export async function runBacktest(
  tickers: string[],
  scenario: ScenarioConfig,
  riskProfile: RiskProfile,
  initialCapital: number = 100000,
): Promise<BacktestResult> {
  const priceMap = await fetchHistoricalData(tickers, '2y');
  const benchmarkPrices = (await fetchHistoricalData(['QQQ'], '2y')).get('QQQ') || [];

  // Find the common date range
  const validTickers = tickers.filter(t => (priceMap.get(t) || []).length >= 50);
  if (validTickers.length === 0) {
    return createEmptyResult(scenario, riskProfile, 'No data');
  }

  // Align all price series to the shortest common length
  const minLen = Math.min(...validTickers.map(t => (priceMap.get(t) || []).length));
  const alignedPrices = new Map<string, number[]>();
  for (const t of validTickers) {
    const prices = priceMap.get(t) || [];
    alignedPrices.set(t, prices.slice(-minLen));
  }

  const state: BacktestState = {
    cash: initialCapital,
    positions: new Map(),
    equity: [initialCapital],
    trades: [],
    holdings: [],
    peak: initialCapital,
    maxDrawdown: 0,
    wins: 0,
    losses: 0,
    totalWins: 0,
    totalLosses: 0,
  };

  const weeklyDates: string[] = [];
  const now = new Date();
  for (let i = 0; i < minLen; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - (minLen - 1 - i) * 7);
    weeklyDates.push(d.toISOString().split('T')[0]);
  }

  // Simple momentum-based strategy
  for (let week = 0; week < minLen; week++) {
    // Rebalance check using scenario config (convert days to weeks)
    const rebalanceWeeks = Math.max(1, Math.round(scenario.rebalanceFreqDays / 7));
    const shouldRebalance = week % rebalanceWeeks === 0;

    if (shouldRebalance && week > 0) {
      // Score each stock based on trailing data
      const signals: { ticker: string; price: number; signal: 'BUY' | 'SELL' | 'HOLD' | 'AVG_DOWN'; score: number; momentum: number }[] = [];

      for (const ticker of validTickers) {
        const prices = alignedPrices.get(ticker) || [];
        if (prices.length <= week + 20) continue;

        const currentPrice = prices[week];
        const lookback4 = prices[Math.max(0, week - 4)];
        const lookback12 = prices[Math.max(0, week - 12)];
        const lookback26 = prices[Math.max(0, week - 26)];
        const lookback52 = prices[Math.max(0, week - 52)];

        const momentum4w = ((currentPrice / lookback4) - 1) * 100;
        const momentum12w = ((currentPrice / lookback12) - 1) * 100;
        const momentum26w = ((currentPrice / lookback26) - 1) * 100;

        // Peak from last 52 weeks
        const peak52 = Math.max(...prices.slice(Math.max(0, week - 52), week + 1));
        const pctFromPeak = ((currentPrice / peak52) - 1) * 100;

        // Simple scoring for backtest
        let btScore = 50;
        if (momentum4w > 0) btScore += 10;
        if (momentum12w > 5) btScore += 10;
        if (momentum26w > 10) btScore += 10;

        // Determine signal
        let signal: 'BUY' | 'SELL' | 'HOLD' | 'AVG_DOWN' = 'HOLD';
        if (btScore >= 75 && momentum4w > 0) signal = 'BUY';
        else if (btScore >= 60 && pctFromPeak <= -15 && momentum52w() > 5) signal = 'AVG_DOWN';
        else if (btScore < 40) signal = 'SELL';

        // 52-week momentum
        function momentum52w(): number {
          if (week < 52) return 5;
          return ((currentPrice / prices[week - 52]) - 1) * 100;
        }

        signals.push({ ticker, price: currentPrice, signal, score: btScore, momentum: momentum12w });
      }

      // Sort by score descending
      signals.sort((a, b) => b.score - a.score);

      // Calculate target number of positions
      const positionSizePct = scenario.positionSizePct / 100;
      const targetNumPositions = Math.floor((1 - scenario.cashReservePct / 100) / (scenario.positionSizePct / 100));

      const buyCandidates = signals.filter(s => s.signal === 'BUY' || s.signal === 'AVG_DOWN').slice(0, targetNumPositions);

      // Sell everything not in buy list
      const buyTickers = new Set(buyCandidates.map(s => s.ticker));
      for (const [ticker, pos] of state.positions) {
        if (!buyTickers.has(ticker)) {
          const price = alignedPrices.get(ticker)?.[week] || 0;
          if (price > 0 && pos.shares > 0) {
            const proceeds = price * pos.shares;
            const pnl = ((price / pos.avgCost) - 1) * 100;

            state.cash += proceeds;
            state.trades.push({
              date: weeklyDates[week],
              ticker,
              action: 'SELL',
              price,
              shares: pos.shares,
              cashChange: proceeds,
              reason: pnl > 0 ? 'Take profit' : 'Stop loss / rebalance',
            });

            if (pnl > 0) {
              state.wins++;
              state.totalWins += pnl;
            } else {
              state.losses++;
              state.totalLosses += pnl;
            }

            state.positions.delete(ticker);
          }
        }
      }

      // Buy / avg-down
      for (const candidate of buyCandidates) {
        const existing = state.positions.get(candidate.ticker);
        const price = candidate.price;

        if (existing) {
          // Averaging down check
          if (candidate.signal === 'AVG_DOWN' && scenario.avgDownEnabled) {
            const drawdownFromCost = ((price / existing.avgCost) - 1) * 100;
            if (drawdownFromCost <= scenario.avgDownThresholdPct) {
              const addAmount = Math.min(state.cash * 0.15, price * 10);
              const addShares = Math.floor(addAmount / price);
              if (addShares > 0) {
                existing.avgCost = ((existing.avgCost * existing.shares) + (price * addShares)) / (existing.shares + addShares);
                existing.shares += addShares;
                state.cash -= price * addShares;
                state.trades.push({
                  date: weeklyDates[week],
                  ticker: candidate.ticker,
                  action: 'AVG_DOWN',
                  price,
                  shares: addShares,
                  cashChange: -(price * addShares),
                  reason: `Averaging down (drawdown ${drawdownFromCost.toFixed(1)}%)`,
                });
              }
            }
          }
        } else {
          // New position
          const allocation = state.cash * positionSizePct;
          const shares = Math.floor(allocation / price);
          if (shares > 0 && allocation <= state.cash) {
            state.positions.set(candidate.ticker, { shares, avgCost: price });
            state.cash -= price * shares;
            state.trades.push({
              date: weeklyDates[week],
              ticker: candidate.ticker,
              action: 'BUY',
              price,
              shares,
              cashChange: -(price * shares),
              reason: `Score: ${candidate.score}, signal: ${candidate.signal}`,
            });
          }
        }
      }
    }

    // Compute current equity after price changes
    let positionsValue = 0;
    for (const [ticker, pos] of state.positions) {
      const currentPrice = alignedPrices.get(ticker)?.[week] || 0;
      positionsValue += currentPrice * pos.shares;
    }
    const totalEquity = state.cash + positionsValue;
    state.equity.push(totalEquity);

    if (totalEquity > state.peak) state.peak = totalEquity;
    const drawdown = (totalEquity - state.peak) / state.peak;
    if (drawdown < state.maxDrawdown) state.maxDrawdown = drawdown;

    // Track holdings
    const holdingTickers: string[] = [];
    const holdingWeights: number[] = [];
    for (const [ticker, pos] of state.positions) {
      const val = (alignedPrices.get(ticker)?.[week] || 0) * pos.shares;
      holdingTickers.push(ticker);
      holdingWeights.push(totalEquity > 0 ? (val / totalEquity) * 100 : 0);
    }
    state.holdings.push({ date: weeklyDates[week], tickers: holdingTickers, weights: holdingWeights });
  }

  // Final metrics
  const totalTrades = state.wins + state.losses;
  const equityReturns = computeReturns(state.equity);
  const benchmarkReturns = benchmarkPrices.length > 0 ? computeReturns(benchmarkPrices.slice(-minLen)) : [];
  const totalReturn = ((state.equity[state.equity.length - 1] / initialCapital) - 1) * 100;
  const yearsHeld = minLen / 52;
  const cagr = yearsHeld > 0 ? (((state.equity[state.equity.length - 1] / initialCapital) ** (1 / yearsHeld)) - 1) * 100 : 0;

  return {
    scenario: scenario.name,
    riskProfile,
    startDate: weeklyDates[0],
    endDate: weeklyDates[weeklyDates.length - 1],
    initialCapital,
    finalValue: Math.round(state.equity[state.equity.length - 1] * 100) / 100,
    totalReturnPct: Math.round(totalReturn * 10) / 10,
    cagr: Math.round(cagr * 10) / 10,
    maxDrawdownPct: Math.round(state.maxDrawdown * 1000) / 10,
    sharpeRatio: Math.round(computeSharpe(equityReturns) * 100) / 100,
    beta: Math.round(computeBeta(equityReturns, benchmarkReturns) * 100) / 100,
    winRatePct: totalTrades > 0 ? Math.round((state.wins / totalTrades) * 100) : 0,
    avgWinPct: state.wins > 0 ? Math.round((state.totalWins / state.wins) * 10) / 10 : 0,
    avgLossPct: state.losses > 0 ? Math.round((state.totalLosses / state.losses) * 10) / 10 : 0,
    trades: state.trades.slice(-20), // last 20 trades for display
    equityCurve: state.equity.map((v, i) => ({ date: weeklyDates[Math.min(i, weeklyDates.length - 1)], value: Math.round(v * 100) / 100 })),
    holdings: state.holdings.slice(-10),
  };
}

function createEmptyResult(scenario: ScenarioConfig, riskProfile: RiskProfile, reason: string): BacktestResult {
  return {
    scenario: scenario.name,
    riskProfile,
    startDate: '',
    endDate: '',
    initialCapital: 0,
    finalValue: 0,
    totalReturnPct: 0,
    cagr: 0,
    maxDrawdownPct: 0,
    sharpeRatio: 0,
    beta: 0,
    winRatePct: 0,
    avgWinPct: 0,
    avgLossPct: 0,
    trades: [],
    equityCurve: [],
    holdings: [],
  };
}
