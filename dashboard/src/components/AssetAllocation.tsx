/**
 * Alocação de Ativos HRP
 */

'use client';

import { AssetData } from '@/types/trading';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface AssetAllocationProps {
  assets: AssetData[];
  hrpMetrics: {
    expectedReturn: number;
    volatility: number;
    sharpeRatio: number;
    effectiveDiversification: number;
  };
}

export function AssetAllocation({ assets, hrpMetrics }: AssetAllocationProps) {
  // Preparar dados para o gráfico de pizza
  const pieData = assets.map(asset => ({
    name: asset.name,
    value: asset.allocation,
    ticker: asset.ticker
  }));

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  return (
    <div className="space-y-4">
      {/* Gráfico de Pizza */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(props: any) => `${props.name}: ${props.value.toFixed(1)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Lista de Ativos */}
      <div className="space-y-2">
        {assets.map((asset, index) => (
          <div key={asset.ticker} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <div>
                <div className="font-medium text-gray-900">{asset.name}</div>
                <div className="text-sm text-gray-500">{asset.ticker}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold text-gray-900">{asset.allocation.toFixed(1)}%</div>
              <div className="text-sm text-gray-500">
                R$ {asset.price.toFixed(2)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Métricas HRP */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Métricas HRP</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-600">Retorno:</span>
            <span className="ml-1 font-medium text-green-600">
              {hrpMetrics?.expectedReturn?.toFixed(1) || '0.0'}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">Volatilidade:</span>
            <span className="ml-1 font-medium text-red-600">
              {hrpMetrics?.volatility?.toFixed(1) || '0.0'}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">Sharpe:</span>
            <span className="ml-1 font-medium text-blue-600">
              {hrpMetrics?.sharpeRatio?.toFixed(2) || '0.00'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Diversificação:</span>
            <span className="ml-1 font-medium text-purple-600">
              {hrpMetrics?.effectiveDiversification?.toFixed(1) || '0.0'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
