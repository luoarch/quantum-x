/**
 * Tipos TypeScript para o Sistema de Trading Signals
 */

export interface CLISignal {
  date: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  strength: number;
  confidence: number;
  regime: string;
  buyProbability: number;
  sellProbability: number;
}

export interface RegimeData {
  name: string;
  probability: number;
  frequency: number;
  avgProbability: number;
  maxProbability: number;
}

export interface HRPAllocation {
  asset: string;
  allocation: number;
  expectedReturn: number;
  volatility: number;
  sharpeRatio: number;
}

export interface PerformanceMetrics {
  totalSignals: number;
  buySignals: number;
  sellSignals: number;
  holdSignals: number;
  avgConfidence: number;
  avgBuyProbability: number;
  avgSellProbability: number;
  regimeSummary: RegimeData[];
  hrpAllocation: HRPAllocation[];
  hrpMetrics: {
    expectedReturn: number;
    volatility: number;
    sharpeRatio: number;
    effectiveDiversification: number;
  };
}

export interface CLIDataPoint {
  date: string;
  value: number;
  regime: string;
  confidence: number;
}

export interface AssetData {
  ticker: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  allocation: number;
  suggestedAllocation?: number;
  currentPrice?: number;
  recommendedAction?: string;
}

export interface DashboardData {
  currentSignal: CLISignal;
  recentSignals: CLISignal[];
  cliData: CLIDataPoint[];
  performance: PerformanceMetrics;
  assets: AssetData[];
  lastUpdate: string;
}
