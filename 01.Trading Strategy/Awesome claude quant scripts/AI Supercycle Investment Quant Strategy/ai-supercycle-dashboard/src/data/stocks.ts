// AI Supercycle Stock Universe - 4 Layer AI Value Chain + Korean Semiconductor names
// Based on: AI Super Cycle Quant Strategy by Dennis Kim (gameworkerkim/vibe-investing)

export interface StockMeta {
  ticker: string;
  name: string;
  nameKr: string;
  layer: 1 | 2 | 3 | 4;
  layerName: string;
  subsegment: string;
  aiExposurePct: number;
  market: 'US' | 'KR';
  region: string;
}

export interface ExtendedStockMeta extends StockMeta {
  // Korean semiconductor correlation fields
  hbmSharePct?: number;
  dramSharePct?: number;
  foundryProcess?: string;
}

// Layer 1: Foundation - Semiconductors, Equipment, Memory
export const LAYER1_FOUNDATION: ExtendedStockMeta[] = [
  { ticker: 'NVDA', name: 'NVIDIA', nameKr: '엔비디아', layer: 1, layerName: 'Foundation', subsegment: 'GPU', aiExposurePct: 90, market: 'US', region: 'US' },
  { ticker: 'AVGO', name: 'Broadcom', nameKr: '브로드컴', layer: 1, layerName: 'Foundation', subsegment: 'ASIC/Network', aiExposurePct: 60, market: 'US', region: 'US' },
  { ticker: 'TSM', name: 'TSMC (ADR)', nameKr: 'TSMC', layer: 1, layerName: 'Foundation', subsegment: 'Foundry', aiExposurePct: 50, market: 'US', region: 'Taiwan', foundryProcess: '3nm/2nm' },
  { ticker: 'ASML', name: 'ASML', nameKr: 'ASML', layer: 1, layerName: 'Foundation', subsegment: 'EUV Equipment', aiExposurePct: 45, market: 'US', region: 'Netherlands' },
  { ticker: 'AMD', name: 'AMD', nameKr: 'AMD', layer: 1, layerName: 'Foundation', subsegment: 'GPU/CPU', aiExposurePct: 40, market: 'US', region: 'US' },
  { ticker: 'MU', name: 'Micron Technology', nameKr: '마이크론', layer: 1, layerName: 'Foundation', subsegment: 'HBM/DRAM/NAND', aiExposurePct: 45, market: 'US', region: 'US', hbmSharePct: 25, dramSharePct: 23 },
  { ticker: 'LRCX', name: 'Lam Research', nameKr: '램리서치', layer: 1, layerName: 'Foundation', subsegment: 'Etch Equipment', aiExposurePct: 35, market: 'US', region: 'US' },
  { ticker: 'AMAT', name: 'Applied Materials', nameKr: '어플라이드머티리얼즈', layer: 1, layerName: 'Foundation', subsegment: 'Semi Equipment', aiExposurePct: 35, market: 'US', region: 'US' },
  { ticker: 'KLAC', name: 'KLA Corporation', nameKr: 'KLA', layer: 1, layerName: 'Foundation', subsegment: 'Process Control', aiExposurePct: 35, market: 'US', region: 'US' },
  { ticker: 'MRVL', name: 'Marvell Technology', nameKr: '마벨', layer: 1, layerName: 'Foundation', subsegment: 'Custom Silicon', aiExposurePct: 50, market: 'US', region: 'US' },
  { ticker: 'INTC', name: 'Intel', nameKr: '인텔', layer: 1, layerName: 'Foundation', subsegment: 'Foundry/CPU', aiExposurePct: 20, market: 'US', region: 'US', foundryProcess: '18A/14A' },
  // Korean semiconductor - Samsung Electronics
  { ticker: '005930.KS', name: 'Samsung Electronics', nameKr: '삼성전자', layer: 1, layerName: 'Foundation', subsegment: 'HBM/DRAM/Foundry', aiExposurePct: 40, market: 'KR', region: 'Korea', hbmSharePct: 35, dramSharePct: 41, foundryProcess: '3nm GAA' },
  // Korean semiconductor - SK Hynix
  { ticker: '000660.KS', name: 'SK Hynix', nameKr: 'SK하이닉스', layer: 1, layerName: 'Foundation', subsegment: 'HBM/DRAM', aiExposurePct: 55, market: 'KR', region: 'Korea', hbmSharePct: 53, dramSharePct: 35 },
];

