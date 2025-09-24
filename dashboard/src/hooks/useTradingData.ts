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

      console.log('🔍 [Dashboard] Buscando dados da API:', `${API_BASE_URL}/api/v1/dashboard/dashboard-data`);

      // Buscar dados do dashboard usando o endpoint real
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/dashboard-data`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const signalsData = await response.json();
      console.log('✅ [Dashboard] Dados recebidos da API:', signalsData);

      // Converter dados da API para o formato do dashboard
      const dashboardData: DashboardData = {
        currentSignal: signalsData.currentSignal || {
          date: new Date().toISOString(),
          signal: 'HOLD',
          strength: 0,
          confidence: 0,
          regime: 'NEUTRAL',
          buyProbability: 0,
          sellProbability: 0
        },
        recentSignals: signalsData.recentSignals || [],
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
          avgConfidence: signalsData.performance?.avgConfidence || 0,
          avgBuyProbability: signalsData.performance?.avgBuyProbability || 0,
          avgSellProbability: signalsData.performance?.avgSellProbability || 0,
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
        assets: signalsData.assets || [
          {
            ticker: 'TESOURO_IPCA',
            name: 'Tesouro IPCA+ 2045',
            price: 100.0,
            change: 0.0,
            changePercent: 0.0,
            allocation: 50.0
          },
          {
            ticker: 'BOVA11',
            name: 'BOVA11',
            price: 100.0,
            change: 0.0,
            changePercent: 0.0,
            allocation: 50.0
          }
        ],
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
