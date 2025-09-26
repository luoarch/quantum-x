<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Documento de Requisitos do Sistema (DRS)

## Global Economic Regime Analysis \& Brazil Spillover Prediction System


***

**Versão:** 1.0
**Data:** 26 de Setembro de 2025
**Autor:** Sistema de Análise Econômica
**Status:** Aprovado

***

## 1. Visão Geral do Projeto

### 1.1 Descrição Executiva

O **Global Economic Regime Analysis \& Brazil Spillover Prediction System** é uma plataforma científica avançada para identificação de regimes econômicos globais e previsão de seus efeitos spillover na economia brasileira. O sistema utiliza modelos Regime-Switching Global VAR (RS-GVAR) e análise multicanal de transmissão para fornecer insights preditivos robustos sobre impactos macroeconômicos.

### 1.2 Objetivos do Sistema

**Objetivos Primários:**

- Identificar regimes econômicos globais em tempo real usando metodologias cientificamente validadas
- Quantificar spillovers econômicos para o Brasil através de múltiplos canais de transmissão
- Prover previsões regime-condicionais para indicadores macroeconômicos brasileiros
- Oferecer interface intuitiva para análise e visualização de resultados

**Objetivos Secundários:**

- Estabelecer framework de validação contínua dos modelos
- Implementar sistema de alertas para mudanças de regime
- Criar repositório de cenários históricos para backtesting
- Desenvolver API robusta para integração com sistemas externos


### 1.3 Escopo do Projeto

**Dentro do Escopo:**

- Análise de regimes para G7 + China + Brasil
- 4 canais de transmissão: Trade, Commodity, Financial, Supply Chain
- Previsões até 12 meses à frente
- Interface web responsiva com dashboards interativos
- API RESTful para acesso programático
- Sistema de validação automatizada

**Fora do Escopo (Fase 1):**

- Análise intraday ou alta frequência
- Modelos de otimização de portfólio
- Integração com sistemas de trading
- Análise setorial granular
- Interface mobile nativa

***

## 2. Arquitetura do Sistema

