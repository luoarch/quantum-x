API de previsão da Selic condicionada a movimentos do Fed.

# Spec: API de Previsão Selic Condicionada ao Fed

## Visão geral

Este documento especifica requisitos funcionais, não funcionais, dados, modelagem, API, MLOps, segurança e governança para um serviço de previsão probabilística do “quando” (horizonte) e “quanto” (em pontos-base) a Selic tende a se mover, condicionado a um movimento informado do Fed.

### Objetivo

Entregar uma API que, dado um evento do Fed (data e magnitude/direção em bps), retorne previsão probabilística de ajuste da Selic por janela do Copom, magnitude em bps e bandas de confiança, com rastreabilidade e versionamento.

### Escopo

- Estimação offline e inferência online de respostas da Selic a choques do Fed.
- Suporte a inputs em incrementos de 25 bps, com possibilidade de múltiplos cenários condicionais.
- Retorno probabilístico por janela do Copom, com discretização em 25 bps.

### Fora de escopo

- Previsões determinísticas sem incerteza.
- Cobertura de variáveis macro adicionais além das listadas em “Dados e features” (fase 1).
- Interface web; somente API.

## Hipóteses e premissas

- Relação dinâmica Fed→Selic existe, com defasagens típicas entre 1 e 24 meses, variando por regime.
- Dados disponíveis: últimos ~20 eventos pareados (Fed x Copom), suficientes para um modelo parcimonioso com regularização/priors; bandas serão largas.
- Movimentos de política são discretos em 25 bps; o serviço deve respeitar essa granularidade.
- Regimes e quebras estruturais existem; o pipeline precisa detectá-los e mitigar instabilidades.

## Definições

- Movimento do Fed: alteração na meta dos Fed Funds (bps) informada na data da reunião.
- Horizonte: janelas mensais e janelas de reunião do Copom subsequentes ao evento do Fed.
- Probabilidade por janela: massa de probabilidade do primeiro ajuste da Selic ocorrer em cada janela do Copom.

## Stakeholders e personas

- Economistas e estrategistas: exploração de cenários e avaliação de risco por janela.
- Times de produto/engenharia: integração em fluxos de decisão.
- Auditoria/model risk: rastreabilidade de versões, dados e decisões.

## Histórias de usuário (exemplos)

- Como analista, ao informar “Fed +25 bps em 2025-10-29”, deseja-se saber a probabilidade de o Copom ajustar a Selic em +25 bps na próxima reunião e o horizonte mais provável do primeiro ajuste.
- Como product owner, deseja-se obter previsões para um conjunto de cenários (0, +25, +50) para as próximas três reuniões do Fed.
- Como auditor, deseja-se recuperar o objeto do modelo, dataset hash e métricas de backtest usados numa previsão passada.

## Dados e features

### Fontes e granularidade

- Série Selic e calendário de reuniões do Copom (nível e variação em bps por reunião e por mês).
- Série Fed Funds (nível e variação em bps por reunião; derivar componente “movimento” e opcionalmente “surpresa”).
- Alinhamento temporal: chavear por data de reunião; criar vistas mensal e por-evento.

### Engenharia de variáveis (fase 1)

- Diferenças em bps: $$\Delta \text{Fed}_t$$, $$\Delta \text{Selic}_t$$.
- Defasagens: $$\Delta \text{Fed}_{t-i}$$, $$\Delta \text{Selic}_{t-j}$$ para $$i,j$$ em janelas curtas.
- Dummies de regime/quebras quando detectadas.
- Calendário do Copom: mapeamento mês→próxima reunião.

### Qualidade de dados

- Remoção de ausências, reconciliação de áreas de corte (mid-month vs. end-month).
- Checagem de estacionariedade e heterocedasticidade; decidir diferenciação e robustez a variância.

## Modelagem

### Abordagem

- Núcleo 1: Local Projections (LP) penalizadas/Bayes para estimar respostas impulso por horizonte $$h$$, com equações do tipo:
  $$
  \Delta \text{Selic}_{t+h} = \alpha_h + \beta_h \cdot \Delta \text{Fed}_t + \sum_{i=1}^{p} \phi_{h,i} \Delta \text{Selic}_{t-i} + \sum_{k=1}^{q} \gamma_{h,k} \Delta \text{Fed}_{t-k} + \varepsilon_{t+h}
  $$
  com shrinkage e bandas via bootstrap/bayes.
- Núcleo 2: BVAR pequeno (Selic, Fed) com prior Minnesota e previsão condicional impondo o caminho do Fed; gerar distribuições preditivas por horizonte.

