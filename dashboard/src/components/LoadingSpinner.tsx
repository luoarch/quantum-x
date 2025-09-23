/**
 * Componente de Loading
 */

'use client';

import { Loader2 } from 'lucide-react';

export function LoadingSpinner() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Carregando Dashboard
        </h2>
        <p className="text-gray-600">
          Buscando dados dos sinais de trading...
        </p>
      </div>
    </div>
  );
}
