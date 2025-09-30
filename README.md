# 🏦 Quantum-X: Spillover Intelligence FED-Selic

**API de Previsão Probabilística da Selic Condicionada ao Fed**

## 🎯 **Visão Geral**

Sistema de previsão probabilística que mapeia movimentos do Fed para respostas da Selic, usando **Local Projections** e **BVAR com priors Minnesota** para amostras pequenas (~20 observações).

### **Objetivo**
- **Input**: Data e magnitude do movimento do Fed (ex.: +25 bps)
- **Output**: Previsão do "quando" (horizonte) e "quanto" (bps) a Selic se move, com intervalos de confiança e probabilidades por janela do Copom

## 🔬 **Fundamentação Científica**

### **Metodologia Principal**
- **Local Projections (Jordà)**: Estimação robusta de respostas por horizonte com shrinkage
- **BVAR com Prior Minnesota**: Previsões condicionais para cenários específicos
- **Validação**: Testes de estacionariedade e detecção de quebras estruturais

### **Por que Funciona com Poucos Dados**
- **LP**: Mais robusto a misspecificação que VAR tradicional
- **BVAR com Priors**: Reduz sobreparametrização via regularização
- **Shrinkage**: Estabiliza estimativas com amostras pequenas

## 🚀 **Instalação**

```bash
# Clonar repositório
git clone <repo-url>
cd quantum-x

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar API
python main.py
```

## 📊 **API Endpoints**

### **POST /predict/selic-from-fed**
Previsão probabilística da Selic condicionada ao Fed

**Request:**
```json
{
  "fed_decision_date": "2025-10-29",
  "fed_move_bps": 25,
  "fed_move_dir": 1,
  "fed_surprise_bps": 10,
  "horizons_months": [1, 3, 6, 12],
  "model_version": "v1.0.0",
  "regime_hint": "normal"
}
```

**Response:**
```json
{
  "expected_move_bps": 25,
  "horizon_months": "1-3",
  "prob_move_within_next_copom": 0.62,
  "ci80_bps": [0, 50],
  "ci95_bps": [-25, 75],
  "per_meeting": [
    { "copom_date": "2025-11-05", "delta_bps": 25, "probability": 0.41 },
    { "copom_date": "2025-12-17", "delta_bps": 25, "probability": 0.21 }
  ],
  "distribution": [
    { "delta_bps": -25, "probability": 0.07 },
    { "delta_bps": 0, "probability": 0.18 },
    { "delta_bps": 25, "probability": 0.52 },
    { "delta_bps": 50, "probability": 0.20 }
  ],
  "model_metadata": {
    "version": "v1.0.0",
    "trained_at": "2025-09-25T12:00:00Z",
    "data_hash": "sha256:...abcd",
    "methodology": "LP primary, BVAR fallback"
  },
  "rationale": "Resposta estimada positiva ao choque de +25 bps do Fed; maior massa de probabilidade no próximo Copom, alta incerteza devido à amostra curta."
}
```

## 🏗️ **Arquitetura**

```
quantum-x/
├── src/
│   ├── models/
│   │   ├── local_projections.py    # Núcleo LP com shrinkage
│   │   ├── bvar_minnesota.py       # BVAR com prior Minnesota
│   │   └── stationarity_tests.py   # Validação científica
│   ├── data/
│   │   ├── fed_data.py             # Coleta dados Fed
│   │   ├── selic_data.py           # Coleta dados Selic/Copom
│   │   └── pipeline.py             # Pipeline de preparação
│   ├── forecasting/
│   │   ├── lp_forecaster.py        # Previsões via LP
│   │   ├── bvar_forecaster.py      # Previsões via BVAR
│   │   └── probability_engine.py   # Conversão para probabilidades
│   └── api/
│       ├── endpoints.py            # FastAPI endpoints
│       ├── schemas.py              # Pydantic schemas
│       └── middleware.py           # Auth, logging, etc.
├── data/
│   ├── raw/                        # Dados brutos
│   ├── processed/                  # Dados processados
│   └── models/                     # Modelos treinados
├── tests/
│   ├── unit/                       # Testes unitários
│   ├── integration/                # Testes de integração
│   └── backtests/                  # Validação histórica
├── requirements.txt
├── main.py
└── README.md
```

## 🔬 **Validação Científica**

### **Testes Implementados**
- ✅ **Estacionariedade**: ADF, KPSS, DF-GLS, Phillips-Perron
- ✅ **Quebras Estruturais**: Zivot-Andrews, Bai-Perron
- ✅ **Heterocedasticidade**: Testes de robustez
- ✅ **Amostras Pequenas**: Validação Ng-Perron

### **Benchmarks Históricos**
- ✅ **Nelson-Plosser (1982)**: Padrões macroeconômicos
- ✅ **Elliott et al. (1996)**: DF-GLS superior ao ADF
- ✅ **Cavaliere & Taylor (2007)**: Robustez à heterocedasticidade

## 📚 **Referências Científicas**

1. **Jordà, Ò. (2005)**: "Estimation and Inference of Impulse Responses by Local Projections"
2. **Elliott, G., Rothenberg, T. J., & Stock, J. H. (1996)**: "Efficient Tests for an Autoregressive Unit Root"
3. **Ng, S., & Perron, P. (2001)**: "Lag Length Selection and the Construction of Unit Root Tests"
4. **Bai, J., & Perron, P. (1998)**: "Estimating and Testing Linear Models with Multiple Structural Changes"
5. **Nelson, C. R., & Plosser, C. I. (1982)**: "Trends and Random Walks in Macroeconomic Time Series"

## 🎯 **Roadmap**

- **Semana 1-2**: Pipeline de dados e treinador LP, API esqueleto
- **Semana 3-4**: BVAR condicional, backtests, observabilidade
- **Semana 5**: Hardening, documentação e produção

## ⚠️ **Limitações**

- **Amostra pequena**: ~20 observações pareadas Fed-Selic
- **Bandas largas**: Incerteza alta devido ao N pequeno
- **Comunicação probabilística**: Não determinística, mas probabilística

## 📄 **Licença**

MIT License - Veja LICENSE para detalhes.

---

**Quantum-X Project - Spillover Intelligence**  
**Versão 2.0 - Nova Abordagem FED-Selic**
