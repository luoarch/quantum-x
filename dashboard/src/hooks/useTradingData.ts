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

      // Buscar dados dos sinais usando o endpoint /generate
      const response = await fetch(`${API_BASE_URL}/api/v1/signals/generate`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const signalsData = await response.json();

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
        cliData: signalsData.cli_data || [],
        performance: signalsData.performance || {
          totalSignals: 0,
          buySignals: 0,
          sellSignals: 0,
          holdSignals: 0,
          avgConfidence: 0,
          avgBuyProbability: 0,
          avgSellProbability: 0,
          regimeSummary: [],
          hrpAllocation: [],
          hrpMetrics: {
            expectedReturn: 0,
            volatility: 0,
            sharpeRatio: 0,
            effectiveDiversification: 0
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar dados');
      console.error('Erro ao buscar dados:', err);
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
