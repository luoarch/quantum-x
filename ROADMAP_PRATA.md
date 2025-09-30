# 🥈 Roadmap para Prata (Silver) - API FED-Selic

**Data de Início:** 30 de Setembro de 2025  
**Duração Estimada:** 6-8 semanas  
**Versão do Projeto:** 2.0 (Quantum-X)

---

## 🎯 Objetivo

**Elevar a maturidade da API de Bronze (90-95%) para Prata (≥85%), habilitando uso interno amplo com qualidade de produção, observabilidade completa, gates automáticos e canário.**

---

## 📊 Status Atual (Pós-Sprint 1)

| Categoria | Status Atual | Target Prata | Gap |
|-----------|--------------|--------------|-----|
| **Foundation e Dados** | 85% | 90% | 5% |
| **Modelagem e Treino** | 100% | 100% | 0% ✅ |
| **Validação Científica** | 85% | 95% | 10% |
| **API e Contratos** | 95% | 95% | 0% ✅ |
| **MLOps** | 75% | 95% | 20% |
| **Observabilidade** | 70% | 95% | 25% 🔴 |
| **Segurança** | 80% | 95% | 15% |
| **Performance** | 0% | 90% | 90% 🔴 |
| **Testes** | 0% | 85% | 85% 🔴 |
| **UAT/Rollout** | 0% | 80% | 80% 🔴 |

**🔴 GAPS CRÍTICOS PARA PRATA:**
1. Observabilidade (Prometheus, dashboards)
2. Performance (métricas, testes de carga)
3. Testes (unitários, integração, e2e)
4. UAT (casos documentados e assinados)
5. MLOps (CI/CD, gates automáticos)

---

## 🗓️ Roadmap por Sprints

### 📦 **Sprint 2: Completar Bronze 100% (Semanas 4-5)**

**Objetivo:** Completar os últimos 5-10% do Bronze para habilitar certificação completa.

**Duração:** 2 semanas  
**Prioridade:** 🔴 CRÍTICA

#### **2.1 Testes Automatizados (Semana 4)**

**🎯 Meta: Cobertura ≥80%**

##### **Dia 1-2: Setup de Testes**
- [ ] Configurar pytest + pytest-cov
- [ ] Setup fixtures para modelos, dados, API
- [ ] Configurar pytest.ini com plugins
- [ ] Criar estrutura tests/unit/ e tests/integration/

##### **Dia 3-4: Testes Unitários (Core)**
- [ ] **Schemas (15 testes)**
  - Validação de PredictionRequest
  - Validação de BatchError
  - Validators (fed_move_bps % 25, consistency)
- [ ] **ModelService (12 testes)**
  - load_model(), get_active_version()
  - Cache LRU (eviction, max size)
  - Self-checks (estabilidade, dimensões)
- [ ] **PredictionService (18 testes)**
  - Discretização analítica
  - Normalização (sum=1.0)
  - Decay adaptativo
  - Copom mapping

##### **Dia 5: Testes Unitários (Modelos)**
- [ ] **BVAR (10 testes)**
  - Estabilidade (eigenvalues)
  - IRF normalization
  - Conditional forecast consistency
  - Prior scaling
- [ ] **LP (8 testes)**
  - Bootstrap CI coverage
  - Horizons ordering
  - Shrinkage effect

**Entregável:** ≥80% cobertura em src/

---

#### **2.2 Observabilidade Completa (Semana 5)**

**🎯 Meta: Prometheus + Grafana operacionais**

##### **Dia 1-2: Prometheus Instrumentação**
- [ ] Adicionar `prometheus-fastapi-instrumentator`
- [ ] Expor `/metrics` endpoint
- [ ] Métricas automáticas:
  - `http_request_duration_seconds` (p50, p95, p99)
  - `http_requests_total` (por status, endpoint)
  - `http_request_size_bytes`, `http_response_size_bytes`
- [ ] Métricas customizadas:
  - `prediction_requests_total` (por model_version)
  - `prediction_latency_seconds` (por horizonte)
  - `model_load_duration_seconds`
  - `cache_hit_ratio`

##### **Dia 3: Grafana Dashboards**
- [ ] Setup docker-compose.observability.yml
  - Prometheus (scrape /metrics a cada 15s)
  - Grafana (dashboards pré-configurados)
- [ ] Dashboard 1: HTTP Metrics
  - Request rate, latency (p50/p95/p99), errors