### 2.1 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND - Next.js 15                   │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway - FastAPI                   │
├─────────────────────────────────────────────────────────────┤
│                 Core Analysis Engine                        │
│  ┌───────────────────┐  ┌───────────────────────────────┐  │
│  │  Global Regime    │  │  Brazil Spillover             │  │
│  │  Analysis         │  │  Analysis                     │  │
│  │                   │  │                               │  │
│  │  - RS-GVAR        │  │  - Trade Channel              │  │
│  │  - Regime ID      │  │  - Commodity Channel          │  │
│  │  - Validation     │  │  - Financial Channel          │  │
│  └───────────────────┘  │  - Supply Chain Channel       │  │
│                         └───────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Data Management Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Data Ingest │ │ Data Store  │ │ Model Artifacts     │  │
│  │             │ │             │ │                     │  │
│  │ - FRED API  │ │ PostgreSQL  │ │ - Trained Models    │  │
│  │ - OECD API  │ │ TimescaleDB │ │ - Validation Cache  │  │
│  │ - Yahoo Fin │ │ Redis       │ │ - Backtesting Data  │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```


### 2.2 Stack Tecnológico

**Backend (Python):**

- **Framework:** FastAPI 0.104+
- **ML/Estatística:** statsmodels, scikit-learn, numpy, pandas
- **Async:** asyncio, aiohttp
- **Database:** PostgreSQL + TimescaleDB, Redis
- **Testing:** pytest, pytest-asyncio
- **Monitoring:** Prometheus + Grafana

**Frontend (Next.js 15):**

- **Framework:** Next.js 15 (App Router)
- **UI Library:** shadcn/ui + Tailwind CSS
- **Charts:** Recharts + D3.js
- **State Management:** Zustand
- **Testing:** Vitest + Playwright
- **Deployment:** Vercel/Netlify

**Infrastructure:**

- **Containerization:** Docker + Docker Compose
- **Orchestration:** Kubernetes (opcional)
- **CI/CD:** GitHub Actions
- **Monitoring:** Datadog/New Relic
- **Cache:** Redis Cluster

***

## 3. Requisitos Funcionais

### 3.1 Módulo de Análise Global (RF001-RF020)

#### RF001: Coleta de Dados Globais

**Descrição:** O sistema deve coletar automaticamente dados econômicos de fontes oficiais para países G7 + China.

**Critérios de Aceitação:**

- Integração com APIs: FRED, OECD, Yahoo Finance, World Bank
- Coleta automática a cada 6 horas
- Validação de integridade dos dados coletados
- Tratamento de dados faltantes e outliers
- Histórico mínimo de 20 anos para cada série

**Prioridade:** Crítica
**Complexidade:** Alta

#### RF002: Identificação de Regimes Globais

**Descrição:** Implementar modelo Regime-Switching Global VAR para identificação automática de regimes econômicos.

**Critérios de Aceitação:**

- Implementação de RS-GVAR usando statsmodels
- Seleção endógena do número de regimes (2-6)
- Critérios BIC/AIC para seleção de modelo
- Identificação de regimes atuais com probabilidades
- Matriz de transição entre regimes

**Prioridade:** Crítica
**Complexidade:** Muito Alta

#### RF003: Validação de Modelos Globais

**Descrição:** Sistema automatizado de validação e diagnóstico dos modelos RS-GVAR.

**Critérios de Aceitação:**

- Testes de linearidade vs. não-linearidade
- Diagnósticos de resíduos
- Validação fora da amostra (rolling window)
- Testes de estabilidade paramétrica
- Métricas de performance do modelo

**Prioridade:** Alta
**Complexidade:** Alta

#### RF004: Previsão de Regimes Globais

**Descrição:** Gerar previsões probabilísticas de regimes globais até 12 meses à frente.

**Critérios de Aceitação:**

- Horizonte de previsão: 1-12 meses
- Intervalos de confiança para previsões
- Cenários alternativos baseados em choques
- Atualização automática das previsões
- Histórico de acurácia das previsões

**Prioridade:** Alta
**Complexidade:** Alta

### 3.2 Módulo de Spillovers Brasil (RF021-RF040)

#### RF021: Análise do Canal Comercial

**Descrição:** Quantificar spillovers via comércio internacional Brasil-Mundo.

**Critérios de Aceitação:**

- Cálculo de pesos comerciais por país/região
- Elasticidades regime-dependentes
- Impacto em termos de troca
- Efeitos no volume de comércio
- Análise de concentração setorial

**Prioridade:** Crítica
**Complexidade:** Alta

#### RF022: Análise do Canal de Commodities

**Descrição:** Quantificar spillovers via preços de commodities relevantes para o Brasil.

**Critérios de Aceitação:**

- Monitoramento de 8+ commodities críticas
- Pesos baseados na pauta exportadora
- Elasticidades preço-quantidade regime-específicas
- Impacto fiscal via royalties/impostos
- Efeito câmbio via termos de troca

**Prioridade:** Crítica
**Complexidade:** Alta

#### RF023: Análise do Canal Financeiro

**Descrição:** Quantificar spillovers via mercados financeiros e fluxos de capital.

**Critérios de Aceitação:**

- Monitoramento de spreads soberanos
- Análise de fluxos de capital
- Impacto em taxa de câmbio
- Prêmio de risco-país
- Efeitos no mercado de capitais doméstico

**Prioridade:** Alta
**Complexidade:** Alta

#### RF024: Análise do Canal de Cadeias Globais

**Descrição:** Quantificar spillovers via cadeias globais de valor (limitado para o Brasil).

**Critérios de Aceitação:**

- Medição de participação em GVCs
- Posição upstream/downstream
- Índices de complexidade produtiva
- Impacto de disruptions globais
- Custo de oportunidade da baixa integração

**Prioridade:** Média
**Complexidade:** Alta

#### RF025: Agregação de Spillovers

**Descrição:** Consolidar efeitos de todos os canais em impacto agregado para o Brasil.

**Critérios de Aceitação:**

- Pesos dinâmicos por canal
- Matriz de correlação entre canais
- Efeitos diretos e indiretos
- Intervalos de confiança para agregação
- Decomposição da variância por canal

**Prioridade:** Alta
**Complexidade:** Alta

### 3.3 Módulo de Previsões Brasil (RF041-RF050)

#### RF041: Previsão de Indicadores Macroeconômicos

**Descrição:** Prever principais indicadores brasileiros condicionados aos regimes globais.

**Critérios de Aceitação:**

- Previsão de PIB, inflação, desemprego, câmbio
- Condicionamento aos regimes globais identificados
- Horizonte: 1-12 meses
- Cenários alternativos de spillovers
- Intervalos de confiança das previsões

**Prioridade:** Crítica
**Complexidade:** Alta

#### RF042: Sistema de Alertas

**Descrição:** Alertas automáticos para mudanças significativas de regime ou spillovers.

**Critérios de Aceitação:**

- Alertas via email/webhook
- Níveis configuráveis de severidade
- Alertas de mudança de regime
- Alertas de spillovers anômalos
- Log completo de alertas enviados

**Prioridade:** Média
**Complexidade:** Média

### 3.4 API e Integração (RF051-RF070)

#### RF051: API RESTful Completa

**Descrição:** API robusta para acesso programático a todas as funcionalidades.

**Critérios de Aceitação:**

- Endpoints para todos os módulos
- Autenticação JWT
- Rate limiting configurável
- Documentação OpenAPI/Swagger
- Versionamento de API

**Prioridade:** Alta
**Complexidade:** Média

#### RF052: Webhooks para Atualizações

**Descrição:** Sistema de webhooks para notificar sistemas externos sobre atualizações.

**Critérios de Aceitação:**

- Webhooks configuráveis por evento
- Retry automático em falhas
- Log de entregas de webhooks
- Validação de payload
- Rate limiting de webhooks

**Prioridade:** Baixa
**Complexidade:** Média

### 3.5 Dashboard e Visualização (RF071-RF090)

#### RF071: Dashboard Principal

**Descrição:** Interface principal com visão consolidada dos regimes globais e spillovers Brasil.

**Critérios de Aceitação:**

- Layout responsivo (desktop/tablet/mobile)
- Atualização em tempo real
- Filtros por período e geografia
- Export de dados e gráficos
- Modo escuro/claro

**Prioridade:** Alta
**Complexidade:** Média

#### RF072: Visualizações Interativas

**Descrição:** Gráficos e visualizações avançadas para análise exploratória.

**Critérios de Aceitação:**

- Gráficos de séries temporais interativos
- Mapas coropléticos para regimes globais
- Sankey diagrams para spillovers
- Heatmaps de correlação
- Árvores de decomposição

**Prioridade:** Alta
**Complexidade:** Alta

#### RF073: Relatórios Automatizados

**Descrição:** Geração automática de relatórios em PDF/HTML com análises padronizadas.

**Critérios de Aceitação:**

- Templates configuráveis
- Geração programada (diária/semanal/mensal)
- Envio automático por email
- Personalização por usuário
- Histórico de relatórios gerados

**Prioridade:** Média
**Complexidade:** Média

***

## 4. Requisitos Não-Funcionais

### 4.1 Performance (RNF001-RNF010)

#### RNF001: Tempo de Resposta

- **API:** Resposta < 500ms para 95% das requisições
- **Dashboard:** Carregamento inicial < 2s
- **Análise Completa:** Execução < 30 minutos
- **Previsões:** Geração < 5 minutos


#### RNF002: Throughput

- **API:** Suporte a 1000+ requisições/minuto
- **Usuários Concorrentes:** 50+ usuários simultâneos
- **Processamento:** 10+ análises paralelas


#### RNF003: Escalabilidade

- **Horizontal:** Auto-scaling baseado em carga
- **Vertical:** Suporte até 32GB RAM / 16 CPU cores
- **Database:** Particionamento temporal automático


### 4.2 Disponibilidade (RNF011-RNF015)

#### RNF011: Uptime

- **SLA:** 99.9% de disponibilidade mensal
- **Downtime Planejado:** < 4 horas/mês
- **Recovery Time:** < 15 minutos


#### RNF012: Backup e Recuperação

- **Backup Incremental:** A cada 6 horas
- **Backup Completo:** Diário
- **Retenção:** 30 dias (incremental), 1 ano (completo)
- **Teste de Recuperação:** Mensal


### 4.3 Segurança (RNF016-RNF025)

#### RNF016: Autenticação e Autorização

- **Autenticação:** JWT com refresh tokens
- **Autorização:** RBAC (Role-Based Access Control)
- **MFA:** Opcionalmente disponível
- **Password Policy:** Conforme OWASP


#### RNF017: Proteção de Dados

- **Encryption at Rest:** AES-256
- **Encryption in Transit:** TLS 1.3
- **API Security:** Rate limiting, input validation
- **Audit Trail:** Log completo de acessos


#### RNF018: Compliance

- **GDPR:** Compliance parcial (dados não-pessoais)
- **SOC 2:** Preparação para certificação
- **Penetration Testing:** Trimestral


### 4.4 Confiabilidade (RNF026-RNF035)

#### RNF026: Validação de Dados

- **Data Quality:** Verificação automática de anomalias
- **Missing Data:** Tratamento robusto < 10% missing
- **Outliers:** Detecção e tratamento automático
- **Consistency:** Validação cruzada entre fontes


#### RNF027: Model Validation

- **Out-of-Sample:** Validação contínua mensal
- **Backtesting:** Histórico de 10+ anos
- **Model Monitoring:** Drift detection automático
- **A/B Testing:** Para mudanças de modelo


#### RNF028: Error Handling

- **Graceful Degradation:** Fallbacks para componentes críticos
- **Circuit Breaker:** Proteção contra falhas em cascata
- **Retry Logic:** Exponential backoff
- **Error Logging:** Structured logging com alertas

***

## 5. Especificação da API

### 5.1 Estrutura Base da API

**Base URL:** `https://api.global-regime-analysis.com/v1`

