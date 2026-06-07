import { Router, Request, Response } from 'express';
import { fetchAllStocks } from '../data/yahoo';
import { ALL_AI_STOCKS, getStocksByLayer, SCENARIOS, type RiskProfile } from '../data/stocks';
import { scoreStock } from '../quant/scoring';
import { runCorrelationAnalysis } from '../quant/correlation';
import { buildPriceTargets, generateScenarios, computePortfolioModel } from '../quant/pricing';
import { runBacktest } from '../quant/backtest';
import { createLLMProvider, buildAnalysisPrompt, RuleBasedProvider, type LLMConfig } from '../llm/provider';

const router = Router();

// Cache for scored results
let cachedScored: any[] = [];
let cachedCorrelation: any = null;
let lastFetchTime = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function getScoredData(forceRefresh = false) {
  const now = Date.now();
  if (!forceRefresh && cachedScored.length > 0 && (now - lastFetchTime) < CACHE_TTL) {
    return cachedScored;
  }

  const stockData = await fetchAllStocks();
  const scored = stockData
    .filter(s => s.metrics !== null)
    .map(s => scoreStock(s.stock, s.metrics!))
    .sort((a, b) => b.totalScore - a.totalScore);

  cachedScored = scored;
  lastFetchTime = now;
  return scored;
}

