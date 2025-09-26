# Global Economic Regime Analysis & Brazil Spillover Prediction System

## 📋 Visão Geral

Sistema científico para **análise de regimes econômicos globais** e **previsão de spillovers para o Brasil** baseado em metodologias econométricas avançadas.

**Versão:** 1.0.0  
**Baseado em:** Documento de Requisitos do Sistema (DRS) v1.0

## 🎯 Objetivos

### Objetivos Primários
- ✅ Identificar regimes econômicos globais em tempo real usando RS-GVAR
- ✅ Quantificar spillovers econômicos para o Brasil via 4 canais de transmissão
- ✅ Prover previsões regime-condicionais para indicadores macroeconômicos brasileiros
- ✅ Oferecer interface intuitiva para análise e visualização de resultados

### Objetivos Secundários
- ✅ Estabelecer framework de validação contínua dos modelos
- ✅ Implementar sistema de alertas para mudanças de regime
- ✅ Criar repositório de cenários históricos para backtesting
- ✅ Desenvolver API robusta para integração com sistemas externos

## 🏗️ Arquitetura

### Stack Tecnológico

**Backend (Python):**
- **Framework:** FastAPI 0.104+
- **ML/Estatística:** statsmodels, scikit-learn, numpy, pandas
- **Async:** asyncio, aiohttp
- **Database:** PostgreSQL + TimescaleDB, Redis
- **Testing:** pytest, pytest-asyncio

**Frontend (Next.js 15):**
- **Framework:** Next.js 15 (App Router)
- **UI Library:** shadcn/ui + Tailwind CSS
- **Charts:** Recharts + D3.js
- **State Management:** Zustand

### Estrutura do Projeto

```
app/
├── core/                    # Configurações centralizadas
│   └── config.py           # Configurações conforme DRS
├── api/v1/endpoints/       # Endpoints da API
│   ├── global_regimes.py   # RF001-RF020: Regimes globais
│   ├── brazil_spillovers.py # RF021-RF040: Spillovers Brasil
│   └── brazil_indicators.py # RF041-RF050: Indicadores Brasil
├── services/               # Lógica de negócio
│   ├── global_regime_analysis/  # Análise de regimes globais
│   ├── brazil_spillovers/       # Análise de spillovers
│   ├── brazil_forecasting/      # Previsões Brasil
│   ├── data_sources/            # Coleta de dados
│   └── regime_analysis/         # Análise científica de regimes
├── types/                  # Tipos TypeScript/Python
│   ├── global_regime.py    # Tipos para regimes globais
│   ├── brazil_spillovers.py # Tipos para spillovers
│   └── brazil_indicators.py # Tipos para indicadores
└── models/                 # Modelos de dados
    └── time_series.py      # Modelos de séries temporais
```

## 🔬 Módulos Científicos

### 1. Análise de Regimes Globais (RF001-RF020)
- **RS-GVAR:** Modelo Regime-Switching Global VAR
- **Identificação:** Seleção endógena do número de regimes (2-6)
- **Validação:** Testes estatísticos robustos
- **Previsão:** Horizonte de 1-12 meses

### 2. Spillovers Brasil (RF021-RF040)
- **Canal Comercial:** Trade Brasil-Mundo
- **Canal Commodities:** 8+ commodities críticas
- **Canal Financeiro:** Spreads soberanos e fluxos de capital
- **Canal Cadeias Globais:** Participação em GVCs

### 3. Previsões Brasil (RF041-RF050)
- **Indicadores:** PIB, inflação, desemprego, câmbio
- **Regime-Condicionais:** Baseadas em regimes globais
- **Alertas:** Sistema de alertas automáticos

## 📊 API Endpoints

### Regimes Globais
- `GET /global-regimes/current` - Regime atual
- `GET /global-regimes/forecast` - Previsões de regimes
- `GET /global-regimes/validation` - Validação do modelo

### Spillovers Brasil
- `GET /brazil-spillovers/current` - Spillovers atuais
- `GET /brazil-spillovers/forecast` - Previsões de spillovers
- `GET /brazil-spillovers/channels/{channel}` - Análise por canal

### Indicadores Brasil
- `GET /brazil-indicators/forecast` - Previsões de indicadores
- `GET /brazil-indicators/gdp` - Previsão do PIB
- `GET /brazil-indicators/inflation` - Previsão da inflação

## 🚀 Instalação

### Backend
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Executar migrações
alembic upgrade head

# Executar aplicação
uvicorn app.main:app --reload
```

### Frontend
```bash
cd dashboard
npm install
npm run dev
```

## 🔧 Configuração

### Variáveis de Ambiente
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/global_regime_analysis
REDIS_URL=redis://localhost:6379/0

# APIs Externas
FRED_API_KEY=your_fred_key
OECD_API_KEY=your_oecd_key
WORLD_BANK_API_KEY=your_worldbank_key

# Configurações
DEBUG=False
LOG_LEVEL=INFO
```

## 📈 Validação Científica

### Critérios de Aceitação
- ✅ Modelos passam em todos os testes de validação estatística
- ✅ Acurácia fora da amostra > 75% para identificação de regimes
- ✅ Intervalos de confiança calibrados corretamente
- ✅ Backtesting histórico com performance satisfatória

### Testes
```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=app --cov-report=html

# Executar testes específicos
pytest tests/test_global_regimes.py
```

## 📚 Documentação

- **DRS:** Documento de Requisitos do Sistema (fonte da verdade)
- **API:** Documentação automática em `/docs`
- **Tipos:** Definições em `app/types/`

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para suporte, abra uma issue no GitHub ou entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ pela equipe Quantum-X**
