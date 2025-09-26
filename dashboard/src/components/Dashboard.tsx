/**
 * Dashboard Principal - Sistema de Trading Signals
 */

'use client';

import { useTradingData } from '@/hooks/useTradingData';
import { CLIChart } from './CLIChart';
import { SignalPanel } from './SignalPanel';
import { PerformanceMetrics } from './PerformanceMetrics';
import { RegimeSummary } from './RegimeSummary';
import { AssetAllocation } from './AssetAllocation';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

export default function Dashboard() {
  const { data, loading, error, refetch } = useTradingData();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />;
  }

  if (!data) {
    return <ErrorMessage error="Nenhum dado disponível" onRetry={refetch} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Quantum X Trading Signals
              </h1>
              <p className="text-sm text-gray-500">
                Sistema Avançado de Sinais Probabilísticos
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">
                Última atualização: {new Date(data.lastUpdate).toLocaleString()}
              </p>
              <button
                onClick={refetch}
                className="mt-1 text-xs text-blue-600 hover:text-blue-800"
              >
                Atualizar
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Coluna Principal - Gráficos */}
          <div className="lg:col-span-2 space-y-6">
            {/* CLI Chart */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                CLI vs Regimes Econômicos
              </h2>
              <CLIChart data={data.cliData} />
            </div>

            {/* Performance Metrics */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Métricas de Performance
              </h2>
              <PerformanceMetrics metrics={data.performance} />
            </div>
          </div>

          {/* Sidebar - Sinais e Resumos */}
          <div className="space-y-6">
            {/* Painel de Sinais */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Sinal Atual
              </h2>
              <SignalPanel 
                currentSignal={data.currentSignal}
                recentSignals={data.recentSignals}
              />
            </div>

            {/* Resumo dos Regimes */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Regimes Econômicos
              </h2>
              <RegimeSummary regimes={data.performance.regimeSummary || []} />
            </div>

            {/* Alocação de Ativos */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Sugestão de Alocação HRP
              </h2>
              <AssetAllocation 
                assets={data.assets}
                hrpMetrics={data.performance.hrpMetrics}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