### Quebras e regimes

- Detecção: testes de quebra única e múltiplas (fase 2) para indicar dummies/estabilidade.
- Estratégias: janelas móveis, dummies de regime, ou reponderação por período.

### Heteroscedasticidade

- Erros-robustos em LP; em BVAR, choques com variância hetero-consistente e bandas por simulação.

### Saídas probabilísticas

- Converter IRFs em distribuições de $$\Delta \text{Selic}$$ por horizonte; discretizar em múltiplos de 25 bps e mapear a janelas do Copom para cálculo de probabilidade do primeiro ajuste.

### Seleção de lags e horizontes

- Critérios AIC/BIC/t, regra de Schwert e heurística conservadora para N pequeno.
- Horizontes: $$h=1,\dots,12$$ meses (fase 1); expandir conforme dados.

### Avaliação offline

- Backtests por evento (Fed move): calibração (PIT), cobertura dos intervalos, Brier/log score, CRPS por horizonte.

## API

### Princípios

- Stateless, versionada, determinista por versão de modelo.
- Probabilística por padrão; sempre retorna bandas e metadados de versão.

### Endpoints

- POST /predict/selic-from-fed
  - Request
    - fed_decision_date: string (ISO-8601)
    - fed_move_bps: integer (…,-50,-25,0,25,50,…)
    - fed_move_dir: integer (-1,0,1) [opcional se fed_move_bps presente]
    - fed_surprise_bps: integer [opcional]
    - horizons_months: array[int] [opcional; default 1..12]
    - model_version: string [opcional; default corrente]
    - regime_hint: string [opcional; ex.: “stress”, “normal”]
  - Response
    - expected_move_bps: integer
    - horizon_months: integer | range (ex.: 1–3)
    - prob_move_within_next_copom: number[1]
    - ci80_bps: [low:int, high:int]
    - ci95_bps: [low:int, high:int]
    - per_meeting: array[{copom_date, delta_bps:int, probability:number}]
    - distribution: array[{delta_bps:int, probability:number}]
    - model_metadata: {version, trained_at, data_hash, methodology}
    - rationale: string

- POST /predict/selic-from-fed/batch
  - Request: array de cenários no mesmo formato.
  - Response: array de previsões com mesmo schema.

- GET /models/versions
  - Lista versões, datas de treino, hashes e métricas de backtest.

- GET /health
  - Status, latências, versão ativa.

### Regras de validação

- fed_decision_date não pode ser futuro além de um limite (se cenário futuro, marcar como scenario: true).
- fed_move_bps deve ser múltiplo de 25; caso contrário, rejeitar ou arredondar com aviso.
- horizons_months no intervalo  (configurável).[1]

### Erros (padrão)

- 400 invalid_request: campos ausentes/invalidos.
- 422 unsupported_value: bps fora do conjunto permitido.
- 429 rate_limited: excedeu limites.
- 500 internal_error: erro inesperado.
- 503 model_unavailable: versão do modelo indisponível.

### Autenticação e limites

- Chave de API no header; limites por minuto e por dia configuráveis.
- Escopo de chave por ambiente (dev/staging/prod).

### Versionamento

- Versão da API via header X-API-Version e path opcional (/v1/…).
- Versão de modelo declarada no payload de saída; previsões reprodutíveis por versão.

## MLOps e operação

### Pipeline offline (treinador)

- Ingestão e validação de dados, engenharia de features, seleção de lags, detecção de quebras, estimação LP e BVAR, avaliação, materialização de artefatos (objetos de modelo, IRFs, metadados).

### Gate de promoção

- Critérios mínimos de cobertura (ex.: 95% CI cobrindo ≥ 90% nos backtests), calibração (PIT), e estabilidade de coeficientes; promotion only se atender thresholds.

### Observabilidade online

- Métricas: latência p50/p95, taxa de erro, % requests por cenário, drift simples (input).
- Logs: request_id, dataset_hash, model_version, seed, tempo de inferência, resumo de saída.
- Traços: span por request com checkpoints (validação, inferência, pós-processamento).

### Re-treino

- Gatilhos mensais/pós-reunião; reprocessar com dados novos; manter N versões ativas para restauração.

### Rollback

- Toggle imediato da versão anterior; health-check e canary para novos releases.

## Segurança, privacidade e compliance

- Sem PII; armazenar apenas metadados técnicos e inputs do usuário para auditoria (configurável).
- Chaves rotacionadas; TLS obrigatório; least privilege.
- Limpeza e retenção de logs (ex.: 90 dias).