**Autenticação:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```


### 5.2 Endpoints Principais

#### 5.2.1 Global Regimes

```python
# GET /global-regimes/current
{
  "current_regime": "GLOBAL_EXPANSION",
  "regime_probabilities": {
    "GLOBAL_RECESSION": 0.05,
    "GLOBAL_RECOVERY": 0.15,
    "GLOBAL_EXPANSION": 0.70,
    "GLOBAL_CONTRACTION": 0.10
  },
  "regime_characteristics": {
    "duration_months": 18,
    "typical_indicators": {
      "global_gdp_growth": [2.5, 4.0],
      "global_inflation": [2.0, 3.5],
      "vix_range": [12.0, 20.0]
    }
  },
  "confidence": 0.85,
  "last_updated": "2025-09-26T08:00:00Z"
}

# GET /global-regimes/forecast?horizon=12
{
  "forecast_horizon": 12,
  "monthly_forecast": [
    {
      "month": 1,
      "most_likely_regime": "GLOBAL_EXPANSION",
      "regime_probabilities": {
        "GLOBAL_RECESSION": 0.08,
        "GLOBAL_RECOVERY": 0.12,
        "GLOBAL_EXPANSION": 0.65,
        "GLOBAL_CONTRACTION": 0.15
      },
      "confidence_interval": [0.60, 0.70]
    }
    // ... mais 11 meses
  ],
  "scenario_analysis": {
    "base_case": 0.65,
    "optimistic": 0.80,
    "pessimistic": 0.45
  }
}

