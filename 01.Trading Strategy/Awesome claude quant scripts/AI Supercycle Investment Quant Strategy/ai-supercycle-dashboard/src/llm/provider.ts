// LLM Provider Interface & Implementations: Claude + DeepSeek
// Generates AI Supercycle investment analysis using LLM prompting

export interface LLMProvider {
  name: string;
  generateAnalysis(prompt: string): Promise<string>;
}

export interface LLMConfig {
  provider: 'claude' | 'deepseek';
  apiKey: string;
}

const AI_SUPERCYCLE_PROMPT_TEMPLATE = `
You are a portfolio manager and Head of AI Infrastructure Research at a top-tier quant hedge fund.
Analyze the following AI Supercycle stock data and generate investment recommendations.

=== CURRENT PORTFOLIO DATA ===
{{DATA}}

=== INSTRUCTIONS ===
Provide the following analysis in JSON format:

{
  "marketSummary": "Brief AI supercycle market assessment (2-3 sentences)",
  "topPicks": [
    { "ticker": "...", "action": "BUY|SELL|HOLD|AVG_DOWN", "confidence": 1-100, "rationale": "..." }
  ],
  "layerAnalysis": {
    "layer1": { "sentiment": "bullish|neutral|bearish", "outlook": "..." },
    "layer2": { "sentiment": "bullish|neutral|bearish", "outlook": "..." },
    "layer3": { "sentiment": "bullish|neutral|bearish", "outlook": "..." },
    "layer4": { "sentiment": "bullish|neutral|bearish", "outlook": "..." }
  },
  "scenarioProjections": {
    "conservative": { "action": "..." },
    "moderate": { "action": "..." },
    "aggressive": { "action": "..." },
    "destructive": { "action": "..." }
  },
  "riskAlerts": ["alert1", "alert2"],
  "hbmDramOutlook": "HBM/DRAM specific outlook for Samsung, SK Hynix, Micron"
}

Respond ONLY with valid JSON, no additional text.`;

