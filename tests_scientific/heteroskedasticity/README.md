# tests_scientific/heteroskedasticity

Validação da robustez dos testes de raiz unitária sob heterocedasticidade e variância não constante no tempo, conforme Cavaliere & Taylor (2007). Mede distorções de size para ADF, DF-GLS e KPSS sob diferentes padrões de σ_t.

## Padrões de heterocedasticidade
- **increasing**: σ_t crescente (0.5 + 0.01 t)
- **decreasing**: σ_t decrescente (2.0 − 0.015 t)
- **breaks**: salto de σ em t = T/2
- **arch**: ARCH(1) com ω, α > 0
- **garch**: GARCH(1,1) com ω, α, β > 0

## Metodologia
- **ADF/DF-GLS**: H0 = raiz unitária → random walk com choques ε_t ~ N(0, σ_t^2) segundo o padrão.
- **KPSS**: H0 = estacionária → AR(1) com |φ|<1, mas com σ_t^2 variando pelo padrão.
- α = 5%; T padrão = 100; n_sims padrão = 1000.

## Uso

```bash
# Todos os padrões com 1000 simulações
python -m tests_scientific.heteroskedasticity.test_heteroskedasticity \
  --patterns increasing,decreasing,breaks,arch,garch --n-sims 1000 --T 100 \
  --out-dir reports/heteroskedasticity

# Apenas padrões ARCH/GARCH
python -m tests_scientific.heteroskedasticity.test_heteroskedasticity \
  --patterns arch,garch --n-sims 1000 --T 100

# Padrões de quebra com T maior
python -m tests_scientific.heteroskedasticity.test_heteroskedasticity \
  --patterns breaks --n-sims 1000 --T 200
```

## Integração com CI

```bash
# Executar via CLI principal
python cli/validate_science.py hetero --model-version v1.0.0

# Executar via CLI principal com gate de promoção
python cli/validate_science.py hetero --model-version v1.0.0 --check-gate
```

## Saídas
- `hetero_size_results.json/.csv` com taxa de rejeição (size) por teste e padrão.
- `run_metadata.json` com seed, parâmetros e data/hora.

## Critérios de Validação

- **Size Distortion**: Medir distorções de size sob diferentes padrões de heterocedasticidade
- **Pattern Sensitivity**: Identificar quais padrões causam maiores distorções
- **Test Robustness**: Comparar robustez entre ADF, DF-GLS e KPSS
- **ARCH/GARCH Impact**: Quantificar impacto de processos ARCH/GARCH

> **Observação**: É esperado que ADF/DF-GLS/KPSS apresentem distorções de size sob alguns padrões. O objetivo é quantificar e rastrear essas distorções para fins de validação científica.

## Referências

- Cavaliere, G., & Taylor, A. M. (2007). Testing for unit roots in time series with non-stationary volatility. Journal of Econometrics, 140(2), 919-947.
- Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation. Econometrica, 50(4), 987-1007.
- Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. Journal of Econometrics, 31(3), 307-327.