# GET /global-regimes/validation
{
  "model_performance": {
    "out_of_sample_accuracy": 0.78,
    "regime_identification_score": 0.82,
    "transition_prediction_score": 0.71
  },
  "last_validation": "2025-09-20T00:00:00Z",
  "next_validation": "2025-10-20T00:00:00Z",
  "model_version": "2.1.3"
}
```


#### 5.2.2 Brazil Spillovers

```python
# GET /brazil-spillovers/current
{
  "aggregate_spillover": {
    "total_impact": -0.25,
    "impact_breakdown": {
      "trade_channel": -0.15,
      "commodity_channel": 0.30,
      "financial_channel": -0.20,
      "supply_chain_channel": -0.20
    },
    "confidence_interval": [-0.35, -0.15]
  },
  "channel_details": {
    "trade_channel": {
      "impact_magnitude": -0.15,
      "key_drivers": ["us_demand_slowdown", "china_import_reduction"],
      "affected_sectors": ["manufacturing", "agriculture"]
    },
    "commodity_channel": {
      "impact_magnitude": 0.30,
      "key_commodities": {
        "iron_ore": 0.12,
        "soybeans": 0.08,
        "crude_oil": 0.06,
        "coffee": 0.04
      }
    }
  }
}

# GET /brazil-spillovers/forecast?horizon=6
{
  "spillover_forecast": [
    {
      "month": 1,
      "expected_impact": -0.22,
      "channel_breakdown": {
        "trade": -0.12,
        "commodity": 0.25,
        "financial": -0.18,
        "supply_chain": -0.17
      },
      "confidence_interval": [-0.32, -0.12]
    }
    // ... mais 5 meses
  ]
}
```


#### 5.2.3 Brazil Indicators

```python
# GET /brazil-indicators/forecast
{
  "indicators_forecast": {
    "gdp_growth": {
      "current_quarter": 1.8,
      "next_quarter": 1.5,
      "confidence_interval": [1.2, 1.8],
      "regime_sensitivity": {
        "global_recession": 0.2,
        "global_expansion": 2.8
      }
    },
    "inflation": {
      "current_month": 4.2,
      "12_month_forecast": 4.8,
      "target_range": [3.0, 6.0],
      "spillover_contribution": 0.6
    },
    "exchange_rate": {
      "current": 5.25,
      "forecast_3m": 5.45,
      "volatility": 0.15,
      "regime_conditional": {
        "global_stress": 6.20,
        "global_calm": 4.80
      }
    }
  }
}
```


### 5.3 Webhook Events

```python
# Webhook payload para mudança de regime
{
  "event_type": "regime_change",
  "timestamp": "2025-09-26T08:15:00Z",
  "data": {
    "previous_regime": "GLOBAL_EXPANSION",
    "new_regime": "GLOBAL_CONTRACTION",
    "transition_probability": 0.85,
    "estimated_duration": "6-12 months",
    "brazil_impact_estimate": -0.40
  }
}

# Webhook payload para alerta de spillover
{
  "event_type": "spillover_alert",
  "timestamp": "2025-09-26T09:00:00Z",
  "severity": "high",
  "data": {
    "channel": "commodity_channel",
    "commodity": "iron_ore",
    "price_change": -15.5,
    "brazil_impact": -0.08,
    "affected_regions": ["Minas Gerais", "Pará"]
  }
}
```


***

## 6. Especificação do Frontend

### 6.1 Arquitetura Next.js 15

**Estrutura de Diretórios:**

```
src/
├── app/                    # App Router (Next.js 15)
│   ├── dashboard/         # Dashboard principal
│   ├── global-regimes/    # Análise de regimes globais
│   ├── brazil-spillovers/ # Spillovers para o Brasil
│   ├── forecasts/         # Previsões
│   └── api/              # API routes internas
├── components/            # Componentes reutilizáveis
│   ├── ui/               # shadcn/ui components
│   ├── charts/           # Componentes de gráficos
│   └── layouts/          # Layouts da aplicação
├── lib/                  # Utilitários e configurações
├── hooks/                # Custom hooks
├── stores/              # Zustand stores
└── types/               # TypeScript types
```


### 6.2 Componentes Principais

#### 6.2.1 Dashboard Principal

```typescript
// components/dashboard/MainDashboard.tsx
interface DashboardProps {
  globalRegimes: GlobalRegimeData;
  brazilSpillovers: SpilloverData;
  indicators: BrazilIndicators;
  realTimeUpdates?: boolean;
}

const MainDashboard = ({
  globalRegimes,
  brazilSpillovers,
  indicators,
  realTimeUpdates = true
}: DashboardProps) => {
  return (
    <div className="dashboard-container">
      <RegimeOverviewCard regime={globalRegimes.current} />
      <SpilloverSummaryCard spillovers={brazilSpillovers} />
      <IndicatorsForecastCard indicators={indicators} />
      <AlertsPanel />
    </div>
  );
};
```


#### 6.2.2 Visualizações Interativas

```typescript
// components/charts/RegimeTimelineChart.tsx
interface RegimeTimelineProps {
  data: RegimeTimeSeriesData[];
  interactive?: boolean;
  height?: number;
}