- [ ] Dashboard 2: Business Metrics
  - Predictions por versão, latência por horizonte
  - Cache hit rate, modelo ativo
- [ ] Dashboard 3: System Health
  - CPU, memória, uptime

##### **Dia 4-5: Logging Estruturado Completo**
- [ ] Configurar structlog
- [ ] Adicionar campos obrigatórios em todos logs:
  - `request_id`, `model_version`, `data_hash`, `action`, `success`
- [ ] Implementar log levels consistentes
- [ ] Configurar rotação de logs (10MB, 5 arquivos)
- [ ] Setup ELK stack opcional (dev)

**Entregável:** Observabilidade production-ready

---

### 🏗️ **Sprint 3: Performance e Segurança (Semanas 6-7)**

**Objetivo:** Validar SLOs de performance e hardening de segurança.

**Duração:** 2 semanas  
**Prioridade:** 🔴 CRÍTICA

#### **3.1 Performance e SLOs (Semana 6)**

##### **Dia 1-2: Setup de Testes de Carga**
- [ ] Instalar Locust ou k6
- [ ] Criar cenários de carga:
  - Scenario 1: 10 RPS steady (5 min)
  - Scenario 2: 50 RPS ramp-up (10 min)
  - Scenario 3: Spike test (100 RPS por 2 min)
- [ ] Configurar coleta de métricas (p50/p95/p99)

##### **Dia 3: Execução e Otimização**
- [ ] Executar baseline (sem otimizações)
- [ ] Identificar gargalos (profiling)
- [ ] Otimizações:
  - Lazy loading de modelos
  - Cache de discretização
  - Async I/O onde aplicável
- [ ] Re-executar e validar **p95 < 250ms**

##### **Dia 4-5: Monitoramento Contínuo**
- [ ] Configurar alertas Prometheus:
  - `http_request_duration_seconds{quantile="0.95"} > 0.250`
  - `http_requests_total{status=~"5.."} / rate(5m) > 0.01`
- [ ] Setup Alertmanager (notificações via webhook/email)
- [ ] Runbook básico para degradação de performance

**Entregável:** p95 < 250ms validado e monitorado

---

#### **3.2 Segurança Hardened (Semana 7)**

##### **Dia 1-2: TLS e HTTPS**
- [ ] Gerar certificado autoassinado (dev)
- [ ] Configurar Uvicorn com SSL
- [ ] Testar endpoints via HTTPS
- [ ] Documentar setup de certificados (prod)

##### **Dia 3: Secrets Management**
- [ ] Implementar loading de API keys de variável de ambiente
- [ ] Criar `.env.example` com chaves dummy
- [ ] Validar que API_KEYS não estão hardcoded
- [ ] Opcional: Setup Vault/AWS Secrets Manager

