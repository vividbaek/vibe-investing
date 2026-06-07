import _YahooFinance from 'yahoo-finance2';
import { ExtendedStockMeta, ALL_AI_STOCKS } from './stocks';

const yahooFinance = new (_YahooFinance as any)() as any;

export interface FetchMetrics {
  ticker: string;
  currentPrice: number;
  marketCapB: number;
  avgDollarVolumeM: number;
  revenueGrowthPct: number;
  fcfMarginPct: number;
  forwardPE: number;
  epsGrowthPct: number;
  roicPct: number;
  price6mPct: number;
  price12mPct: number;
  pctFrom52wHigh: number;
  dividendYield: number;
  beta: number;
}

export interface FetchResult {
  metrics: FetchMetrics | null;
  error: string | null;
}

function safeNum(val: any): number {
  return typeof val === 'number' && isFinite(val) ? val : 0;
}

export async function fetchStockMetrics(ticker: string): Promise<FetchResult> {
  try {
    const quote: any = await yahooFinance.quote(ticker);
    if (!quote || !quote.regularMarketPrice) {
      return { metrics: null, error: `No market data for ${ticker}` };
    }

    let quoteSummary: any = null;
    try {
      quoteSummary = await yahooFinance.quoteSummary(ticker, {
        modules: ['defaultKeyStatistics', 'financialData', 'summaryDetail']
      });
    } catch {
      // quoteSummary might not be available for all tickers (e.g., Korean stocks)
    }

    const defaultStats: any = quoteSummary?.defaultKeyStatistics ?? {};
    const financialData: any = quoteSummary?.financialData ?? {};
    const summaryDetail: any = quoteSummary?.summaryDetail ?? {};

    const price = safeNum(quote.regularMarketPrice ?? quote.currentPrice);
    const marketCap = safeNum(quote.marketCap ?? 0);
    const avgVolume = safeNum(quote.averageDailyVolume3Month ?? quote.averageDailyVolume10Day ?? 0);
    const avgDollarVolume = (avgVolume * price) / 1e6;

    const revGrowth: number = safeNum(quote.revenueGrowth ?? 0) * 100;
    const fcf: number = safeNum(financialData.freeCashflow ?? 0);
    const rev: number = safeNum(financialData.totalRevenue ?? 1);
    const fcfMargin: number = rev > 0 ? (fcf / rev) * 100 : 0;
    const fwdPE: number = safeNum(summaryDetail.forwardPE ?? quote.forwardPE ?? 0);
    const epsGrowth: number = safeNum(quote.earningsGrowth ?? 0) * 100;
    const roic: number = safeNum(quote.returnOnEquity ?? 0) * 100;

    const price52wHigh: number = safeNum(quote.fiftyTwoWeekHigh ?? price);
    const price52wLow: number = safeNum(quote.fiftyTwoWeekLow ?? price);
    const pctFrom52wHigh: number = price52wHigh > 0 ? ((price / price52wHigh) - 1) * 100 : 0;

    const midPoint = (price52wHigh + price52wLow) / 2;
    const price6mPct: number = price > 0 ? ((price / midPoint) - 1) * 100 : 0;
    const price12mPct: number = price52wLow > 0 ? ((price / price52wLow) - 1) * 100 : 0;
    const dividendYield: number = safeNum(summaryDetail.dividendYield ?? 0) * 100;
    const beta: number = safeNum(defaultStats.beta ?? 1);

    return {
      metrics: {
        ticker,
        currentPrice: price,
        marketCapB: marketCap / 1e9,
        avgDollarVolumeM: avgDollarVolume,
        revenueGrowthPct: revGrowth,
        fcfMarginPct: fcfMargin,
        forwardPE: fwdPE,
        epsGrowthPct: epsGrowth,
        roicPct: roic,
        price6mPct,
        price12mPct,
        pctFrom52wHigh,
        dividendYield,
        beta,
      },
      error: null,
    };
  } catch (err: any) {
    return { metrics: null, error: `${ticker}: ${err.message || err}` };
  }
}

export async function fetchAllStocks(): Promise<{ stock: ExtendedStockMeta; metrics: FetchMetrics | null; error: string | null }[]> {
  const results = [];
  for (const stock of ALL_AI_STOCKS) {
    const result = await fetchStockMetrics(stock.ticker);
    results.push({ stock, ...result });
  }
  return results;
}

export async function fetchHistoricalData(tickers: string[], period: '1y' | '2y' | '5y' | '10y' = '2y'): Promise<Map<string, number[]>> {
  const priceMap = new Map<string, number[]>();

  for (const ticker of tickers) {
    try {
      const hist: any[] = await yahooFinance.historical(ticker, {
        period1: getStartDate(period),
        interval: '1wk',
      });
      const closes: number[] = hist
        .map((h: any) => safeNum(h.close))
        .filter((c: number) => c > 0);
      priceMap.set(ticker, closes);
    } catch {
      priceMap.set(ticker, []);
    }
  }

  return priceMap;
}

function getStartDate(period: string): string {
  const now = new Date();
  switch (period) {
    case '1y': return new Date(now.setFullYear(now.getFullYear() - 1)).toISOString().split('T')[0];
    case '2y': return new Date(now.setFullYear(now.getFullYear() - 2)).toISOString().split('T')[0];
    case '5y': return new Date(now.setFullYear(now.getFullYear() - 5)).toISOString().split('T')[0];
    case '10y': return new Date(now.setFullYear(now.getFullYear() - 10)).toISOString().split('T')[0];
    default: return new Date(now.setFullYear(now.getFullYear() - 2)).toISOString().split('T')[0];
  }
}
