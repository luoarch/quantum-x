# Quantum X - Sistema Avançado de Trading Signals

Sistema de geração de sinais de trading baseado em **metodologias científicas avançadas**, combinando Markov-Switching models, Hierarchical Risk Parity e sinais probabilísticos para otimização de portfólio.

## 🚀 **Status do Projeto**

### ✅ **IMPLEMENTADO (Sistema Avançado)**
- **Markov-Switching Model** com statsmodels (regimes econômicos)
- **Hierarchical Risk Parity (HRP)** para alocação de portfólio
- **Sinais Probabilísticos** baseados em regimes
- **Yield Curve Indicators** (spread 10Y-2Y)
- **Backtesting** com ativos reais (Tesouro IPCA+, BOVA11)
- **Logs detalhados** para debug profundo

### 🔄 **EM DESENVOLVIMENTO**
- Dashboard Next.js/React
- Integração em tempo real
- Deploy em produção

## 📊 **Resultados da Estratégia Avançada**

```
📈 PERFORMANCE ATUAL:
- Sharpe Ratio: 3.50-5.15
- Retorno Esperado: 160-220%
- Diversificação Efetiva: 2.00
- Confiança Média: 81.3%
- Regimes Identificados: RECESSION, RECOVERY, EXPANSION, CONTRACTION
```

## 🏗️ **Arquitetura do Sistema**

### **Backend (Python)**
```
app/
├── core/                    # Configurações e database
├── models/                  # Modelos SQLAlchemy
├── services/
│   ├── data_sources/        # APIs (BCB, OECD, IPEA)
│   ├── signal_generation/    # Core engine
│   │   ├── markov_switching_model.py      # Regimes econômicos
│   │   ├── hierarchical_risk_parity.py    # Alocação HRP
│   │   ├── probabilistic_signal_generator.py # Sinais probabilísticos
│   │   ├── yield_curve_indicators.py      # Curva de juros
│   │   └── cli_calculator.py              # CLI tradicional
│   ├── backtesting/         # Simulação histórica
│   └── ml/                   # Machine Learning
├── api/v1/                  # Endpoints REST
└── schemas/                 # Validação Pydantic
```

### **Frontend (Next.js - Planejado)**
```typescript
// Dashboard em tempo real
- CLI Charts (Chart.js/D3)
- Signal Panel (React)
- Position Management
- SHAP Explanations
```

## 🛠️ **Instalação e Configuração**

### **Pré-requisitos**
- Python 3.9+
- PostgreSQL 13+
- Redis (opcional)

### **Setup Rápido**
```bash
# 1. Clone e instale
git clone <repository-url>
cd quantum-x
pip install -r requirements.txt

# 2. Configure ambiente
cp env.example .env
# Edite .env com suas configurações

# 3. Configure database
createdb quantum_x_db

# 4. Execute
python run.py
```

### **Variáveis de Ambiente**
```env
# Database
DATABASE_URL=postgresql://luoarch:postgres@localhost:5432/quantum_x_db
REDIS_URL=redis://localhost:6379/0

# APIs
BCB_API_KEY=
OECD_API_KEY=
TRADING_ECONOMICS_API_KEY=

# Aplicação
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

## 📈 **APIs e Endpoints**

### **Dados Econômicos**
- `POST /api/v1/data/collect` - Coleta de dados
- `GET /api/v1/data/series` - Lista séries
- `GET /api/v1/data/series/{code}` - Dados específicos
- `GET /api/v1/data/stats` - Estatísticas

### **Sinais de Trading**
- `GET /api/v1/signals/` - Sinais atuais
- `GET /api/v1/signals/backtest` - Backtesting
- `GET /api/v1/signals/health` - Health check

## 🧠 **Metodologias Científicas**

### **1. Markov-Switching Model**
```python
# Identifica regimes econômicos automaticamente
from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression

model = MarkovAutoregression(
    data, k_regimes=4, order=1,
    switching_ar=True, switching_variance=True
)
```

### **2. Hierarchical Risk Parity (HRP)**
```python
# Alocação robusta baseada em clustering
- Clustering hierárquico de ativos
- Alocação baseada em risco, não retorno
- Diversificação efetiva > 2.0
```

### **3. Sinais Probabilísticos**
```python
# Sinais baseados em probabilidades de regime
if Pr(Regime="EXPANSION") > 80% and yield_spread < 0:
    signal = "BUY"
elif Pr(Regime="RECESSION") > 60%:
    signal = "SELL"
```

## 📊 **Fontes de Dados**

### **Banco Central do Brasil (BCB)**
- IPCA (433) - Inflação
- SELIC (432) - Taxa de juros
- PIB (4380) - Produto Interno Bruto
- Câmbio (1) - USD/BRL
- Produção Industrial (21859)

### **OECD**
- CLI Brasil, EUA, China, Global
- Metodologia científica comprovada

### **IPEA**
- Dados econômicos brasileiros
- Séries históricas longas

## 🧪 **Testes e Validação**

### **Testes Essenciais**
```bash
# Teste da estratégia avançada
python test_advanced_strategy.py

# Backtesting com ativos reais
python test_real_assets_backtest.py

# Sistema de robustez
python test_robustness_system.py
```

### **Métricas de Validação**
- **Sharpe Ratio**: > 3.0 (atual: 3.50-5.15)
- **Hit Rate**: > 65% para sinais de virada
- **Maximum Drawdown**: < 20%
- **Alpha anual**: > 2% para títulos públicos

## 🎯 **Próximos Passos**

### **Fase 1: Dashboard (Semana 1-2)**
- [ ] Interface Next.js/React
- [ ] Gráficos CLI em tempo real
- [ ] Painel de sinais
- [ ] Sistema de alertas

### **Fase 2: Produção (Semana 3-4)**
- [ ] Deploy em cloud (AWS/GCP)
- [ ] Monitoramento em tempo real
- [ ] Integração com corretoras
- [ ] Documentação para clientes

## 📝 **Exemplos de Uso**

### **Coleta de Dados**
```python
from app.services.robust_data_collector import RobustDataCollector

collector = RobustDataCollector(db_session)
data = collector.collect_all_series()
```

### **Geração de Sinais**
```python
from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator

generator = ProbabilisticSignalGenerator()
signals = generator.generate_signals(economic_data, asset_returns)
```

### **Backtesting**
```python
from app.services.backtesting.historical_backtester import HistoricalBacktester

backtester = HistoricalBacktester()
results = backtester.run_backtest(start_date, end_date)
```

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

---

**Quantum X** - Sistema de Trading Signals baseado em ciência, não em especulação.