##### **Dia 4-5: Security Headers e Rate Limiting**
- [ ] Validar headers de segurança:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security` (HSTS)
- [ ] Testar rate limiting (429 responses)
- [ ] Audit de dependências (safety check)
- [ ] OWASP Top 10 checklist

**Entregável:** Segurança hardened para piloto amplo

---

### 🧪 **Sprint 4: UAT e Certificação Bronze (Semana 8)**

**Objetivo:** Executar UAT, documentar, assinar e certificar Bronze 100%.

**Duração:** 1 semana  
**Prioridade:** 🔴 CRÍTICA

##### **Dia 1-2: Definir Casos de UAT**
- [ ] **Caso 1:** Fed +25 bps (hawkish)
  - Request: `{"fed_move_bps": 25, "fed_move_dir": "1", ...}`
  - Validar: distribution, CI80/95, rationale
- [ ] **Caso 2:** Fed 0 bps (neutral)
  - Validar: probabilidade maior em delta=0
- [ ] **Caso 3:** Fed -25 bps (dovish)
  - Validar: resposta negativa da Selic
- [ ] **Caso 4:** Fed +50 bps (shock)
  - Validar: CI95 amplo, incerteza alta
- [ ] **Caso 5:** Fed +25 bps com surpresa de +10 bps
  - Validar: impacto adicional no modelo

##### **Dia 3-4: Executar UAT**
- [ ] Ambiente: staging com modelo v1.0.2
- [ ] Executar 5 casos via Postman/curl
- [ ] Documentar resultados:
  - Screenshots de responses
  - Logs estruturados
  - Métricas de latência
  - Análise qualitativa (rationale faz sentido?)

##### **Dia 5: Documentação e Assinatura**
- [ ] Criar `UAT_REPORT.md`:
  - Casos executados
  - Resultados observados vs esperados
  - Desvios e explicações
  - Aprovação ou ajustes necessários
- [ ] Assinar UAT (aprovação formal)
- [ ] **🏆 CERTIFICAR BRONZE 100%**

**Entregável:** Bronze certificado com UAT assinado

---

### 🥈 **Sprints 5-7: Prata (Semanas 9-14)**

**Objetivo:** Implementar gates automáticos, CI/CD, alertas e canário para atingir Prata.

**Duração:** 6 semanas  
**Prioridade:** 🟡 ALTA

---

#### **Sprint 5: Gates de Qualidade Automáticos (Semanas 9-10)**

##### **5.1 Gate de Cobertura CI**
- [ ] Calcular cobertura CI95 em backtest histórico
- [ ] Threshold: cobertura ≥85%
- [ ] Gate automático: bloquear promoção se < 85%
- [ ] Métricas adicionais:
  - Brier Score (vs baseline random)
  - CRPS (Continuous Ranked Probability Score)

##### **5.2 Gate de Estabilidade**
- [ ] Verificar eigenvalues BVAR < 1.0
- [ ] Verificar IRF convergência (decaimento exponencial)
- [ ] Bloquear se modelo instável

##### **5.3 Gate de Performance**
- [ ] Executar mini load test (10 RPS, 1 min)
- [ ] Threshold: p95 < 250ms
- [ ] Bloquear se exceder

**Entregável:** 3 gates automáticos funcionais

---

#### **Sprint 6: CI/CD e Registro de Modelos (Semanas 11-12)**

##### **6.1 GitHub Actions Pipeline**
- [ ] `.github/workflows/ci.yml`:
  - Lint (ruff, black)
  - Testes (pytest com coverage ≥80%)
  - Gates científicos (estabilidade, cobertura CI)
  - Build de artefatos
- [ ] `.github/workflows/cd.yml`:
  - Deploy para staging (automático em merge para main)
  - Deploy para prod (manual approval)

##### **6.2 Registro de Modelos**
- [ ] Implementar `ModelRegistry` service
- [ ] Armazenar artefatos versionados:
  - `models/v{version}/model_lp.pkl`
  - `models/v{version}/model_bvar.pkl`
  - `models/v{version}/metadata.json`
  - `models/v{version}/validation_report.json`
- [ ] API para promoção:
  - `/models/{version}/promote` (staging → prod)
  - Validar gates antes de promover

##### **6.3 Versionamento Semântico**
- [ ] Implementar auto-bump de versão:
  - Major: quebra de contrato
  - Minor: nova feature (regime hint, etc.)
  - Patch: bugfix
- [ ] Tag Git automático

**Entregável:** CI/CD completo com registro de modelos

---

#### **Sprint 7: Alertas, RBAC e Canário (Semanas 13-14)**

##### **7.1 Alertmanager e Runbooks**
- [ ] Configurar Alertmanager
- [ ] Alertas críticos:
  - `HighLatency` (p95 > 250ms por 5 min)
  - `HighErrorRate` (5xx > 1% por 5 min)
  - `ModelLoadFailure` (startup failure)
- [ ] Runbooks para cada alerta:
  - Diagnóstico
  - Mitigação
  - Escalação

##### **7.2 RBAC Básico**
- [ ] Níveis de acesso:
  - `viewer`: read-only (GET /predict, /health)
  - `operator`: manage models (POST /models/activate)
  - `admin`: full access (DELETE, config)
- [ ] Implementar no AuthenticationMiddleware
- [ ] Documentar permissões

##### **7.3 Deploy Canário**
- [ ] Implementar estratégia de canário:
  - 10% tráfego para nova versão (30 min)
  - Monitorar: latência, erros, métricas de negócio
  - Auto-rollback se:
    - Error rate > 2x baseline
    - Latency p95 > 1.5x baseline
- [ ] Script de rollback manual
- [ ] Testar canário em staging

**Entregável:** Canário funcional com auto-rollback

---

## 🏆 Critérios de Aceitação - Prata

### ✅ **Checklist Prata (85% em todos pilares)**

| # | Critério | Target | Status |
|---|----------|--------|--------|
| 1 | **Testes unitários** | ≥80% coverage | ⏳ Sprint 2 |
| 2 | **Testes integração** | ≥20 cenários e2e | ⏳ Sprint 2 |
| 3 | **Performance p95** | <250ms validado | ⏳ Sprint 3 |
| 4 | **Observabilidade** | Prometheus + Grafana | ⏳ Sprint 2 |
| 5 | **Logging estruturado** | Todos campos obrigatórios | ⏳ Sprint 2 |
| 6 | **Segurança TLS** | HTTPS em staging/prod | ⏳ Sprint 3 |
| 7 | **Secrets management** | Env vars ou Vault | ⏳ Sprint 3 |
| 8 | **UAT assinado** | 5 casos executados | ⏳ Sprint 4 |
| 9 | **Gates automáticos** | 3 gates funcionais | ⏳ Sprint 5 |
| 10 | **CI/CD** | GitHub Actions completo | ⏳ Sprint 6 |
| 11 | **Registro de modelos** | Versionamento automático | ⏳ Sprint 6 |
| 12 | **Alertas** | Alertmanager + runbooks | ⏳ Sprint 7 |
| 13 | **RBAC** | 3 níveis de acesso | ⏳ Sprint 7 |
| 14 | **Canário** | Auto-rollback funcional | ⏳ Sprint 7 |
| 15 | **Disponibilidade** | 99.95% em staging (2 semanas) | ⏳ Sprint 7 |

---

## 📊 Métricas de Progresso

### **Tabela de Evolução**

| Métrica | Bronze | Prata Target | Status Atual |
|---------|--------|--------------|--------------|
| **Cobertura Testes** | 80% | 85% | 0% → 85% 🔴 |
| **Latência P95** | <250ms | <200ms | - → 180ms ⏳ |
| **Disponibilidade** | 99.9% | 99.95% | - → 99.95% ⏳ |
| **Gates Ativos** | 0 | 3 | 0 → 3 🔴 |
| **Runbooks** | 1 | 3 | 0 → 3 🔴 |
| **Ambientes** | 2 (dev, staging) | 3 (+ prod) | 2 → 3 ⏳ |
| **Cobertura CI95** | ≥85% | ≥90% | - → 90% 🔴 |
| **MTTR (Mean Time to Restore)** | - | <30min | - → 25min ⏳ |

---

## 🚀 Plano de Execução

### **Timeline Visual**

```
Semana 4     │████████░░│ Testes Unitários
Semana 5     │██████████│ Observabilidade
Semana 6     │████████░░│ Performance
Semana 7     │██████████│ Segurança
Semana 8     │██████████│ UAT + Cert Bronze
             └─────────────────────────────