export class ClaudeProvider implements LLMProvider {
  name = 'Claude';
  private apiKey: string;
  private baseUrl = 'https://api.anthropic.com/v1/messages';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async generateAnalysis(prompt: string): Promise<string> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4096,
        messages: [{ role: 'user', content: prompt }],
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Claude API error ${response.status}: ${err}`);
    }

    const data = await response.json() as any;
    return data.content?.[0]?.text || JSON.stringify(data);
  }
}

export class DeepSeekProvider implements LLMProvider {
  name = 'DeepSeek';
  private apiKey: string;
  private baseUrl = 'https://api.deepseek.com/v1/chat/completions';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async generateAnalysis(prompt: string): Promise<string> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 4096,
        temperature: 0.3,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`DeepSeek API error ${response.status}: ${err}`);
    }

    const data = await response.json() as any;
    return data.choices?.[0]?.message?.content || JSON.stringify(data);
  }
}

// Rule-based LLM fallback when API keys are not available
export class RuleBasedProvider implements LLMProvider {
  name = 'Rule-Based Engine';
  private scoredData: string;

  constructor(scoredData: string) {
    this.scoredData = scoredData;
  }

  async generateAnalysis(prompt: string): Promise<string> {
    // Parse the data to generate rule-based analysis
    const data = JSON.parse(this.scoredData || '{"stocks":[]}');
    const stocks = data.stocks || [];

    const topPicks = stocks
      .filter((s: any) => s.totalScore >= 80)
      .slice(0, 5)
      .map((s: any) => ({
        ticker: s.ticker,
        action: s.totalScore >= 90 ? 'STRONG_BUY' : s.totalScore >= 80 ? 'BUY' : 'HOLD',
        confidence: Math.min(Math.round(s.totalScore), 95),
        rationale: s.investmentThesis || 'AI supercycle beneficiary',
      }));

    const layerScores = { layer1: [], layer2: [], layer3: [], layer4: [] } as Record<string, number[]>;
    for (const s of stocks) {
      const key = `layer${s.layer}`;
      if (layerScores[key]) layerScores[key].push(s.totalScore);
    }

    const layerAnalysis: Record<string, any> = {};
    for (const [key, scores] of Object.entries(layerScores)) {
      const avg = scores.length > 0 ? scores.reduce((a: number, b: number) => a + b, 0) / scores.length : 0;
      const sentiment = avg >= 75 ? 'bullish' : avg >= 55 ? 'neutral' : 'bearish';
      layerAnalysis[key.replace('layer', 'layer')] = {
        sentiment,
        outlook: avg >= 75 ? 'Strong AI demand. Favorable positioning.' : avg >= 55 ? 'Moderate outlook. Selective exposure advised.' : 'Headwinds. Reduce exposure.',
      };
    }

    // Fix layerAnalysis keys
    const fixedLayerAnalysis: Record<string, any> = {};
    for (const [key, val] of Object.entries(layerAnalysis)) {
      const layerNum = key.replace('layer', 'layer');
      if (layerNum === 'layer1') fixedLayerAnalysis['layer1'] = val;
      else if (layerNum === 'layer2') fixedLayerAnalysis['layer2'] = val;
      else if (layerNum === 'layer3') fixedLayerAnalysis['layer3'] = val;
      else if (layerNum === 'layer4') fixedLayerAnalysis['layer4'] = val;
    }

    return JSON.stringify({
      marketSummary: `AI supercycle remains intact with ${stocks.length} stocks analyzed. Top picks concentrated in Layer 1 (Foundation) and Layer 2 (Infrastructure). HBM/DRAM demand driven by GPU proliferation.`,
      topPicks: topPicks.length > 0 ? topPicks : [
        { ticker: 'NVDA', action: 'BUY', confidence: 90, rationale: 'GPU cycle leader' },
        { ticker: 'TSM', action: 'BUY', confidence: 88, rationale: 'Foundry monopoly' },
        { ticker: 'MSFT', action: 'BUY', confidence: 85, rationale: 'Azure AI growth' },
      ],
      layerAnalysis: fixedLayerAnalysis,
      scenarioProjections: {
        conservative: { action: 'Focus on Layer 1 top-3 (NVDA, TSM, AVGO). 20% cash. Tight -10% stops.' },
        moderate: { action: 'Equal-weight Layer 1-2. 10% cash. -15% stops. Rebalance quarterly.' },
        aggressive: { action: 'Full Layer 1-4 exposure. 5% cash. -22% stops. Monthly rebalance.' },
        destructive: { action: 'Maximum Layer 1 leverage. No cash. -30% stops. Accept -50% drawdown. Bi-weekly rebalance.' },
      },
      riskAlerts: [
        'Monitor GPU ASP trends for cycle peak signal',
        'Watch hyperscaler Capex guidance revisions',
        'Geopolitical risk: Taiwan + Korea exposure',
        'HBM oversupply risk if DRAM cycle turns',
      ],
      hbmDramOutlook: 'HBM3E supply tight through mid-2026. Samsung + SK Hynix dominant (>90% share). Micron gaining share. DRAM pricing cycle approaching peak — monitor closely for inflection.',
    });
  }
}

export function createLLMProvider(config: LLMConfig): LLMProvider {
  switch (config.provider) {
    case 'claude':
      return new ClaudeProvider(config.apiKey);
    case 'deepseek':
      return new DeepSeekProvider(config.apiKey);
    default:
      throw new Error(`Unknown LLM provider: ${config.provider}`);
  }
}

export function buildAnalysisPrompt(stockData: any, correlationData: any, scenarioData: any): string {
  const dataJson = JSON.stringify({
    stocks: stockData,
    correlations: correlationData,
    scenarios: scenarioData,
    timestamp: new Date().toISOString(),
  }, null, 2);

  return AI_SUPERCYCLE_PROMPT_TEMPLATE.replace('{{DATA}}', dataJson);
}