// Layer 2: Infrastructure - Hyperscalers, Cloud
export const LAYER2_INFRA: ExtendedStockMeta[] = [
  { ticker: 'MSFT', name: 'Microsoft', nameKr: '마이크로소프트', layer: 2, layerName: 'Infrastructure', subsegment: 'Azure AI', aiExposurePct: 35, market: 'US', region: 'US' },
  { ticker: 'GOOGL', name: 'Alphabet', nameKr: '알파벳', layer: 2, layerName: 'Infrastructure', subsegment: 'GCP/TPU', aiExposurePct: 30, market: 'US', region: 'US' },
  { ticker: 'META', name: 'Meta Platforms', nameKr: '메타', layer: 2, layerName: 'Infrastructure', subsegment: 'Ad AI', aiExposurePct: 40, market: 'US', region: 'US' },
  { ticker: 'AMZN', name: 'Amazon', nameKr: '아마존', layer: 2, layerName: 'Infrastructure', subsegment: 'AWS', aiExposurePct: 25, market: 'US', region: 'US' },
  { ticker: 'ORCL', name: 'Oracle', nameKr: '오라클', layer: 2, layerName: 'Infrastructure', subsegment: 'OCI', aiExposurePct: 30, market: 'US', region: 'US' },
];

// Layer 3: Enablers - Power, Cooling, Network
export const LAYER3_ENABLERS: ExtendedStockMeta[] = [
  { ticker: 'VRT', name: 'Vertiv', nameKr: '베르티브', layer: 3, layerName: 'Enablers', subsegment: 'DC Power/Cooling', aiExposurePct: 70, market: 'US', region: 'US' },
  { ticker: 'ANET', name: 'Arista Networks', nameKr: '아리스타네트웍스', layer: 3, layerName: 'Enablers', subsegment: 'DC Network', aiExposurePct: 65, market: 'US', region: 'US' },
  { ticker: 'ETN', name: 'Eaton', nameKr: '이튼', layer: 3, layerName: 'Enablers', subsegment: 'Power Mgmt', aiExposurePct: 35, market: 'US', region: 'US' },
  { ticker: 'GEV', name: 'GE Vernova', nameKr: 'GE버노바', layer: 3, layerName: 'Enablers', subsegment: 'Grid/Power', aiExposurePct: 25, market: 'US', region: 'US' },
  { ticker: 'NVT', name: 'nVent Electric', nameKr: '엔벤트', layer: 3, layerName: 'Enablers', subsegment: 'Cooling', aiExposurePct: 30, market: 'US', region: 'US' },
  { ticker: 'SMCI', name: 'Super Micro Computer', nameKr: '슈퍼마이크로', layer: 3, layerName: 'Enablers', subsegment: 'AI Servers', aiExposurePct: 80, market: 'US', region: 'US' },
];

// Layer 4: Application - Enterprise AI Software
export const LAYER4_APP: ExtendedStockMeta[] = [
  { ticker: 'PLTR', name: 'Palantir', nameKr: '팔란티어', layer: 4, layerName: 'Application', subsegment: 'AIP Platform', aiExposurePct: 80, market: 'US', region: 'US' },
  { ticker: 'NOW', name: 'ServiceNow', nameKr: '서비스나우', layer: 4, layerName: 'Application', subsegment: 'Enterprise AI', aiExposurePct: 30, market: 'US', region: 'US' },
  { ticker: 'CRM', name: 'Salesforce', nameKr: '세일즈포스', layer: 4, layerName: 'Application', subsegment: 'Agentforce', aiExposurePct: 25, market: 'US', region: 'US' },
  { ticker: 'CRWD', name: 'CrowdStrike', nameKr: '크라우드스트라이크', layer: 4, layerName: 'Application', subsegment: 'AI Security', aiExposurePct: 50, market: 'US', region: 'US' },
  { ticker: 'ADBE', name: 'Adobe', nameKr: '어도비', layer: 4, layerName: 'Application', subsegment: 'Generative AI', aiExposurePct: 25, market: 'US', region: 'US' },
];