## Performance e SLOs

- P95 latência < 250 ms (payloads normais); p99 < 500 ms.
- Disponibilidade mensal ≥ 99.9%.
- Throughput alvo inicial: 50 RPS sustentados (escalável horizontalmente).

## Riscos e mitigação

- N pequeno: usar priors/shrinkage, bandas largas e comunicação probabilística; validar continuamente.
- Regime shift: dummies e alarmes de recalibração; versões por regime em roadmap.
- Dependência de calendário: manter tabela de Copom atualizada; fallback para janelas mensais se indisponível.

## Testes

- Unidade: validação de schemas, transformações, discretização.
- Integração: percurso completo do request à resposta, idempotência por versão.
- Regressão: snapshot por versão de modelo.
- Backtests: event-based, calibrations, cobertura, pontuações probabilísticas.
- Chaos/latência: injetar falhas e medir resiliência.

## Deploy e arquitetura

- Runtime: serviço stateless (ex.: FastAPI), containerizado, cache leve por versão.
- Infra: autoscaling, circuito de proteção, readiness/liveness probes.
- Armazenamento: artefatos de modelo (read-only), feature store simples (opcional), logs/metrics centralizados.

## Configuração e feature flags

- Flags para: troca de núcleo (LP/BVAR), usar dummies de regime, arredondamento de bps, nível de logs.
- Config por ambiente; imutabilidade por tag de release.

## Interpretabilidade e comunicação

- Retornar “rationale” com sumário: método, horizonte mais responsivo, sinal estimado, limitações do N e regime.
- Expor metadados mínimos para auditoria (data_hash, version, metrics).

## Critérios de aceitação (MVP)

- Endpoint /predict funcional, validando inputs e retornando distribuição discretizada em 25 bps com prob_move_within_next_copom, ci80/ci95 e per_meeting.
- Versionamento de modelo e reprodução de previsões.
- Backtests mínimos com relatório exportável e gate de promoção aplicado.
- Observabilidade básica (métricas, logs, health).

## Roadmap (alto nível)

- Semana 1–2: pipeline de dados e treinador LP, API esqueleto, schemas, testes unidade.
- Semana 3–4: BVAR condicional, backtests, gates, observabilidade, canary.
- Semana 5: hardening (rate limit, auth, rollback), documentação e promoção a prod.

## Perguntas em aberto

- Incluir controles adicionais (ex.: câmbio, EMBI, expectativas) na fase 1 ou 2?
- Política de arredondamento de bps fora de múltiplos de 25: rejeitar ou ajustar?
- Qual threshold mínimo de probabilidade para afirmar “quando” no resumo?

***

## Anexos

### Schema: POST /predict/selic-from-fed (request)

```json
{
  "fed_decision_date": "2025-10-29",
  "fed_move_bps": 25,
  "fed_move_dir": 1,
  "fed_surprise_bps": 10,
  "horizons_months": [1, 3, 6, 12],
  "model_version": "v1.2.0",
  "regime_hint": "normal"
}
```

### Schema: POST /predict/selic-from-fed (response)

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
    { "delta_bps": 50, "probability": 0.20 },
    { "delta_bps": 75, "probability": 0.03 }
  ],
  "model_metadata": {
    "version": "v1.2.0",
    "trained_at": "2025-09-25T12:00:00Z",
    "data_hash": "sha256:...abcd",
    "methodology": "LP primary, BVAR fallback"
  },
  "rationale": "Resposta estimada positiva ao choque de +25 bps do Fed; maior massa de probabilidade no próximo Copom, alta incerteza devido à amostra curta."
}
```

### Fórmulas de referência

- LP por horizonte:
  $$
  \Delta \text{Selic}_{t+h} = \alpha_h + \beta_h \cdot \Delta \text{Fed}_t + \sum_{i=1}^{p} \phi_{h,i} \Delta \text{Selic}_{t-i} + \sum_{k=1}^{q} \gamma_{h,k} \Delta \text{Fed}_{t-k} + \varepsilon_{t+h}
  $$

- BVAR condicional (esboço):
  $$
  Y_t = c + A_1 Y_{t-1} + \dots + A_p Y_{t-p} + u_t,\quad u_t \sim \mathcal{N}(0,\Sigma),\ \text{com prior Minnesota e caminho de } \text{Fed}_t \text{ imposto}
  $$

***

Observação: este documento presume bandas de incerteza explícitas e comunicação probabilística por janela; com ~20 eventos históricos, o sistema prioriza parcimônia, priors fortes e validação contínua.