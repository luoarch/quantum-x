# tests_scientific/benchmarks_np

Smoke tests de referência inspirados em Nelson–Plosser para verificar se os testes (ADF, DF-GLS, KPSS) se comportam como esperado em séries "tipo macro" simuladas com propriedades-alvo (unit root vs. estacionárias de alta persistência).

## Objetivos
- Checar coerência dos testes em séries com:
  - random walk com tendência (tipo GDP/preços)
  - AR(1) altamente persistente (tipo taxa de desemprego/juros)
  - RW puro (nível de preços)
- Reportar taxa de concordância com rótulos esperados (unit_root = True/False).

## Séries simuladas (exemplos)
- **real_gdp_like**: RW com drift pequeno (esperado: unit root)
- **price_level_like**: RW puro (esperado: unit root)
- **unemployment_like**: AR(1), φ=0.85 (esperado: estacionária)
- **interest_rate_like**: AR(1), φ=0.90 (esperado: estacionária)

> **Observação**: trata-se de um smoke test reprodutível — não são dados reais Nelson–Plosser, mas proxies simulados.

## Uso

```bash
# Teste padrão com 100 simulações
python -m tests_scientific.benchmarks_np.test_benchmarks_np \
  --T 100 --n-sims 100 --out-dir reports/benchmarks_np

# Teste rápido
python -m tests_scientific.benchmarks_np.test_benchmarks_np \
  --T 100 --n-sims 50 --alpha 0.05 --seed 42

# Teste com amostra maior
python -m tests_scientific.benchmarks_np.test_benchmarks_np \
  --T 200 --n-sims 200 --out-dir reports/benchmarks_np_large
```

## Integração com CI

```bash
# Executar via CLI principal
python cli/validate_science.py benchmarks --model-version v1.0.0

# Executar via CLI principal com gate de promoção
python cli/validate_science.py benchmarks --model-version v1.0.0 --check-gate
```

## Saídas
- `benchmarks_results.json/.csv` com concordância por série.
- `run_metadata.json` com seed e parâmetros.

## Critérios de Validação

- **Unit Root Series**: Taxa de concordância > 70% para séries RW
- **Stationary Series**: Taxa de concordância > 60% para séries AR(1) persistentes
- **Overall Coherence**: Média de concordância > 65% em todas as séries
- **Consensus Logic**: Combinar ADF, DF-GLS e KPSS para decisão robusta

## Interpretação dos Resultados

### Concordância Alta (>80%)
- Testes estão coerentes com propriedades teóricas
- Boa calibração de α e poder dos testes

### Concordância Média (60-80%)
- Esperado para séries ambíguas (AR persistente vs. unit root)
- Reflete trade-off entre size e power

### Concordância Baixa (<60%)
- Possível problema com implementação dos testes
- Necessário revisar parâmetros (lags, tendência, etc.)

## Referências

- Nelson, C. R., & Plosser, C. R. (1982). Trends and random walks in macroeconomic time series: Some evidence and implications. Journal of Monetary Economics, 10(2), 139-162.
- Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for autoregressive time series with a unit root. Journal of the American Statistical Association, 74(366a), 427-431.
- Kwiatkowski, D., Phillips, P. C., Schmidt, P., & Shin, Y. (1992). Testing the null hypothesis of stationarity against the alternative of a unit root. Journal of Econometrics, 54(1-3), 159-178.