const RegimeTimelineChart = ({
  data,
  interactive = true,
  height = 400
}: RegimeTimelineProps) => {
  const [selectedPeriod, setSelectedPeriod] = useState<DateRange>();
  
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <XAxis dataKey="date" />
        <YAxis />
        <CartesianGrid strokeDasharray="3 3" />
        <Line 
          type="monotone" 
          dataKey="regime_probability" 
          stroke="#8884d8" 
        />
        <ReferenceLine y={0.5} stroke="red" strokeDasharray="2 2" />
        <Tooltip content={<RegimeTooltip />} />
        <Brush 
          dataKey="date" 
          height={30}
          onChange={setSelectedPeriod}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
```


#### 6.2.3 Painel de Spillovers

```typescript
// components/spillovers/SpilloverPanel.tsx
interface SpilloverPanelProps {
  spillovers: ChannelSpillovers;
  country: string;
  timeHorizon: number;
}

const SpilloverPanel = ({
  spillovers,
  country,
  timeHorizon
}: SpilloverPanelProps) => {
  return (
    <Card className="spillover-panel">
      <CardHeader>
        <CardTitle>Spillovers para {country}</CardTitle>
      </CardHeader>
      <CardContent>
        <SpilloverSankeyDiagram data={spillovers} />
        <ChannelBreakdownTable channels={spillovers.channels} />
        <ImpactForecastChart 
          forecast={spillovers.forecast} 
          horizon={timeHorizon} 
        />
      </CardContent>
    </Card>
  );
};
```


### 6.3 State Management (Zustand)

```typescript
// stores/regimeStore.ts
interface RegimeState {
  globalRegimes: GlobalRegimeData | null;
  brazilSpillovers: SpilloverData | null;
  indicators: BrazilIndicators | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchGlobalRegimes: () => Promise<void>;
  fetchBrazilSpillovers: () => Promise<void>;
  fetchIndicators: () => Promise<void>;
  setRealTimeUpdates: (enabled: boolean) => void;
}

const useRegimeStore = create<RegimeState>((set, get) => ({
  globalRegimes: null,
  brazilSpillovers: null,
  indicators: null,
  loading: false,
  error: null,
  
  fetchGlobalRegimes: async () => {
    set({ loading: true, error: null });
    try {
      const data = await regimeAPI.getGlobalRegimes();
      set({ globalRegimes: data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
  
  fetchBrazilSpillovers: async () => {
    // Implementação similar...
  }
}));
```


### 6.4 Real-time Updates

```typescript
// hooks/useRealTimeUpdates.ts
const useRealTimeUpdates = (enabled: boolean = true) => {
  const store = useRegimeStore();
  
  useEffect(() => {
    if (!enabled) return;
    
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL);
    
    ws.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data);
      
      switch (type) {
        case 'regime_update':
          store.fetchGlobalRegimes();
          break;
        case 'spillover_update':
          store.fetchBrazilSpillovers();
          break;
        case 'indicator_update':
          store.fetchIndicators();
          break;
      }
    };
    
    return () => ws.close();
  }, [enabled, store]);
};
```


***

## 7. Integração de Dados

### 7.1 Fontes de Dados

#### 7.1.1 Dados Globais

| Fonte | Dados | Frequência | API/Método |
| :-- | :-- | :-- | :-- |
| FRED | US GDP, CPI, Unemployment, Fed Rate | Monthly/Quarterly | REST API |
| OECD | G7 Leading Indicators, GDP, CPI | Monthly/Quarterly | REST API |
| Yahoo Finance | VIX, Stock Indices, Commodity Prices | Daily | yfinance library |
| World Bank | Trade Data, Commodity Indices | Monthly/Quarterly | REST API |
| ECB | EUR indicators, Policy Rates | Monthly | REST API |

#### 7.1.2 Dados Brasil

| Fonte | Dados | Frequência | API/Método |
| :-- | :-- | :-- | :-- |
| IBGE | PIB, IPCA, PNAD | Monthly/Quarterly | Web Scraping |
| BCB | SELIC, Câmbio, IBC-Br, Expectativas | Daily/Monthly | REST API |
| MDIC | Comércio Exterior | Monthly | REST API |
| IPEADATA | Séries históricas diversas | Monthly/Quarterly | REST API |

### 7.2 Pipeline de Dados

```python
# data_pipeline/collectors/global_collector.py
class GlobalDataCollector:
    """Coletor de dados globais com retry e validação"""
    
    def __init__(self):
        self.sources = {
            'fred': FREDCollector(),
            'oecd': OECDCollector(),
            'yahoo': YahooFinanceCollector(),
            'worldbank': WorldBankCollector()
        }
    
    async def collect_all_data(self) -> Dict[str, pd.DataFrame]:
        """Coleta dados de todas as fontes de forma assíncrona"""
        
        tasks = []
        for source_name, collector in self.sources.items():
            task = asyncio.create_task(
                self._collect_with_retry(source_name, collector)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados e tratar erros
        collected_data = {}
        for source_name, result in zip(self.sources.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Erro ao coletar {source_name}: {result}")
                # Usar dados em cache se disponível
                cached_data = await self._get_cached_data(source_name)
                if cached_data is not None:
                    collected_data[source_name] = cached_data
            else:
                collected_data[source_name] = result
        
        return collected_data
    
    async def _collect_with_retry(self, source_name: str, 
                                 collector: BaseCollector, 
                                 max_retries: int = 3) -> pd.DataFrame:
        """Coleta com retry exponential backoff"""
        
        for attempt in range(max_retries):
            try:
                data = await collector.collect()
                
                # Validar dados coletados
                if self._validate_data(data):
                    await self._cache_data(source_name, data)
                    return data
                else:
                    raise ValueError(f"Dados inválidos de {source_name}")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"Tentativa {attempt + 1} falhou para {source_name}. "
                             f"Aguardando {wait_time}s...")
                await asyncio.sleep(wait_time)
```


### 7.3 Validação e Limpeza

```python
# data_pipeline/validation/data_validator.py
class DataValidator:
    """Validação robusta de dados econômicos"""
    
    def __init__(self):
        self.validation_rules = {
            'gdp_growth': {'min': -20.0, 'max': 20.0},
            'inflation': {'min': -5.0, 'max': 50.0},
            'unemployment': {'min': 0.0, 'max': 30.0},
            'policy_rate': {'min': -2.0, 'max': 25.0},
            'vix': {'min': 5.0, 'max': 100.0}
        }
    
    async def validate_dataset(self, data: pd.DataFrame, 
                              source: str) -> ValidationResult:
        """Validação completa do dataset"""
        
        validation_result = ValidationResult()
        
        # 1. Validação estrutural
        structural_issues = self._validate_structure(data)
        validation_result.add_issues('structural', structural_issues)
        
        # 2. Validação de valores
        value_issues = self._validate_values(data)
        validation_result.add_issues('values', value_issues)
        
        # 3. Validação temporal
        temporal_issues = self._validate_temporal_consistency(data)
        validation_result.add_issues('temporal', temporal_issues)
        
        # 4. Validação de outliers
        outlier_issues = self._detect_outliers(data)
        validation_result.add_issues('outliers', outlier_issues)
        
        # 5. Validação cruzada
        if source in ['fred', 'oecd']:
            cross_validation_issues = await self._cross_validate(data, source)
            validation_result.add_issues('cross_validation', cross_validation_issues)
        
        return validation_result
    
    def _detect_outliers(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Detecção de outliers usando múltiplos métodos"""
        
        issues = []
        
        for column in data.select_dtypes(include=[np.number]).columns:
            # Método 1: IQR
            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            iqr_outliers = data[(data[column] < lower_bound) | 
                              (data[column] > upper_bound)]
            
            # Método 2: Z-Score modificado
            median = data[column].median()
            mad = np.median(np.abs(data[column] - median))
            modified_z_scores = 0.6745 * (data[column] - median) / mad
            zscore_outliers = data[np.abs(modified_z_scores) > 3.5]
            
            # Combinar resultados
            all_outliers = pd.concat([iqr_outliers, zscore_outliers]).drop_duplicates()
            
            if len(all_outliers) > 0:
                issues.append(ValidationIssue(
                    level='warning',
                    column=column,
                    message=f"Detectados {len(all_outliers)} outliers",
                    affected_rows=all_outliers.index.tolist()
                ))
        
        return issues
```


***

## 8. Cronograma de Desenvolvimento

### 8.1 Fases do Projeto

#### **Fase 1: Fundação (Semanas 1-4)**

- **Semana 1-2:** Configuração da infraestrutura básica
    - Setup do repositório e CI/CD
    - Containerização com Docker
    - Configuração de bancos de dados
    - Framework básico da API (FastAPI)
    - Setup inicial do frontend (Next.js 15)
- **Semana 3-4:** Pipeline de dados básico
    - Implementação dos coletores de dados
    - Validação e limpeza de dados
    - Armazenamento em TimescaleDB
    - Testes unitários dos coletores


#### **Fase 2: Core Analytics (Semanas 5-10)**

- **Semana 5-6:** Implementação RS-GVAR
    - Modelo Markov-Switching básico
    - Seleção de número de regimes
    - Validação estatística inicial
- **Semana 7-8:** Análise de spillovers
    - Implementação dos 4 canais de transmissão
    - Cálculos de elasticidades
    - Agregação de efeitos
- **Semana 9-10:** Sistema de previsões
    - Previsões regime-condicionais
    - Intervalos de confiança
    - Validação fora da amostra


#### **Fase 3: API e Backend (Semanas 11-14)**

- **Semana 11-12:** API completa
    - Todos os endpoints funcionais
    - Autenticação e autorização
    - Rate limiting e segurança
    - Documentação OpenAPI
- **Semana 13-14:** Otimização e caching
    - Redis para cache
    - Otimização de queries
    - Monitoramento de performance


#### **Fase 4: Frontend (Semanas 15-20)**

- **Semana 15-16:** Dashboards básicos
    - Layout principal
    - Componentes de visualização
    - Integração com API
- **Semana 17-18:** Visualizações avançadas
    - Gráficos interativos
    - Mapas e sankey diagrams
    - Relatórios automatizados
- **Semana 19-20:** UX e responsividade
    - Mobile-first design
    - Testes de usabilidade
    - Otimização de performance


#### **Fase 5: Validação e Deploy (Semanas 21-24)**

- **Semana 21-22:** Testes extensivos
    - Testes de integração
    - Testes de carga
    - Validação científica
- **Semana 23-24:** Deploy e monitoramento
    - Deploy em produção
    - Monitoramento e alertas
    - Documentação final


### 8.2 Marcos Importantes

| Marco | Semana | Entregável |
| :-- | :-- | :-- |
| M1 | 4 | Pipeline de dados funcional |
| M2 | 8 | Modelos RS-GVAR implementados |
| M3 | 10 | Sistema de spillovers completo |
| M4 | 14 | API completa e documentada |
| M5 | 18 | Frontend com dashboards principais |
| M6 | 22 | Sistema completo testado |
| M7 | 24 | Sistema em produção |

### 8.3 Recursos Necessários

#### **Equipe Sugerida:**

- **1 Senior Full-Stack Developer** (Python + TypeScript)
- **1 Data Scientist** (especialista em econometria)
- **1 Frontend Developer** (Next.js/React expert)
- **1 DevOps Engineer** (infraestrutura e deployment)


#### **Infraestrutura:**

- **Servidor Principal:** 16 CPU cores, 64GB RAM, 1TB SSD
- **Database Server:** PostgreSQL + TimescaleDB
- **Cache Server:** Redis Cluster
- **CDN:** Para assets estáticos
- **Monitoring:** Prometheus + Grafana stack

***

## 9. Critérios de Aceitação e Testes

### 9.1 Critérios de Aceitação Global

#### **Científicos:**

- Modelos passam em todos os testes de validação estatística
- Acurácia fora da amostra > 75% para identificação de regimes
- Intervalos de confiança calibrados corretamente
- Backtesting histórico com performance satisfatória


#### **Técnicos:**

- API atende todos os requisitos de performance
- Frontend responsivo em dispositivos móveis e desktop
- Sistema suporta carga esperada sem degradação
- Cobertura de testes > 85%


#### **Operacionais:**

- Uptime > 99.9% durante período de teste
- Backup e recovery testados com sucesso
- Alertas funcionando corretamente
- Documentação completa e atualizada


### 9.2 Plano de Testes

#### **Testes Unitários (Coverage > 85%):**

```python
# tests/test_regime_analysis.py
class TestRegimeAnalysis:
    
    def test_rs_gvar_model_fitting(self):
        """Teste da implementação RS-GVAR"""
        # Dados sintéticos conhecidos
        data = generate_regime_switching_data(n_regimes=3, n_obs=500)
        
        # Ajustar modelo
        model = RSGVARModel()
        fitted_model = model.fit(data)
        
        # Verificações
        assert fitted_model.k_regimes == 3
        assert fitted_model.converged == True
        assert len(fitted_model.regime_labels) == 500
        
    def test_spillover_calculation(self):
        """Teste dos cálculos de spillover"""
        global_shock = GlobalShock(type='recession', magnitude=-0.5)
        brazil_model = BrazilSpilloverModel()
        
        spillovers = brazil_model.calculate_spillovers(global_shock)
        
        # Verificar que spillovers estão dentro de ranges esperados
        assert -2.0 <= spillovers.total_impact <= 2.0
        assert len(spillovers.channel_breakdown) == 4
```


#### **Testes de Integração:**

```python
# tests/integration/test_api_endpoints.py
class TestAPIIntegration:
    
    async def test_global_regimes_endpoint(self):
        """Teste do endpoint de regimes globais"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/v1/global-regimes/current")
            
            assert response.status_code == 200
            data = response.json()
            assert "current_regime" in data
            assert "regime_probabilities" in data
            assert sum(data["regime_probabilities"].values()) == pytest.approx(1.0)
```


#### **Testes de Performance:**

```python
# tests/performance/test_load.py
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def test_api_load():
    """Teste de carga da API"""
    
    async def make_request():
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.test/v1/global-regimes/current") as response:
                return await response.json()
    
    # 1000 requisições concorrentes
    tasks = [make_request() for _ in range(1000)]
    start_time = time.time()
    
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verificações de performance
    assert end_time - start_time < 30.0  # Máximo 30 segundos
    assert len([r for r in results if 'error' not in r]) >= 950  # 95% de sucesso
```


### 9.3 Validação Científica

#### **Backtesting Histórico:**

```python
# validation/backtesting.py
class BacktestingFramework:
    
    def run_historical_backtest(self, start_date: str, end_date: str):
        """Validação com dados históricos"""
        
        results = {}
        
        # Janela deslizante de 5 anos para treinamento
        for train_end in pd.date_range(start_date, end_date, freq='M'):
            train_start = train_end - pd.DateOffset(years=5)
            test_end = train_end + pd.DateOffset(months=6)
            
            # Treinar modelo nos dados históricos
            train_data = self.get_data(train_start, train_end)
            model = self.train_model(train_data)
            
            # Testar nos 6 meses seguintes
            test_data = self.get_data(train_end, test_end)
            predictions = model.predict(test_data)
            
            # Calcular métricas
            accuracy = self.calculate_regime_accuracy(predictions, test_data)
            results[train_end] = accuracy
        
        return results
```


***

## 10. Considerações de Deployment

### 10.1 Infraestrutura de Produção

#### **Arquitetura de Deploy:**

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    image: regime-analysis-api:latest
    replicas: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: regime-analysis-frontend:latest
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      - POSTGRES_DB=regime_analysis
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
```


#### **Monitoramento:**

```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      
  alert-manager:
    image: prom/alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
```


### 10.2 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Backend Tests
        run: |
          cd backend
          python -m pytest tests/ --cov=src --cov-report=xml
          
      - name: Run Frontend Tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false
      
      - name: Security Scan
        run: |
          docker run --rm -v $(pwd):/app securecodewarrior/docker-security-scan
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Deploy to Production
        run: |
          # Deploy logic here
          kubectl apply -f k8s/
          kubectl rollout status deployment/regime-analysis-api
```


### 10.3 Backup e Disaster Recovery

```bash
#!/bin/bash
# scripts/backup.sh

# Backup do banco de dados
pg_dump $DATABASE_URL | gzip > "backups/db-$(date +%Y%m%d_%H%M%S).sql.gz"

# Backup dos modelos treinados
tar -czf "backups/models-$(date +%Y%m%d_%H%M%S).tar.gz" models/

# Upload para S3
aws s3 sync backups/ s3://regime-analysis-backups/

# Limpar backups antigos (manter 30 dias)
find backups/ -name "*.gz" -mtime +30 -delete
```


***

## 11. Orçamento e Timeline Detalhado

### 11.1 Estimativa de Custos

#### **Desenvolvimento (24 semanas):**

| Recurso | Quantidade | Custo/mês | Total |
| :-- | :-- | :-- | :-- |
| Senior Full-Stack Developer | 1 | R\$ 18.000 | R\$ 108.000 |
| Data Scientist (Econometrista) | 1 | R\$ 20.000 | R\$ 120.000 |
| Frontend Developer | 1 | R\$ 14.000 | R\$ 84.000 |
| DevOps Engineer | 0.5 | R\$ 16.000 | R\$ 48.000 |
| **Total Desenvolvimento** |  |  | **R\$ 360.000** |

#### **Infraestrutura (anual):**

| Item | Especificação | Custo/mês | Custo/ano |
| :-- | :-- | :-- | :-- |
| Servidor Principal | 16 CPU, 64GB RAM | R\$ 2.000 | R\$ 24.000 |
| Database Server | Managed PostgreSQL | R\$ 800 | R\$ 9.600 |
| CDN + Storage | 1TB transfer, 500GB storage | R\$ 300 | R\$ 3.600 |
| Monitoring Stack | Datadog Pro | R\$ 400 | R\$ 4.800 |
| **Total Infraestrutura** |  |  | **R\$ 42.000** |

#### **Licenças e Ferramentas:**

| Ferramenta | Finalidade | Custo/ano |
| :-- | :-- | :-- |
| GitHub Enterprise | Repositório privado + CI/CD | R\$ 2.400 |
| JetBrains All Products | IDEs | R\$ 3.000 |
| Figma Professional | Design | R\$ 720 |
| **Total Ferramentas** |  | **R\$ 6.120** |

#### **Custo Total Projeto:**

- **Desenvolvimento:** R\$ 360.000
- **Infraestrutura (6 meses):** R\$ 21.000
- **Ferramentas:** R\$ 6.120
- **Contingência (15%):** R\$ 58.068
- **TOTAL:** R\$ 445.188


### 11.2 ROI Projetado

#### **Receita Potencial (anual):**

- **Subscription SaaS:** R\$ 500-2000/mês por cliente
- **Meta de clientes (ano 1):** 50-100 clientes
- **Receita estimada ano 1:** R\$ 300.000 - R\$ 2.400.000
- **ROI esperado:** 65% - 540%

***

## 12. Conclusão

Este documento especifica um sistema robusto e cientificamente válido para análise de regimes econômicos globais e previsão de spillovers para o Brasil. A arquitetura proposta combina:

- **Rigor Científico:** Modelos RS-GVAR validados
- **Robustez Técnica:** API escalável e frontend moderno
- **Praticidade:** Interface intuitiva e insights acionáveis
- **Escalabilidade:** Arquitetura preparada para crescimento

O projeto representa uma oportunidade significativa de criar valor tanto acadêmico quanto comercial, estabelecendo nova referência em análise macroeconômica preditiva para economias emergentes.

**Próximos Passos:**

1. Aprovação dos stakeholders
2. Definição da equipe de desenvolvimento
3. Setup inicial da infraestrutura
4. Início da Fase 1 (Semanas 1-4)

***

*Documento gerado em 26 de Setembro de 2025*
*Versão 1.0 - Para aprovação*

