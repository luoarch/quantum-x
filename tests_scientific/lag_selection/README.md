# tests_scientific/lag_selection

Valida critérios de seleção de lags (AIC, BIC, t-stat, Schwert) em séries AR(p) sintéticas, com métricas de acerto e distribuição dos lags escolhidos.

## Objetivos
- Avaliar a capacidade dos critérios em recuperar p verdadeiro em AR(p).
- Reportar acerto exato e acerto tolerado (±1).
- Exportar distribuição dos lags selecionados por critério e cenário.

## Metodologia
- Gerar séries AR(p) com p ∈ {1,2,3,4}, T ∈ {50, 100, 200}.
- Coeficientes estáveis, ex.: AR(2): y_t = 0.7 y_{t-1} − 0.2 y_{t-2} + ε_t.
- Critérios:
  - **AIC/BIC** via ajuste AutoReg variando lags.
  - **t-stat backwards**: iniciar de L_max e reduzir enquanto |t_final| < τ (τ=1.6).
  - **Schwert rule** para L_max: L_max = ⌊12 (T/100)^{1/4}⌋.

## Uso

```bash
# Todos os cenários com 500 simulações
python -m tests_scientific.lag_selection.test_lag_selection \
  --Ts 50,100,200 --ps 1,2,3,4 --n-sims 500 --out-dir reports/lag_selection

# Apenas T=100 com diferentes p
python -m tests_scientific.lag_selection.test_lag_selection \
  --Ts 100 --ps 1,2,3,4 --n-sims 1000 --seed 42

# Teste rápido com poucas simulações
python -m tests_scientific.lag_selection.test_lag_selection \
  --Ts 50,100 --ps 1,2 --n-sims 100
```

## Integração com CI

```bash
# Executar via CLI principal
python cli/validate_science.py lags --model-version v1.0.0

# Executar via CLI principal com gate de promoção
python cli/validate_science.py lags --model-version v1.0.0 --check-gate
```

## Saídas
- `lag_selection_results.json/.csv` com acertos por critério, T e p.
- `lag_distributions.json` com histograma de lags selecionados.

## Critérios de Validação

- **AIC Performance**: Deve ter boa recuperação de p verdadeiro em amostras grandes
- **BIC Performance**: Deve ser mais parcimonioso que AIC, penalizando lags extras
- **t-stat Performance**: Deve ter boa detecção de significância estatística
- **Schwert Rule**: L_max deve ser apropriado para o tamanho da amostra
- **Tolerance**: Acerto ±1 lag deve ser > 80% para critérios adequados

## Coeficientes AR(p) Padrão

- **AR(1)**: φ₁ = 0.7
- **AR(2)**: φ₁ = 0.7, φ₂ = -0.2  
- **AR(3)**: φ₁ = 0.5, φ₂ = -0.2, φ₃ = 0.1
- **AR(4)**: φ₁ = 0.5, φ₂ = -0.2, φ₃ = 0.1, φ₄ = -0.05

## Referências

- Schwert, G. W. (1989). Tests for unit roots: A Monte Carlo investigation. Journal of Business & Economic Statistics, 7(2), 147-159.
- Ng, S., & Perron, P. (2001). Lag length selection and the construction of unit root tests with good size and power. Econometrica, 69(6), 1519-1554.
- Akaike, H. (1974). A new look at the statistical model identification. IEEE Transactions on Automatic Control, 19(6), 716-723.
- Schwarz, G. (1978). Estimating the dimension of a model. The Annals of Statistics, 6(2), 461-464.
