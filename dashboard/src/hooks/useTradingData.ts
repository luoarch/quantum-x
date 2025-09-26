/**
 * Hook para buscar dados de trading da API
 */

import { useState, useEffect } from 'react';
import { DashboardData } from '@/types/trading';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useTradingData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔍 [Dashboard] Buscando dados da API:', `${API_BASE_URL}/api/v1/dashboard/dashboard-data-simple`);

      // Buscar dados do dashboard usando o endpoint simplificado
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/dashboard-data-simple`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const signalsData = await response.json();
      console.log('✅ [Dashboard] Dados recebidos da API:', signalsData);

      // Converter dados da API para o formato do dashboard
      const dashboardData: DashboardData = {
        currentSignal: {
          date: signalsData.currentSignal?.date || new Date().toISOString(),
          signal: signalsData.currentSignal?.signal || 'HOLD',
          strength: signalsData.currentSignal?.strength || 0,
          confidence: signalsData.currentSignal?.confidence || 0,
          regime: signalsData.currentSignal?.regime || 'NEUTRAL',
          buyProbability: signalsData.currentSignal?.buyProbability || 0,
          sellProbability: signalsData.currentSignal?.sellProbability || 0
        },
        recentSignals: (signalsData.recentSignals || []).map((signal: any) => ({
          date: signal.date,
          signal: signal.signal || 'HOLD',
          strength: signal.strength || 0,
          confidence: signal.confidence || 0,
          regime: signal.regime || 'NEUTRAL',
          buyProbability: signal.buyProbability || 0,
          sellProbability: signal.sellProbability || 0
        })),
        cliData: (signalsData.cliData || []).map((point: any) => ({
          date: point.date,
          value: point.value,
          confidence: point.confidence,
          regime: point.regime || 'EXPANSION'
        })),
        performance: {
          totalSignals: signalsData.performance?.totalSignals || 0,
          buySignals: signalsData.performance?.buySignals || 0,
          sellSignals: signalsData.performance?.sellSignals || 0,
          holdSignals: signalsData.performance?.holdSignals || 0,
          avgConfidence: signalsData.currentSignal?.confidence || 0, // Usar confiança do sinal atual
          avgBuyProbability: signalsData.currentSignal?.buyProbability || 0,
          avgSellProbability: signalsData.currentSignal?.sellProbability || 0,
          regimeSummary: (signalsData.performance?.regimeSummary || []).map((regime: any) => ({
            name: regime.regime || 'UNKNOWN',
            probability: regime.probability || 0,
            frequency: regime.frequency || 0,
            avgProbability: regime.probability || 0,
            maxProbability: regime.probability || 0
          })),
          hrpAllocation: signalsData.performance?.hrpAllocation || [],
          hrpMetrics: {
            expectedReturn: signalsData.performance?.hrpMetrics?.expectedReturn || 0,
            volatility: signalsData.performance?.hrpMetrics?.volatility || 0,
            sharpeRatio: signalsData.performance?.hrpMetrics?.sharpeRatio || 0,
            effectiveDiversification: signalsData.performance?.hrpMetrics?.effectiveDiversification || 0
          }
        },
        assets: (signalsData.assets || []).map((asset: any) => ({
          ticker: asset.ticker || 'UNKNOWN',
          name: asset.name || 'Ativo',
          price: asset.price || 0,
          change: asset.change || 0,
          changePercent: asset.changePercent || 0,
          allocation: asset.allocation || 0,
          suggestedAllocation: asset.suggestedAllocation || asset.allocation || 0,
          currentPrice: asset.currentPrice || asset.price || 0,
          recommendedAction: asset.recommendedAction || 'MANTER'
        })),
        lastUpdate: signalsData.lastUpdate || new Date().toISOString()
      };

      setData(dashboardData);
      console.log('🎉 [Dashboard] Dados processados e salvos:', dashboardData);
      console.log('📊 [Dashboard] CLI Data:', signalsData.cliData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar dados');
      console.error('❌ [Dashboard] Erro ao buscar dados:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Atualizar dados a cada 30 segundos
    const interval = setInterval(fetchData, 30000);

    return () => clearInterval(interval);
  }, []);

  return { data, loading, error, refetch: fetchData };
}
