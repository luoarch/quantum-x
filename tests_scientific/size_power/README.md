# tests_scientific/size_power

Validação científica de propriedades de size (erro tipo I) e power (potência) para testes de raiz unitária com amostras pequenas e moderadas, usando implementações validadas (arch.unitroot/statsmodels) e metodologia baseada no framework de Monte Carlo consolidado no projeto.

## Objetivos

- Estimar taxa de rejeição sob H0 (size) para ADF, DF-GLS e KPSS em diferentes T.  
- Estimar potência contra alternativas AR(1) estacionárias para ADF e DF-GLS em diferentes T e φ.  
- Exportar resultados em JSON/CSV e imprimir sumário legível, respeitando a sinalização correta das hipóteses de cada teste.

## Metodologia

- **Size**:
  - ADF/DF-GLS: H0 = raiz unitária; gerar random walk e medir rejeição a 5%.  
  - KPSS: H0 = estacionária; gerar AR(1) com |φ|<1 e medir rejeição a 5%.
- **Power**:
  - Gerar AR(1) com φ ∈ {0.95, 0.90, 0.85, 0.80, 0.70, 0.50} (H1 verdadeira) e medir rejeição de ADF e DF-GLS a 5%.

## Saídas

- **console**: sumário por T e por φ.  
- **artifacts**:
  - `size_results.json` / `.csv`  
  - `power_results.json` / `.csv`  
  - `run_metadata.json` (seed, T, n_sims, data/hora)

## Requisitos

- Python 3.10+; arch, statsmodels, numpy, pandas instalados

## Uso

```bash
# Size em T=100 com 1000 simulações
python -m tests_scientific.size_power.test_size_power --mode size --n-sims 1000 --T 100

# Power em T=100 com 1000 simulações
python -m tests_scientific.size_power.test_size_power --mode power --n-sims 1000 --T 100

# Rodar ambos e exportar CSV/JSON
python -m tests_scientific.size_power.test_size_power --mode both --n-sims 1000 --T 100 --out-dir reports/size_power
```

## Integração com CI

```bash
# Executar via CLI principal
python cli/validate_science.py size --model-version v1.0.0

# Executar via CLI principal com gate de promoção
python cli/validate_science.py size --model-version v1.0.0 --check-gate
```

## Critérios de Validação

- **Size**: Taxa de rejeição deve estar próxima de 5% (tolerância ±2%)
- **Power**: DF-GLS deve ser superior ao ADF (conforme literatura Elliott et al. 1996)
- **Robustez**: Testes devem funcionar com T ≥ 25 (amostras pequenas)

## Referências

- Elliott, G., Rothenberg, T. J., & Stock, J. H. (1996). Efficient tests for an autoregressive unit root. Econometrica, 64(4), 813-836.
- Ng, S., & Perron, P. (2001). Lag length selection and the construction of unit root tests with good size and power. Econometrica, 69(6), 1519-1554.
- Kwiatkowski, D., Phillips, P. C., Schmidt, P., & Shin, Y. (1992). Testing the null hypothesis of stationarity against the alternative of a unit root. Journal of Econometrics, 54(1-3), 159-178.