export const ALL_AI_STOCKS: ExtendedStockMeta[] = [
  ...LAYER1_FOUNDATION,
  ...LAYER2_INFRA,
  ...LAYER3_ENABLERS,
  ...LAYER4_APP,
];

export function getStocksByLayer(layer: number): ExtendedStockMeta[] {
  return ALL_AI_STOCKS.filter(s => s.layer === layer);
}

export function getKoreanSemis(): ExtendedStockMeta[] {
  return ALL_AI_STOCKS.filter(s => s.market === 'KR');
}

export function getUSStocks(): ExtendedStockMeta[] {
  return ALL_AI_STOCKS.filter(s => s.market === 'US');
}

export const SCORING_WEIGHTS = {
  aiExposure: 0.35,
  capitalEfficiency: 0.30,
  valuation: 0.20,
  momentum: 0.15,
};

export const SCREENING_THRESHOLDS = {
  minMarketCapB: 20,
  minRevenueGrowthPct: 12,
  minFcfMarginPct: 8,
  minAiExposurePct: 15,
  minAvgDollarVolumeM: 500,
};

// AI Supercycle Scenario configurations
export type RiskProfile = 'conservative' | 'moderate' | 'aggressive' | 'destructive';

export interface ScenarioConfig {
  name: string;
  nameKr: string;
  description: string;
  stopLossPct: number;
  positionSizePct: number;
  rebalanceFreqDays: number;
  minScoreThreshold: number;
  useLeverage: boolean;
  maxDrawdownPct: number;
  cashReservePct: number;
  avgDownEnabled: boolean;
  avgDownThresholdPct: number;
}

export const SCENARIOS: Record<RiskProfile, ScenarioConfig> = {
  conservative: {
    name: 'Conservative',
    nameKr: '보수적 접근',
    description: 'Capital preservation focus. Only high-score (≥85) Layer 1+2 stocks. 20% cash reserve. Tight stop-loss. No leverage.',
    stopLossPct: -10,
    positionSizePct: 8,
    rebalanceFreqDays: 90,
    minScoreThreshold: 85,
    useLeverage: false,
    maxDrawdownPct: -15,
    cashReservePct: 20,
    avgDownEnabled: true,
    avgDownThresholdPct: -8,
  },
  moderate: {
    name: 'Moderate',
    nameKr: '중도적 접근',
    description: 'Balanced growth & risk. Score ≥75 across all layers. 10% cash. Moderate stops. Standard position sizing.',
    stopLossPct: -15,
    positionSizePct: 10,
    rebalanceFreqDays: 60,
    minScoreThreshold: 75,
    useLeverage: false,
    maxDrawdownPct: -25,
    cashReservePct: 10,
    avgDownEnabled: true,
    avgDownThresholdPct: -12,
  },
  aggressive: {
    name: 'Aggressive',
    nameKr: '공격적 접근',
    description: 'Growth maximization. Score ≥65. Larger positions. Wider stops. Layer 3+4 included. 5% cash only.',
    stopLossPct: -22,
    positionSizePct: 14,
    rebalanceFreqDays: 30,
    minScoreThreshold: 65,
    useLeverage: false,
    maxDrawdownPct: -35,
    cashReservePct: 5,
    avgDownEnabled: true,
    avgDownThresholdPct: -15,
  },
  destructive: {
    name: 'Destructive',
    nameKr: '파괴적 접근 (고위험)',
    description: 'Maximum risk tolerance. No score floor. Full Layer 1-4 exposure. 2x leverage on Layer 1. Wide stops. Accept -50%+ drawdown.',
    stopLossPct: -30,
    positionSizePct: 16,
    rebalanceFreqDays: 14,
    minScoreThreshold: 0,
    useLeverage: true,
    maxDrawdownPct: -55,
    cashReservePct: 0,
    avgDownEnabled: true,
    avgDownThresholdPct: -20,
  },
};
