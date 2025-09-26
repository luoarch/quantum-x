/**
 * Utilitários compartilhados para regimes econômicos
 */

import { Activity, TrendingUp, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-react';

export const getRegimeIcon = (regime: string) => {
  if (!regime || typeof regime !== 'string') {
    return <Activity className="w-4 h-4 text-gray-600" />;
  }
  switch (regime.toUpperCase()) {
    case 'EXPANSION':
      return <TrendingUp className="w-4 h-4 text-green-600" />;
    case 'RECESSION':
      return <TrendingDown className="w-4 h-4 text-red-600" />;
    case 'RECOVERY':
      return <Activity className="w-4 h-4 text-blue-600" />;
    case 'CONTRACTION':
      return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
    default:
      return <Activity className="w-4 h-4 text-gray-600" />;
  }
};

export const getRegimeColor = (regime: string) => {
  if (!regime || typeof regime !== 'string') {
    return '#6B7280'; // Cor padrão para regime indefinido
  }
  switch (regime.toUpperCase()) {
    case 'EXPANSION':
      return '#10B981';
    case 'RECESSION':
      return '#EF4444';
    case 'RECOVERY':
      return '#3B82F6';
    case 'CONTRACTION':
      return '#F59E0B';
    default:
      return '#6B7280';
  }
};

export const getRegimeColorClasses = (regime: string) => {
  if (!regime || typeof regime !== 'string') {
    return 'bg-gray-50 border-gray-200 text-gray-800';
  }
  switch (regime.toUpperCase()) {
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

export const getRegimeDescription = (regime: string) => {
  if (!regime || typeof regime !== 'string') {
    return 'Regime econômico não identificado';
  }
  switch (regime.toUpperCase()) {
    case 'EXPANSION':
      return 'Período de crescimento econômico robusto';
    case 'RECESSION':
      return 'Período de declínio econômico com alta desemprego';
    case 'RECOVERY':
      return 'Período de recuperação econômica pós-recessão';
    case 'CONTRACTION':
      return 'Período de desaceleração econômica';
    default:
      return 'Regime econômico não identificado';
  }
};
