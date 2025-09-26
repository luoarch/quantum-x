/**
 * Componente para mostrar probabilidades de regimes econômicos
 */

'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getRegimeIcon, getRegimeColor } from '@/utils/regimeUtils';

interface RegimeProbabilitiesProps {
  regimeSummary: Array<{
    regime: string;
    probability: number;
    frequency: number;
    avgProbability: number;
    maxProbability: number;
  }>;
}

export function RegimeProbabilities({ regimeSummary }: RegimeProbabilitiesProps) {

  // Preparar dados para o gráfico
  const chartData = regimeSummary
    .filter(regime => regime && regime.regime) // Filtrar regimes válidos
    .map(regime => ({
      regime: regime.regime || 'UNKNOWN',
      probability: regime.probability || 0,
      frequency: regime.frequency || 0,
      color: getRegimeColor(regime.regime)
    }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Probabilidades de Regimes Econômicos
      </h2>

      {/* Gráfico de barras */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="regime"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              label={{ value: 'Probabilidade (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}%`, 'Probabilidade']}
              labelFormatter={(label: string) => `Regime: ${label}`}
            />
            <Bar
              dataKey="probability"
              fill="#3B82F6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Lista detalhada */}
      <div className="space-y-3">
        {regimeSummary
          .filter(regime => regime && regime.regime) // Filtrar regimes válidos
          .map((regime, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getRegimeIcon(regime.regime)}
                <div>
                  <div className="font-medium text-gray-900">{regime.regime || 'UNKNOWN'}</div>
                  <div className="text-sm text-gray-500">
                    Frequência: {(regime.frequency || 0).toFixed(1)}%
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-gray-900">
                  {(regime.probability || 0).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">
                  Probabilidade
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Resumo estatístico */}
      <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Resumo Estatístico</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Regime mais provável:</span>
            <span className="ml-1 font-medium text-indigo-600">
              {regimeSummary
                .filter(regime => regime && regime.regime)
                .reduce((max, regime) =>
                  (regime.probability || 0) > (max.probability || 0) ? regime : max,
                  { regime: 'UNKNOWN', probability: 0 }
                ).regime}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Diversidade:</span>
            <span className="ml-1 font-medium text-purple-600">
              {regimeSummary.length} regimes
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
