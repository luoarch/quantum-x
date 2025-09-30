# ✅ Checklist de Go-Live - API FED-Selic

**Versão da API:** 1.0.0  
**Versão do Modelo:** v1.0.2 (BVAR v2.1 FINAL)  
**Data:** 2025-09-30  
**Ambiente:** Staging → Production

---

## 🔐 1. Configuração de Ambiente

### Variáveis de Ambiente Obrigatórias

- [ ] `DATA_DIR` configurado
  ```bash
  export DATA_DIR="/path/to/data"
  ```

- [ ] `ALLOWED_HOSTS` definido (não vazio!)
  ```bash
  export ALLOWED_HOSTS='["api.selic.com", "*.selic.com"]'
  ```

- [ ] `ALLOWED_ORIGINS` para CORS
  ```bash
  export ALLOWED_ORIGINS='["https://app.selic.com"]'
  ```

- [ ] `MAX_MODEL_CACHE` definido
  ```bash
  export MAX_MODEL_CACHE=3
  ```

- [ ] `MAX_BATCH_SIZE` definido
  ```bash
  export MAX_BATCH_SIZE=10
  ```

- [ ] `API_VERSION` definida
  ```bash
  export API_VERSION="1.0.0"
  ```

- [ ] Chave de API configurada (não em código!)
  ```bash
  export API_KEY_SECRET="seu-segredo-aqui"
  ```

- [ ] `DEBUG=False` em produção
  ```bash
  export DEBUG=false
  ```

### ⚠️ Validações de Segurança

- [ ] ALLOWED_HOSTS não está vazio ou "*"
- [ ] ALLOWED_ORIGINS não está "*" em produção
- [ ] Chaves de API fora do repositório
- [ ] TLS obrigatório (HTTPS only)
- [ ] Stack traces desabilitados (DEBUG=false)

---

## 📦 2. Model Card e Metadata

### Conferir Versão Ativa

- [ ] Model card `MODEL_CARD_v1.0.2.md` revisado
- [ ] Metadata `data/models/v1.0.2/metadata.json` conferido
  ```json
  {
    "version": "v1.0.2",
    "data_hash": "sha256:60b22b64...",
    "n_observations": 246,
    "models": {
      "bvar_minnesota": {
        "stable": true,
        "eigs_max_abs": 0.412
      }
    }
  }
  ```

- [ ] Artefatos completos:
  - [ ] `model_lp.pkl` (4.8K)
  - [ ] `model_bvar.pkl` (19K)
  - [ ] `irfs_lp.json` (1.4K)
  - [ ] `irfs_bvar.json` (600B)
  - [ ] `metadata.json` (900B)

- [ ] BVAR estável: `max|eig| = 0.412 < 1.0` ✓
- [ ] IRFs normalizados: `0.51 bps/bps` ✓
- [ ] Identificação: `cholesky_fed_first` ✓

---

## 🧪 3. Testes End-to-End em Staging

### Teste de Previsão Completo

- [ ] **Cenário 1: Fed +25 bps**
  ```bash
  curl -X POST https://staging-api.selic.com/predict/selic-from-fed \
    -H "Content-Type: application/json" \
    -H "X-API-Key: sk_staging_test" \
    -d '{
      "fed_decision_date": "2025-10-29",
      "fed_move_bps": 25
    }'
  ```
  
  Validar:
  - [ ] Status 200
  - [ ] `expected_move_bps` presente
  - [ ] `distribution` com múltiplos de 25 bps
  - [ ] Soma de probabilidades = 1.0
  - [ ] `model_metadata.version` = "v1.0.2"
  - [ ] `model_metadata.data_hash` correto

- [ ] **Cenário 2: Fed 0 bps (neutro)**
  - [ ] Resposta válida
  - [ ] `expected_move_bps` próximo de 0

- [ ] **Cenário 3: Fed -25 bps (dovish)**
  - [ ] Resposta válida
  - [ ] Direção negativa ou neutra

- [ ] **Cenário 4: Fed +50 bps (hawkish forte)**
  - [ ] CI95 mais largo
  - [ ] Múltiplos valores na distribuição

- [ ] **Cenário 5: Batch (3 cenários simultâneos)**
  ```json
  {
    "scenarios": [
      {"fed_move_bps": 25, ...},
      {"fed_move_bps": 0, ...},
      {"fed_move_bps": -25, ...}
    ]
  }
  ```
  - [ ] Retorna 3 previsões
  - [ ] `model_version` consistente em todas

### Teste de Discretização

