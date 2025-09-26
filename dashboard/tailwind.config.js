/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Cores do sistema
        background: 'var(--background)',
        foreground: 'var(--foreground)',

        // Cores para regimes econômicos
        regime: {
          recession: '#ef4444',    // Vermelho para recessão
          recovery: '#f59e0b',     // Laranja para recuperação
          expansion: '#10b981',    // Verde para expansão
          contraction: '#8b5cf6',  // Roxo para contração
          stress: '#dc2626',       // Vermelho escuro para estresse
          calm: '#06b6d4',         // Ciano para calma
        },

        // Cores para spillovers
        spillover: {
          trade: '#3b82f6',        // Azul para canal comercial
          commodity: '#f59e0b',    // Laranja para commodities
          financial: '#8b5cf6',    // Roxo para financeiro
          supply_chain: '#10b981', // Verde para cadeias globais
        },

        // Cores para indicadores
        indicator: {
          positive: '#10b981',     // Verde para positivo
          negative: '#ef4444',     // Vermelho para negativo
          neutral: '#6b7280',      // Cinza para neutro
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
