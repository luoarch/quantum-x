/**
 * Resumo dos Regimes Econômicos
 */

'use client';

import { RegimeData } from '@/types/trading';
import { Activity, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';

interface RegimeSummaryProps {
  regimes: RegimeData[];
}

export function RegimeSummary({ regimes }: RegimeSummaryProps) {
  const getRegimeIcon = (name: string) => {
    switch (name.toUpperCase()) {
      case 'EXPANSION':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'RECESSION':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      case 'RECOVERY':
        return <Activity className="w-4 h-4 text-blue-600" />;
      case 'CONTRACTION':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getRegimeColor = (name: string) => {
    switch (name.toUpperCase()) {
      case 'EXPANSION':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'RECESSION':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'RECOVERY':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'CONTRACTION':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  if (!regimes || regimes.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        Nenhum regime disponível
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {regimes.map((regime, index) => (
        <div key={index} className={`rounded-lg border p-4 ${getRegimeColor(regime.name)}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              {getRegimeIcon(regime.name)}
              <span className="font-medium">{regime.name}</span>
            </div>
            <span className="text-sm font-bold">
              {((regime.frequency || 0) * 100).toFixed(1)}%
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Prob. Média:</span>
              <span className="ml-1 font-medium">
                {((regime.avgProbability || 0) * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">Prob. Máxima:</span>
              <span className="ml-1 font-medium">
                {((regime.maxProbability || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Barra de progresso */}
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-current opacity-60"
                style={{ width: `${regime.frequency * 100}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
