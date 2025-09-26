/**
 * Card de Análise Macroeconômica Avançada
 */

'use client';

import { Shield, BarChart3 } from 'lucide-react';
import { getRegimeIcon, getRegimeColorClasses, getRegimeDescription } from '@/utils/regimeUtils';

interface MacroAnalysisCardProps {
  macroAnalysis: {
    currentRegime: string;
    regimeConfidence: number;
    dataQuality: number;
    analysisTimestamp: string;
  };
}

export function MacroAnalysisCard({ macroAnalysis }: MacroAnalysisCardProps) {

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <Shield className="w-5 h-5 mr-2 text-purple-600" />
        Análise Macroeconômica Avançada
      </h2>

      {/* Regime Atual */}
      <div className={`rounded-lg border p-4 mb-4 ${getRegimeColorClasses(macroAnalysis.currentRegime)}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            {getRegimeIcon(macroAnalysis.currentRegime)}
            <span className="font-medium text-lg">{macroAnalysis.currentRegime}</span>
          </div>
          <span className="text-sm font-bold">
            {macroAnalysis.regimeConfidence.toFixed(1)}%
          </span>
        </div>

        <p className="text-sm opacity-80 mb-3">
          {getRegimeDescription(macroAnalysis.currentRegime)}
        </p>

        {/* Barra de confiança */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="h-2 rounded-full bg-current opacity-60"
            style={{ width: `${macroAnalysis.regimeConfidence}%` }}
          />
        </div>
      </div>

      {/* Métricas de Qualidade */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="flex items-center">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <span className="ml-2 text-sm font-medium text-blue-900">Séries de Dados</span>
          </div>
          <div className="text-xl font-bold text-blue-900 mt-1">
            {macroAnalysis.dataQuality}
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-3">
          <div className="flex items-center">
            <Shield className="w-4 h-4 text-purple-600" />
            <span className="ml-2 text-sm font-medium text-purple-900">Confiança</span>
          </div>
          <div className="text-xl font-bold text-purple-900 mt-1">
            {macroAnalysis.regimeConfidence.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Timestamp */}
      <div className="mt-4 text-xs text-gray-500">
        Última análise: {new Date(macroAnalysis.analysisTimestamp).toLocaleString()}
      </div>
    </div>
  );
}