// GET /api/stocks - Get all scored stocks
router.get('/stocks', async (_req: Request, res: Response) => {
  try {
    const scored = await getScoredData();
    const layer = _req.query.layer ? parseInt(_req.query.layer as string) : undefined;
    const filtered = layer ? scored.filter(s => s.stock.layer === layer) : scored;

    res.json({
      count: filtered.length,
      timestamp: new Date(lastFetchTime).toISOString(),
      stocks: filtered.map(s => ({
        ticker: s.stock.ticker,
        name: s.stock.name,
        nameKr: s.stock.nameKr,
        layer: s.stock.layer,
        layerName: s.stock.layerName,
        subsegment: s.stock.subsegment,
        market: s.stock.market,
        region: s.stock.region,
        aiExposurePct: s.stock.aiExposurePct,
        price: s.metrics.currentPrice,
        marketCapB: Math.round(s.metrics.marketCapB * 10) / 10,
        revenueGrowthPct: Math.round(s.metrics.revenueGrowthPct * 10) / 10,
        fcfMarginPct: Math.round(s.metrics.fcfMarginPct * 10) / 10,
        forwardPE: Math.round(s.metrics.forwardPE * 10) / 10,
        epsGrowthPct: Math.round(s.metrics.epsGrowthPct * 10) / 10,
        roicPct: Math.round(s.metrics.roicPct * 10) / 10,
        price6mPct: Math.round(s.metrics.price6mPct * 10) / 10,
        price12mPct: Math.round(s.metrics.price12mPct * 10) / 10,
        pctFrom52wHigh: Math.round(s.metrics.pctFrom52wHigh * 10) / 10,
        beta: Math.round(s.metrics.beta * 10) / 10,
        scores: s.scores,
        totalScore: s.totalScore,
        passesScreen: s.passesScreen,
        failReasons: s.failReasons,
        actionSignal: s.actionSignal,
        investmentThesis: s.investmentThesis,
        riskFactors: s.riskFactors,
      })),
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/stocks/refresh - Force refresh stock data
router.post('/stocks/refresh', async (_req: Request, res: Response) => {
  try {
    const scored = await getScoredData(true);
    res.json({ success: true, count: scored.length, timestamp: new Date().toISOString() });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/correlation - Semiconductor correlation analysis
router.get('/correlation', async (_req: Request, res: Response) => {
  try {
    if (cachedCorrelation && (Date.now() - lastFetchTime) < CACHE_TTL) {
      return res.json(cachedCorrelation);
    }

    const report = await runCorrelationAnalysis();
    cachedCorrelation = report;
    res.json(report);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/price-targets - Price determination model
router.get('/price-targets', async (_req: Request, res: Response) => {
  try {
    const scored = await getScoredData();
    const correlationReport = cachedCorrelation || undefined;
    const priceTargets = buildPriceTargets(scored, correlationReport);
    const scenarios = generateScenarios();
    const portfolio = computePortfolioModel(priceTargets, scenarios);

    res.json(portfolio);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/scenarios - Investment scenarios by risk profile
router.get('/scenarios', (_req: Request, res: Response) => {
  const scenarios = generateScenarios();
  res.json({
    scenarios,
    riskProfiles: Object.entries(SCENARIOS).map(([key, config]) => ({
      id: key,
      ...config,
    })),
  });
});

// GET /api/strategy/:profile - Get strategy for a specific risk profile
router.get('/strategy/:profile', async (req: Request, res: Response) => {
  try {
    const profile = req.params.profile as RiskProfile;
    const scenarioConfig = SCENARIOS[profile];
    if (!scenarioConfig) {
      return res.status(400).json({ error: `Unknown profile: ${profile}. Use: conservative, moderate, aggressive, destructive` });
    }

    const scored = await getScoredData();
    const filtered = scored
      .filter(s => s.totalScore >= scenarioConfig.minScoreThreshold)
      .slice(0, 10);

    // Generate buy/sell/hold/avg_down signals with scenario-specific logic
    const signals = filtered.map(s => {
      let action = s.actionSignal;
      let positionPct = scenarioConfig.positionSizePct;

      // Adjust for scenario
      if (profile === 'destructive' && s.stock.layer === 1) positionPct *= 2; // leverage on Layer 1
      if (profile === 'moderate' && s.totalScore >= 85) action = 'STRONG_BUY';

      return {
        ticker: s.stock.ticker,
        name: s.stock.name,
        nameKr: s.stock.nameKr,
        layer: s.stock.layer,
        score: s.totalScore,
        action,
        positionSizePct: Math.round(positionPct * 10) / 10,
        currentPrice: s.metrics.currentPrice,
        stopLoss: Math.round(s.metrics.currentPrice * (1 + scenarioConfig.stopLossPct / 100) * 100) / 100,
        avgDownPrice: Math.round(s.metrics.currentPrice * (1 + scenarioConfig.avgDownThresholdPct / 100) * 100) / 100,
        thesis: s.investmentThesis,
        risks: s.riskFactors,
      };
    });

    // Layer allocation
    const layerAllocation: Record<number, { stocks: number; weightPct: number; tickers: string[] }> = {};
    for (const s of signals) {
      if (!layerAllocation[s.layer]) {
        layerAllocation[s.layer] = { stocks: 0, weightPct: 0, tickers: [] };
      }
      layerAllocation[s.layer].stocks++;
      layerAllocation[s.layer].weightPct += s.positionSizePct;
      layerAllocation[s.layer].tickers.push(s.ticker);
    }

    const cashReserve = scenarioConfig.cashReservePct;

    res.json({
      profile: scenarioConfig,
      signals,
      layerAllocation,
      cashReservePct: cashReserve,
      totalAllocatedPct: signals.reduce((sum, s) => sum + s.positionSizePct, 0),
      disclaimer: 'This is educational/research simulation. Not investment advice.',
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/backtest - Run backtest
router.get('/backtest', async (req: Request, res: Response) => {
  try {
    const profile = (req.query.profile as RiskProfile) || 'moderate';
    const scenarioConfig = SCENARIOS[profile];
    const tickers = ['NVDA', 'TSM', 'MSFT', 'AVGO', 'META', 'GOOGL', 'ASML', 'VRT', 'ANET', 'PLTR'];

    const result = await runBacktest(tickers, scenarioConfig, profile, 100000);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/llm/analyze - LLM analysis
router.post('/llm/analyze', async (req: Request, res: Response) => {
  try {
    const { provider: providerName = 'claude', apiKey: bodyApiKey, language } = req.body as {
      provider?: string;
      apiKey?: string;
      language?: string;
    };

    // Resolve API key: request body > env var > null (falls back to rule-based)
    const envKey = providerName === 'claude' ? process.env.CLAUDE_API_KEY : process.env.DEEPSEEK_API_KEY;
    const apiKey = bodyApiKey || envKey;

    const scored = await getScoredData();
    const correlationReport = cachedCorrelation || null;

    // Build simplified data for prompt
    const stockData = scored.map(s => ({
      ticker: s.stock.ticker,
      name: s.stock.name,
      layer: s.stock.layer,
      score: s.totalScore,
      action: s.actionSignal,
      price: s.metrics.currentPrice,
      thesis: s.investmentThesis,
      risks: s.riskFactors,
    }));

    const correlationData = correlationReport ? {
      pairs: correlationReport.pairs.slice(0, 10),
      lagAnalysis: correlationReport.lagAnalysis.slice(0, 5),
    } : null;

    const scenarioData = generateScenarios();
    const prompt = buildAnalysisPrompt(stockData, correlationData, scenarioData);

    // Append language instruction
    const langInstruction = language === 'ko'
      ? '\n\nIMPORTANT: Respond in Korean (한국어). All output text must be in Korean.'
      : '\n\nIMPORTANT: Respond in English. All output text must be in English.';

    let analysis: string;

    if (apiKey && (providerName === 'claude' || providerName === 'deepseek')) {
      const config: LLMConfig = { provider: providerName as 'claude' | 'deepseek', apiKey };
      const llmProvider = createLLMProvider(config);
      analysis = await llmProvider.generateAnalysis(prompt + langInstruction);
    } else {
      const ruleBased = new RuleBasedProvider(JSON.stringify({ stocks: stockData }));
      analysis = await ruleBased.generateAnalysis(prompt + langInstruction);
    }

    res.json({
      provider: apiKey ? providerName : 'rule-based',
      analysis: JSON.parse(analysis),
    });
  } catch (err: any) {
    // Fallback to rule-based on error
    try {
      const scored = await getScoredData();
      const stockData = scored.map(s => ({
        ticker: s.stock.ticker, name: s.stock.name, layer: s.stock.layer,
        score: s.totalScore, action: s.actionSignal, price: s.metrics.currentPrice,
        thesis: s.investmentThesis, risks: s.riskFactors,
      }));
      const ruleBased2 = new RuleBasedProvider(JSON.stringify({ stocks: stockData }));
      const analysis2 = await ruleBased2.generateAnalysis('');
      res.json({ provider: 'rule-based', analysis: JSON.parse(analysis2), note: 'API fallback used' });
    } catch (fallbackErr: any) {
      res.status(500).json({ error: err.message });
    }
  }
});

// GET /api/health - Health check
router.get('/health', (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    stocksCached: cachedScored.length,
    correlationCached: cachedCorrelation !== null,
    availableProviders: ['claude', 'deepseek', 'rule-based'],
  });
});

export default router;