- [ ] Todos `delta_bps` são múltiplos de 25
- [ ] Soma de probabilidades = 1.0
- [ ] CI80 dentro de CI95
- [ ] `per_meeting` com datas Copom corretas

---

## 🏥 4. Health Checks

### Endpoint `/health`

- [ ] GET /health retorna 200
- [ ] Campo `status`: "healthy"
- [ ] Campo `model_version`: "v1.0.2"
- [ ] Campo `models_loaded`: true
- [ ] Campo `uptime_seconds` > 0
- [ ] Campo `latency_p50_ms` < 150ms
- [ ] Campo `latency_p95_ms` < 250ms

### Endpoint `/health/ready`

- [ ] Retorna 200 se modelos carregados
- [ ] Retorna 503 se modelos não carregados
- [ ] Campo `ready`: true quando OK
- [ ] Campo `models_loaded`: true
- [ ] Campo `checks` com detalhes

### Endpoint `/health/live`

- [ ] Responde rapidamente (< 50ms)
- [ ] Não depende de I/O externo
- [ ] Sempre retorna 200 se API está rodando

---

## 📊 5. Métricas e Observabilidade

### Prometheus Metrics

- [ ] Endpoint `/metrics` exposto
- [ ] Métricas disponíveis:
  - [ ] `http_request_duration_seconds` (histogram)
  - [ ] `http_requests_total` (counter)
  - [ ] `http_requests_in_progress` (gauge)
  - [ ] Custom: `model_predictions_total`
  - [ ] Custom: `model_version` (label)

### Latências Dentro do SLO

- [ ] p50 < 100ms
- [ ] p95 < 250ms ✅ TARGET BRONZE
- [ ] p99 < 500ms
- [ ] Medido sob carga de 50 RPS por 5 minutos

### Logs Estruturados

- [ ] Formato JSON
- [ ] Campos obrigatórios:
  - [ ] `timestamp`
  - [ ] `request_id`
  - [ ] `model_version`
  - [ ] `data_hash`
  - [ ] `fed_move_bps`
  - [ ] `horizon_months`
  - [ ] `latency_ms`
  - [ ] `error_code` (se erro)

- [ ] Rotação configurada (100MB, 5 arquivos)
- [ ] Sem PII em logs
- [ ] Retenção: 90 dias

---

## 🔒 6. Segurança

### TLS/HTTPS

- [ ] Certificado SSL válido instalado
- [ ] HTTP → HTTPS redirect configurado
- [ ] HSTS header habilitado
- [ ] TLS 1.2+ apenas

### Autenticação

- [ ] Sistema de chaves API funcional
- [ ] Chaves em cofre (AWS Secrets Manager / Vault)
- [ ] Zero segredos em código ou .env commitado
- [ ] Escopo por ambiente (dev/staging/prod)

### Rate Limiting

- [ ] Configurado: 10 req/min por chave (MVP)
- [ ] Headers de rate limit presentes:
  - [ ] `X-RateLimit-Limit`
  - [ ] `X-RateLimit-Remaining`
  - [ ] `X-RateLimit-Reset`

### CORS e TrustedHost

- [ ] ALLOWED_ORIGINS restrito (não "*")
- [ ] ALLOWED_HOSTS restrito (não vazio)
- [ ] Credentials habilitado apenas se necessário

---

## 🧪 7. Testes de Carga

### Teste com Locust

```bash
locust -f tests/load/locustfile.py \
  --host=https://staging-api.selic.com \
  --users=50 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless
```

### Critérios de Aceitação

- [ ] 15,000 requests (50 RPS × 5 min)
- [ ] Taxa de erro < 1%
- [ ] p50 < 100ms
- [ ] p95 < 250ms ✅ SLO BRONZE
- [ ] p99 < 500ms
- [ ] Sem memory leaks (RSS estável)
- [ ] CPU < 80% médio

---

## 🚦 8. Canary Deployment (1 hora)

### Configuração

- [ ] Canary com 10% do tráfego
- [ ] Duração: 1 hora
- [ ] Critérios de corte automáticos:
  - [ ] Taxa de 5xx > 1%
  - [ ] p95 > 300ms
  - [ ] Erro rate > 5%

### Validações Durante Canary

- [ ] Monitorar `/metrics` a cada 5 min
- [ ] Alertas configurados
- [ ] Dashboards visíveis
- [ ] Logs sendo coletados

### Critérios de Sucesso

- [ ] Zero 5xx em 1 hora
- [ ] p95 < 250ms sustentado
- [ ] Nenhum alerta disparado
- [ ] Previsões consistentes (não regression)

### Rollback Plan

