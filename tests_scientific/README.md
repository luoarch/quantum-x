# Sistema de Validação Científica - Quantum-X

Sistema completo de validação científica para modelos econométricos de séries temporais, com foco em testes de raiz unitária e seleção de lags.

## 📚 Visão Geral

Este sistema implementa **6 pacotes de validação científica** que cobrem os principais aspectos metodológicos necessários para garantir a robustez e confiabilidade dos modelos:

### 1️⃣ Size & Power (`size_power/`)
- **Objetivo**: Validar propriedades fundamentais dos testes de raiz unitária
- **Testes**: ADF, DF-GLS, KPSS
- **Métricas**: Taxa de rejeição (size), Potência contra alternativas
- **Referências**: Dickey & Fuller (1979), Elliott et al. (1996)

### 2️⃣ Small Samples (`small_samples/`)
- **Objetivo**: Quantificar distorções em amostras pequenas (T < 100)
- **Cenários**: T ∈ {25, 50, 75, 100}
- **Métricas**: Size por tamanho de amostra, Power em T pequenos
- **Referências**: Schwert (1989), Ng & Perron (2001)

### 3️⃣ Heteroskedasticity (`heteroskedasticity/`)
- **Objetivo**: Avaliar robustez sob variância não constante
- **Padrões**: increasing, decreasing, breaks, ARCH(1), GARCH(1,1)
- **Métricas**: Distorção de size por padrão de heterocedasticidade
- **Referências**: Cavaliere & Taylor (2007)

### 4️⃣ Structural Breaks (`structural_breaks/`)
- **Objetivo**: Detectar quebras estruturais em séries
- **Método**: Zivot–Andrews (quebra única)
- **Casos**: single_level, trend_break, double_level, mixed_breaks
- **Métricas**: Taxa de detecção, Erro de localização
- **Referências**: Zivot & Andrews (1992), Perron (1989)

### 5️⃣ Lag Selection (`lag_selection/`)
- **Objetivo**: Validar critérios de seleção de lags
- **Critérios**: AIC, BIC, t-stat backwards, Schwert rule
- **Cenários**: AR(p) com p ∈ {1,2,3,4}, T ∈ {50, 100, 200}
- **Métricas**: Acerto exato, Acerto ±1 lag
- **Referências**: Schwert (1989), Ng & Perron (2001)

### 6️⃣ Benchmarks NP (`benchmarks_np/`)
- **Objetivo**: Smoke tests em séries tipo macro
- **Séries**: GDP-like, Price-level-like, Unemployment-like, Interest-rate-like
- **Métricas**: Taxa de concordância com propriedades esperadas
- **Referências**: Nelson & Plosser (1982)

## 🚀 Uso Rápido

### Executar Todas as Validações

```bash
# Validação completa (1000 simulações por teste)
make -f Makefile.validation all

# Validação rápida (100 simulações - para desenvolvimento)
make -f Makefile.validation validate-quick

# Validação para CI (sem cores)
make -f Makefile.validation validate-ci
```

### Executar Validações Individuais

```bash
# Size & Power
make -f Makefile.validation size-power

# Small Samples
make -f Makefile.validation small-samples

# Heteroskedasticity
make -f Makefile.validation heteroskedasticity

# Structural Breaks
make -f Makefile.validation structural-breaks

# Lag Selection
make -f Makefile.validation lag-selection

# Benchmarks NP
make -f Makefile.validation benchmarks-np
```

### Customizar Parâmetros

```bash
# Aumentar número de simulações
make -f Makefile.validation all N_SIMS=5000

# Mudar seed de reprodutibilidade
make -f Makefile.validation all SEED=12345

# Mudar nível de significância
make -f Makefile.validation all ALPHA=0.01
```

## 📊 Estrutura de Relatórios

Todos os relatórios são salvos em `reports/validation/YYYY-MM-DD_HH-MM-SS/`:

```
reports/validation/2025-09-30_10-00-00/
├── size_power/
│   ├── size_results.json
│   ├── size_results.csv
│   ├── power_results.json
│   └── power_results.csv
├── small_samples/
│   ├── small_size_results.json
│   ├── small_size_results.csv
│   ├── small_power_results.json
│   └── small_power_results.csv
├── heteroskedasticity/
│   ├── hetero_size_results.json
│   └── hetero_size_results.csv
├── structural_breaks/
│   ├── breaks_results.json
│   └── breaks_results.csv
├── lag_selection/
│   ├── lag_selection_results.json
│   ├── lag_selection_results.csv
│   └── lag_distributions.json
└── benchmarks_np/
    ├── benchmarks_results.json
    └── benchmarks_results.csv
```

