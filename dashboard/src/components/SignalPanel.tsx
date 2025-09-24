/**
 * Painel de Sinais - Mostra sinal atual e histórico
 */

'use client';

import { CLISignal } from '@/types/trading';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

interface SignalPanelProps {
  currentSignal: CLISignal;
  recentSignals: CLISignal[];
}

export function SignalPanel({ currentSignal, recentSignals }: SignalPanelProps) {
  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'SELL':
        return <TrendingDown className="w-5 h-5 text-red-600" />;
      default:
        return <Minus className="w-5 h-5 text-gray-600" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'SELL':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
      {/* Sinal Atual */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">Sinal Atual</h3>
          <div className="flex items-center space-x-2">
            {getSignalIcon(currentSignal.signal)}
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getSignalColor(currentSignal.signal)}`}>
              {currentSignal.signal}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Força:</span>
            <span className="ml-2 font-medium">{currentSignal.strength}/5</span>
          </div>
          <div>
            <span className="text-gray-500">Confiança:</span>
            <span className={`ml-2 font-medium ${getConfidenceColor(currentSignal.confidence)}`}>
              {(currentSignal.confidence || 0).toFixed(1)}%
            </span>
          </div>
          <div>
            <span className="text-gray-500">Regime:</span>
            <span className="ml-2 font-medium">{currentSignal.regime}</span>
          </div>
          <div>
            <span className="text-gray-500">Data:</span>
            <span className="ml-2 font-medium">
              {new Date(currentSignal.date).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Probabilidades */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex justify-between text-sm">
            <div className="flex items-center">
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-gray-500">Compra:</span>
              <span className="ml-1 font-medium text-green-600">
                {(currentSignal.buyProbability || 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center">
              <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
              <span className="text-gray-500">Venda:</span>
              <span className="ml-1 font-medium text-red-600">
                {(currentSignal.sellProbability || 0).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Sinais Recentes */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
          <Activity className="w-4 h-4 mr-2" />
          Sinais Recentes
        </h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {recentSignals.slice(0, 10).map((signal, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getSignalIcon(signal.signal)}
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {signal.signal}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(signal.date).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">
                  {signal.regime}
                </div>
                <div className="text-xs text-gray-500">
                  {(signal.confidence || 0).toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
