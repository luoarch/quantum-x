# tests_scientific/small_samples

Validação científica das propriedades de testes de raiz unitária em amostras pequenas (T < 100), conforme Schwert (1989) e Ng & Perron (2001). Mede distorções de size (erro tipo I) e potência para T ∈ {25, 50, 75, 100}.

## Objetivos
- Quantificar distorções de size para ADF, DF-GLS e KPSS em T pequenos.
- Quantificar potência para ADF e DF-GLS contra alternativas AR(1) estacionárias em T pequenos.
- Exportar resultados por tamanho de amostra para gates de promoção.

## Metodologia
- **Size**:
  - ADF/DF-GLS: H0 = raiz unitária → gerar random walk.
  - KPSS: H0 = estacionária → gerar AR(1) com |φ|<1 (φ=0.7).
- **Power**:
  - AR(1) com φ ∈ {0.95, 0.90, 0.85, 0.80} (mais focado em T pequenos).
- α = 5%, n_sims configurável (default 1000).

## Uso

```bash
# Size em múltiplos T com 1000 simulações
python -m tests_scientific.small_samples.test_small_samples --mode size --n-sims 1000 --Ts 25,50,75,100

# Power em múltiplos T com 1000 simulações
python -m tests_scientific.small_samples.test_small_samples --mode power --n-sims 1000 --Ts 25,50,75,100

# Rodar ambos e exportar CSV/JSON
python -m tests_scientific.small_samples.test_small_samples --mode both --n-sims 1000 --Ts 25,50,75,100 --out-dir reports/small_samples
```

## Integração com CI

```bash
# Executar via CLI principal
python cli/validate_science.py small --model-version v1.0.0

# Executar via CLI principal com gate de promoção
python cli/validate_science.py small --model-version v1.0.0 --check-gate
```

## Saídas
- `small_size_results.json/.csv` com taxa de rejeição por teste e T.
- `small_power_results.json/.csv` com potência por φ e T.
- `run_metadata.json` com seed, datas e parâmetros.

## Critérios de Validação

- **Size Distortion**: Taxa de rejeição deve divergir de 5% em T pequenos
- **Power Loss**: Potência deve diminuir com T menor
- **DF-GLS Superiority**: DF-GLS deve manter vantagem sobre ADF mesmo em T pequenos
- **T < 50 Problem**: Confirmação de que T < 50 é inadequado para testes tradicionais

## Referências

- Schwert, G. W. (1989). Tests for unit roots: A Monte Carlo investigation. Journal of Business & Economic Statistics, 7(2), 147-159.
- Ng, S., & Perron, P. (2001). Lag length selection and the construction of unit root tests with good size and power. Econometrica, 69(6), 1519-1554.
- Elliott, G., Rothenberg, T. J., & Stock, J. H. (1996). Efficient tests for an autoregressive unit root. Econometrica, 64(4), 813-836.