Semana 9-10  │██████████│ Gates Automáticos
Semana 11-12 │██████████│ CI/CD + Registro
Semana 13-14 │██████████│ Alertas + Canário
             └─────────────────────────────
             🏆 PRATA CERTIFICADO
```

---

## 📝 Próximos Passos Imediatos

### **🔴 AÇÃO IMEDIATA (Hoje):**
1. ✅ Criar branch `feat/silver-sprint-2-tests`
2. ⏳ Setup pytest + pytest-cov
3. ⏳ Criar fixtures básicos
4. ⏳ Primeiro teste: `test_prediction_request_validation`

### **📅 Esta Semana (Semana 4):**
- Completar setup de testes
- Atingir 50% de cobertura em schemas e services
- Documentar estratégia de testes

### **🎯 Este Mês (Outubro):**
- Completar Sprint 2 e 3
- Certificar Bronze 100%
- Iniciar Sprint 5 (gates)

---

## 🎓 Lições do Sprint 1 Aplicadas

**✅ O que funcionou bem:**
- Foco em qualidade científica desde o início
- Governança por headers e logs estruturados
- Fail-soft e graceful degradation

**🔄 O que melhoraremos:**
- Testes desde o início (não deixar para depois)
- Observabilidade early (Prometheus desde Sprint 2)
- Performance testing contínuo (não só no final)

---

## 📚 Referências

- [ANALISE_MATURIDADE.md](./ANALISE_MATURIDADE.md) - Análise completa de maturidade
- [REQUISITOS.md](./REQUISITOS.md) - Requisitos funcionais e não-funcionais
- [GO_LIVE_CHECKLIST.md](./GO_LIVE_CHECKLIST.md) - Checklist de go-live
- [MODEL_CARD_v1.0.2.md](./MODEL_CARD_v1.0.2.md) - Validação técnica do modelo

---

**🎊 Status:** ROADMAP APROVADO  
**🚀 Next:** Sprint 2 - Testes e Observabilidade  
**🏆 Goal:** Prata em 6-8 semanas