## 🔍 Interpretando Resultados

### Size & Power
- **Size ideal**: ~5% (α = 0.05)
- **Size aceitável**: 3-7%
- **Power desejável**: > 80% para φ = 0.95

### Small Samples
- **T=25**: Size distorcido esperado
- **T=50**: Size moderado
- **T≥100**: Size próximo do nominal

### Heteroskedasticity
- **ARCH/GARCH**: Size moderadamente inflado esperado
- **Breaks**: Size pode estar inflado
- **Increasing/Decreasing**: Monitorar distorções

### Structural Breaks
- **Single breaks**: Taxa de detecção > 80%
- **Multiple breaks**: Taxa baixa esperada (limitação do ZA)
- **Erro de localização**: < 10 períodos para quebras únicas

### Lag Selection
- **BIC**: Mais parcimonioso que AIC
- **AIC**: Pode sobre-selecionar lags
- **t-stat**: Performance dependente de τ
- **Acerto ±1**: > 80% desejável

### Benchmarks NP
- **Unit root series**: Concordância > 70%
- **Stationary series**: Concordância > 60%
- **Overall**: Média > 65%

## 🎯 Critérios de Aceitação

Para **aprovar** um modelo para produção, os seguintes critérios devem ser atendidos:

1. **Size & Power**: Size entre 3-7%, Power > 70% para φ=0.95
2. **Small Samples**: Size < 10% para T≥50
3. **Heteroskedasticity**: Size < 15% para todos os padrões
4. **Structural Breaks**: Detecção > 80% para quebras únicas
5. **Lag Selection**: Acerto ±1 lag > 70% para BIC
6. **Benchmarks NP**: Concordância média > 65%

## 📦 Instalação de Dependências

```bash
pip install -r requirements.txt
```

Dependências principais:
- `numpy` - Operações numéricas
- `pandas` - Manipulação de dados
- `statsmodels` - Testes econométricos
- `arch` - DF-GLS e testes de raiz unitária

## 🔄 Integração com CI/CD

Adicionar ao `.github/workflows/validation.yml`:

```yaml
name: Scientific Validation

on:
  schedule:
    - cron: '0 0 * * *'  # Rodar diariamente
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run validation
        run: make -f Makefile.validation validate-ci
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: validation-reports
          path: reports/validation/
```

## 📖 Documentação Adicional

- **Size & Power**: `tests_scientific/size_power/README.md`
- **Small Samples**: `tests_scientific/small_samples/README.md`
- **Heteroskedasticity**: `tests_scientific/heteroskedasticity/README.md`
- **Structural Breaks**: `tests_scientific/structural_breaks/README.md`
- **Lag Selection**: `tests_scientific/lag_selection/README.md`
- **Benchmarks NP**: `tests_scientific/benchmarks_np/README.md`

## 🤝 Contribuindo

Para adicionar novos testes de validação:

1. Criar novo subpacote em `tests_scientific/novo_teste/`
2. Implementar `test_novo_teste.py` com CLI consistente
3. Adicionar `README.md` documentando objetivos e uso
4. Atualizar `Makefile.validation` com novo target
5. Adicionar critérios de aceitação a este README

## 📚 Referências Científicas

- Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for autoregressive time series with a unit root. *JASA*, 74(366a), 427-431.
- Elliott, G., Rothenberg, T. J., & Stock, J. H. (1996). Efficient tests for an autoregressive unit root. *Econometrica*, 64(4), 813-836.
- Kwiatkowski, D., Phillips, P. C., Schmidt, P., & Shin, Y. (1992). Testing the null hypothesis of stationarity against the alternative of a unit root. *Journal of Econometrics*, 54(1-3), 159-178.
- Schwert, G. W. (1989). Tests for unit roots: A Monte Carlo investigation. *JBES*, 7(2), 147-159.
- Ng, S., & Perron, P. (2001). Lag length selection and the construction of unit root tests with good size and power. *Econometrica*, 69(6), 1519-1554.
- Cavaliere, G., & Taylor, A. M. R. (2007). Testing for unit roots in time series models with non-stationary volatility. *Journal of Econometrics*, 140(2), 919-947.
- Zivot, E., & Andrews, D. W. K. (1992). Further evidence on the great crash, the oil-price shock, and the unit-root hypothesis. *JBES*, 10(3), 251-270.
- Nelson, C. R., & Plosser, C. R. (1982). Trends and random walks in macroeconomic time series. *Journal of Monetary Economics*, 10(2), 139-162.

## 📄 Licença

Este sistema de validação científica é parte do projeto Quantum-X e segue a mesma licença do projeto principal.
