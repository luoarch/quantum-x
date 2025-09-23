/**
 * Gráfico CLI com Chart.js
 */

'use client';

import { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { CLIDataPoint } from '@/types/trading';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface CLIChartProps {
  data: CLIDataPoint[];
}

export function CLIChart({ data }: CLIChartProps) {
  const chartRef = useRef<ChartJS<'line'>>(null);

  // Preparar dados para o gráfico
  const chartData = {
    labels: data.map(point => new Date(point.date).toLocaleDateString()),
    datasets: [
      {
        label: 'CLI Value',
        data: data.map(point => point.value),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Confidence',
        data: data.map(point => point.confidence * 100),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
        yAxisID: 'y1',
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      title: {
        display: true,
        text: 'CLI e Confiança dos Regimes',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          afterLabel: (context: any) => {
            const dataIndex = context.dataIndex;
            const point = data[dataIndex];
            return [
              `Regime: ${point.regime}`,
              `Confiança: ${((point.confidence || 0) * 100).toFixed(1)}%`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Data'
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'CLI Value'
        },
        min: 90,
        max: 110
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Confiança (%)'
        },
        min: 0,
        max: 100,
        grid: {
          drawOnChartArea: false,
        },
      }
    }
  };

  return (
    <div className="h-96">
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  );
}
