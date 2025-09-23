/**
 * Métricas de Performance
 */

'use client';

import { PerformanceMetrics as PerformanceMetricsType } from '@/types/trading';
import { BarChart3, TrendingUp, Target, Shield } from 'lucide-react';

interface PerformanceMetricsProps {
  metrics: PerformanceMetricsType;
}

export function PerformanceMetrics({ metrics }: PerformanceMetricsProps) {
  const totalSignals = metrics.totalSignals;
  const buyPercentage = totalSignals > 0 ? (metrics.buySignals / totalSignals) * 100 : 0;
  const sellPercentage = totalSignals > 0 ? (metrics.sellSignals / totalSignals) * 100 : 0;
  const holdPercentage = totalSignals > 0 ? (metrics.holdSignals / totalSignals) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Resumo Geral */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <span className="ml-2 text-sm font-medium text-blue-900">Total Sinais</span>
          </div>
          <div className="text-2xl font-bold text-blue-900 mt-1">
            {totalSignals}
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-green-600" />
            <span className="ml-2 text-sm font-medium text-green-900">Compra</span>
          </div>
          <div className="text-2xl font-bold text-green-900 mt-1">
            {buyPercentage.toFixed(1)}%
          </div>
        </div>

        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-red-600 rotate-180" />
            <span className="ml-2 text-sm font-medium text-red-900">Venda</span>
          </div>
          <div className="text-2xl font-bold text-red-900 mt-1">
            {sellPercentage.toFixed(1)}%
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <Target className="w-5 h-5 text-gray-600" />
            <span className="ml-2 text-sm font-medium text-gray-900">Hold</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {holdPercentage.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Métricas HRP */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Shield className="w-5 h-5 mr-2 text-purple-600" />
          Métricas HRP (Hierarchical Risk Parity)
        </h3>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-900">
              {metrics.hrpMetrics?.expectedReturn?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-purple-700">Retorno Esperado</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-purple-900">
              {metrics.hrpMetrics?.volatility?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-purple-700">Volatilidade</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-purple-900">
              {metrics.hrpMetrics?.sharpeRatio?.toFixed(2) || '0.00'}
            </div>
            <div className="text-sm text-purple-700">Sharpe Ratio</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-purple-900">
              {metrics.hrpMetrics?.effectiveDiversification?.toFixed(1) || '0.0'}
            </div>
            <div className="text-sm text-purple-700">Diversificação</div>
          </div>
        </div>
      </div>

      {/* Probabilidades Médias */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Confiança Média</div>
          <div className="text-2xl font-bold text-gray-900">
            {((metrics.avgConfidence || 0) * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Prob. Compra Média</div>
          <div className="text-2xl font-bold text-green-600">
            {((metrics.avgBuyProbability || 0) * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Prob. Venda Média</div>
          <div className="text-2xl font-bold text-red-600">
            {((metrics.avgSellProbability || 0) * 100).toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
}
