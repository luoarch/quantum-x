# Quantum X Dashboard

Dashboard em tempo real para o sistema de trading signals baseado em metodologias científicas avançadas.

## 🚀 Funcionalidades

- **Gráficos CLI em tempo real** com Chart.js
- **Painel de sinais** com probabilidades
- **Resumo de regimes econômicos** (Markov-Switching)
- **Alocação HRP** com gráficos interativos
- **Métricas de performance** em tempo real
- **Atualização automática** a cada 30 segundos

## 🛠️ Tecnologias

- **Next.js 15** com App Router
- **TypeScript** para type safety
- **Tailwind CSS** para styling
- **Chart.js** para gráficos
- **Recharts** para gráficos de pizza
- **Lucide React** para ícones

## 📦 Instalação

```bash
# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local
# Editar .env.local com suas configurações

# Executar em desenvolvimento
npm run dev
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Estrutura do Projeto

```
src/
├── app/                 # App Router do Next.js
├── components/          # Componentes React
│   ├── Dashboard.tsx    # Dashboard principal
│   ├── CLIChart.tsx    # Gráfico CLI
│   ├── SignalPanel.tsx  # Painel de sinais
│   └── ...
├── hooks/              # Custom hooks
├── types/              # Tipos TypeScript
└── lib/                # Utilitários
```

## 🎯 Componentes Principais

### Dashboard
- Layout responsivo com grid
- Integração com API backend
- Atualização automática

### CLIChart
- Gráfico de linha com Chart.js
- Dados CLI e confiança
- Tooltips informativos

### SignalPanel
- Sinal atual com probabilidades
- Histórico de sinais recentes
- Indicadores visuais

### PerformanceMetrics
- Métricas HRP
- Estatísticas de sinais
- KPIs de performance

## 🚀 Deploy

```bash
# Build para produção
npm run build

# Executar em produção
npm start
```

## 📊 APIs Utilizadas

- `GET /api/v1/signals/` - Sinais atuais
- `GET /api/v1/signals/backtest` - Métricas de performance
- `GET /api/v1/data/series/cli` - Dados CLI

## 🔄 Atualização em Tempo Real

O dashboard atualiza automaticamente a cada 30 segundos, buscando novos dados da API backend.

## 🎨 Design System

- **Cores**: Azul (primário), Verde (compra), Vermelho (venda)
- **Tipografia**: Inter (sistema)
- **Ícones**: Lucide React
- **Layout**: Grid responsivo com Tailwind CSS