- [ ] Script de rollback testado
- [ ] Versão anterior (v1.0.1) disponível
- [ ] Comando de rollback documentado:
  ```python
  model_service.set_active_version("v1.0.1")
  ```

---

## 📋 9. Validações Finais

### Idempotência

- [ ] Mesma requisição → mesma resposta (seed fixo)
- [ ] `model_version` fixo → previsão determinística
- [ ] Request_id único por requisição

### Versionamento

- [ ] `/models/versions` lista v1.0.2
- [ ] Metadata correto em cada versão
- [ ] `data_hash` presente e correto
- [ ] Compatibilidade retroativa (v1.0.0 ainda funciona)

### Error Handling

- [ ] 400 para `fed_move_bps` não múltiplo de 25
- [ ] 422 para `horizons_months` fora de [1, 12]
- [ ] 401 para chave API inválida
- [ ] 429 para rate limit excedido
- [ ] 503 para modelo não disponível
- [ ] 500 com request_id em todos os erros internos

---

## 📊 10. Monitoramento Pós-Deploy

### Primeira Hora

- [ ] Monitorar `/health/ready` a cada minuto
- [ ] Verificar `models_loaded: true`
- [ ] Latências dentro do SLO
- [ ] Zero erros 5xx

### Primeiro Dia

- [ ] Dashboard com métricas p50/p95/p99
- [ ] Alertas funcionando
- [ ] Logs sendo arquivados
- [ ] Requests distribuídos normalmente

### Primeira Semana

- [ ] SLO p95 < 250ms mantido
- [ ] Disponibilidade > 99.9%
- [ ] Feedback de usuários UAT
- [ ] Nenhum incidente crítico

---

## 🎯 11. Critérios de Go/No-Go

### GO (Todos devem ser ✅)

- [ ] ✅ Modelo v1.0.2 validado e aprovado
- [ ] ✅ Testes end-to-end passando (5 cenários)
- [ ] ✅ Teste de carga p95 < 250ms
- [ ] ✅ Health checks funcionando
- [ ] ✅ TLS configurado
- [ ] ✅ Chaves API em cofre
- [ ] ✅ Rate limiting testado
- [ ] ✅ Logs estruturados
- [ ] ✅ Métricas Prometheus
- [ ] ✅ Rollback plan documentado
- [ ] ✅ Runbook de incidentes criado

### NO-GO (Qualquer ❌ bloqueia)

- [ ] ❌ Modelo instável (max|eig| >= 1.0)
- [ ] ❌ Teste de carga falhando
- [ ] ❌ Latência p95 > 300ms
- [ ] ❌ Taxa de erro > 1%
- [ ] ❌ TLS não configurado
- [ ] ❌ Chaves hardcoded
- [ ] ❌ Stack traces expostos
- [ ] ❌ Sem monitoramento

---

## 🚀 12. Procedimento de Deploy

### Pre-Deploy

1. [ ] Backup da versão atual
2. [ ] Revisão de código aprovada
3. [ ] Testes passando (CI/CD green)
4. [ ] Model card assinado
5. [ ] Checklist de Go-Live 100%

### Deploy

1. [ ] Build da imagem Docker
   ```bash
   docker build -t quantum-x-api:v1.0.2 .
   ```

2. [ ] Push para registry
   ```bash
   docker push registry.selic.com/quantum-x-api:v1.0.2
   ```

3. [ ] Deploy canário (10%)
   ```bash
   kubectl apply -f k8s/canary-v1.0.2.yaml
   ```

4. [ ] Monitorar por 1 hora
   - [ ] Zero 5xx
   - [ ] p95 < 250ms
   - [ ] Logs OK

5. [ ] Promover para 100%
   ```bash
   kubectl apply -f k8s/production-v1.0.2.yaml
   ```

### Post-Deploy

1. [ ] Smoke test em produção
   ```bash
   curl https://api.selic.com/health
   curl https://api.selic.com/info
   ```

2. [ ] Verificar métricas por 15 minutos
3. [ ] Notificar stakeholders
4. [ ] Documentar deploy em changelog

---

## 📞 13. Runbook de Incidentes

### Incidente: Modelos não carregaram

**Sintoma:** `/health/ready` retorna 503, `models_loaded: false`

**Diagnóstico:**
```bash
# Verificar logs
tail -f logs/api.log | grep "Carregando modelos"

# Verificar artefatos
ls -lh data/models/v1.0.2/
```

**Correção:**
```bash
# Retreinar modelo
python scripts/train_pipeline.py --version v1.0.2

# Ou ativar versão anterior
# No código: model_service.set_active_version("v1.0.1")
```

---

