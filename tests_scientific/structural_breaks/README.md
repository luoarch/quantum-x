# tests_scientific/structural_breaks

Validação da detecção de quebras estruturais em séries, com ênfase em limitações conhecidas do teste de Zivot–Andrews (ZA) para múltiplas quebras. Mede taxa de detecção e erro de localização com tolerância.

## Objetivos
- Quantificar taxa de detecção de uma quebra única em nível/tendência com ZA.
- Demonstrar limitação do ZA para múltiplas quebras (esperar baixa/zero detecção).
- Medir erro absoluto médio da posição da quebra e taxa dentro de tolerâncias (±k períodos).

## Casos gerados
- **single_level**: uma quebra no nível em t = T/2.
- **trend_break**: mudança de inclinação (tendência) em t = T/2.
- **double_level**: duas quebras no nível (aprox. T/3 e 2T/3).
- **mixed_breaks**: combinação (nível + tendência).

## Parâmetros principais
- Tamanho da amostra T (default 100)
- Magnitude(s) da(s) quebra(s)
- Tolerância de acerto em períodos (default ±10)
- N de simulações (default 500)

## Uso

```bash
# Todos os casos com 500 simulações
python -m tests_scientific.structural_breaks.test_structural_breaks \
  --cases single_level,trend_break,double_level,mixed_breaks \
  --T 100 --mag 2.0 --n-sims 500 --tol 10 --out-dir reports/structural_breaks

# Apenas quebra única com tolerância menor
python -m tests_scientific.structural_breaks.test_structural_breaks \
  --cases single_level,trend_break --T 100 --mag 2.0 --n-sims 500 --tol 5

# Múltiplas quebras com tolerância maior
python -m tests_scientific.structural_breaks.test_structural_breaks \
  --cases double_level,mixed_breaks --T 200 --mag 2.0 --n-sims 500 --tol 15
```

## Integração com CI

```bash
# Executar via CLI principal
python cli/validate_science.py breaks --model-version v1.0.0

# Executar via CLI principal com gate de promoção
python cli/validate_science.py breaks --model-version v1.0.0 --check-gate
```

## Saídas
- `breaks_results.json/.csv` com taxa de detecção por caso e erro médio de localização.
- `run_metadata.json` com seed, parâmetros e data/hora.

## Critérios de Validação

- **Single Break Detection**: ZA deve detectar bem quebras únicas (taxa > 80%)
- **Multiple Breaks Limitation**: ZA deve falhar em múltiplas quebras (taxa < 30%)
- **Location Accuracy**: Erro médio de localização deve ser baixo para quebras únicas
- **Tolerance Sensitivity**: Taxa de detecção deve aumentar com tolerância maior

> **Observação**: Zivot–Andrews foi projetado para uma quebra única. Em cenários com múltiplas quebras, esperamos baixas taxas de detecção adequada.

## Referências

- Zivot, E., & Andrews, D. W. K. (1992). Further evidence on the great crash, the oil-price shock, and the unit-root hypothesis. Journal of Business & Economic Statistics, 10(3), 251-270.
- Perron, P. (1989). The great crash, the oil price shock, and the unit root hypothesis. Econometrica, 57(6), 1361-1401.
- Bai, J., & Perron, P. (1998). Estimating and testing linear models with multiple structural changes. Econometrica, 66(1), 47-78.