### Incidente: Latência alta (p95 > 300ms)

**Sintoma:** `/metrics` mostra `http_request_duration_seconds{quantile="0.95"} > 0.3`

**Diagnóstico:**
```bash
# Verificar cache
curl https://api.selic.com/models/cache-info

# Verificar CPU/memória
htop
```

**Correção:**
```bash
# Limpar cache se necessário
# Aumentar MAX_MODEL_CACHE se CPU OK
# Escalar horizontalmente se CPU > 80%
```

---

### Incidente: Taxa de erro > 5%

**Sintoma:** `/metrics` mostra muitos 4xx ou 5xx

**Diagnóstico:**
```bash
# Agrupar por código de erro
cat logs/api.log | jq '.status_code' | sort | uniq -c

# Ver erros específicos
cat logs/api.log | jq 'select(.level=="ERROR")'
```

**Correção:**
- 4xx: Validação de entrada → documentar melhor API
- 5xx: Erro interno → verificar stack trace, rollback se necessário

---

## 🎯 14. Status Atual (Pre-Deploy)

### ✅ Completo

- [x] Pipeline de treino end-to-end
- [x] BVAR v2.1 FINAL production-ready
- [x] ModelService v2.1 com 10 ajustes
- [x] API startup carregando modelos
- [x] Endpoints / e /info funcionando
- [x] Model Card documentado
- [x] v1.0.2 treinada e validada

### ⬜ Pendente (Sprint 1 Remanescente)

- [ ] Remover mocks do PredictionService
- [ ] Implementar calendário Copom
- [ ] Discretização na resposta da API
- [ ] Teste end-to-end completo

### ⬜ Pendente (Sprint 2-3)

- [ ] Prometheus instrumentado
- [ ] Testes de carga executados
- [ ] TLS configurado
- [ ] Chaves API em cofre
- [ ] UAT com 5 casos
- [ ] Canary testado

---

## 📝 15. Sign-off

### Aprovações Necessárias

- [ ] **Tech Lead:** Código revisado e aprovado
- [ ] **Data Scientist:** Modelo validado cientificamente
- [ ] **SRE:** Infraestrutura e monitoramento prontos
- [ ] **Security:** Auditoria de segurança aprovada
- [ ] **Product Owner:** UAT assinado

### Documento de Aprovação

```
APROVAÇÃO DE GO-LIVE

Projeto: API FED-Selic Quantum-X
Versão: v1.0.2 (BVAR v2.1 FINAL)
Data: ___ / ___ / 2025

Aprovações:
[ ] Tech Lead: _______________  Data: ___ / ___ / 2025
[ ] Data Scientist: __________  Data: ___ / ___ / 2025
[ ] SRE: _____________________  Data: ___ / ___ / 2025
[ ] Security: ________________  Data: ___ / ___ / 2025
[ ] Product Owner: ___________  Data: ___ / ___ / 2025

Status: PENDING / APPROVED / REJECTED
```

---

## 🏆 16. Certificação Bronze

### Critérios Bronze (Revisar Após Completar Checklist)

- [ ] Foundation e Dados (5/5)
- [ ] Modelagem e Treino (5/5)
- [ ] Validação Científica (suites executadas + gates)
- [ ] API e Contratos (5/5)
- [ ] Observabilidade (5/5)
- [ ] MLOps (pipeline reproduzível)
- [ ] Segurança (TLS + chave)
- [ ] Performance (p95 < 250ms)
- [ ] Testes (cobertura ≥ 80%)
- [ ] UAT (5/5 casos aprovados)

**Certificação:** ⬜ BRONZE PENDENTE

---

## 📅 Timeline de Deploy

```
Semana 1 (Sprint 1):
├── Tarefa 1.1 ✅ COMPLETA (Pipeline + BVAR v2.1)
├── Tarefa 1.2 ✅ COMPLETA (ModelService v2.1)
├── Tarefa 1.3 ⬜ PENDENTE (Remover mocks)
└── Tarefa 1.4 ⬜ PENDENTE (Discretização + Copom)

Semana 2 (Sprint 2):
├── Observabilidade (Prometheus)
├── Segurança (TLS + Auth)
└── Testes de carga

Semana 3 (Sprint 3):
├── Testes unitários (≥80%)
├── UAT (5 casos)
└── Canary + Go-Live

TARGET: 21/10/2025 🎯
```

---

**Status Atual:** Sprint 1 - 50% completo (Tarefas 1.1 e 1.2 ✅)  
**Próximo:** Tarefa 1.3 - Remover mocks do PredictionService  
**ETA Bronze:** 21/10/2025 (3 semanas)

