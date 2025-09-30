# 🎯 Roadmap para Certificação Bronze

**Objetivo:** Completar todos os requisitos Bronze em 3 semanas  
**Status Atual:** Bronze Parcial (60-70%)  
**Data Início:** 30/09/2025  
**Data Alvo:** 21/10/2025

---

## 📅 Visão Geral dos Sprints

```
Sprint 1 (Semana 1)    Sprint 2 (Semana 2)    Sprint 3 (Semana 3)
    MLOps                 Observabilidade            Testes
      +                        +                       +
    Dados                  Segurança                 UAT
      ↓                        ↓                       ↓
 API Funcional          Monitoramento           Bronze Completo
```

---

## 🔥 Sprint 1: MLOps + Dados + API Funcional

**Duração:** 5 dias  
**Objetivo:** API respondendo com previsões reais de modelos treinados

### 📋 Tarefas Detalhadas

#### 1.1 Pipeline de Treino End-to-End (2 dias)

**Arquivo:** `scripts/train_pipeline.py`

```python
# Criar script de treino completo com:
- Ingestão de dados (fed_selic_combined.csv)
- Hash SHA256 do dataset
- Preparação de features (lags, diferenças)
- Treino de LP e BVAR
- Cálculo de IRFs
- Materialização de artefatos
- Geração de metadata.json

# Estrutura de saída:
data/models/v{version}/
  ├── model_lp.pkl
  ├── model_bvar.pkl
  ├── irfs.npy
  ├── metadata.json
  └── validation_report.json
```

**Checklist:**
- [ ] Criar `scripts/train_pipeline.py`
- [ ] Implementar função `hash_dataset(df: pd.DataFrame) -> str`
- [ ] Implementar função `save_artifacts(model, version: str, metadata: dict)`
- [ ] Testar pipeline com dados existentes
- [ ] Gerar versão v1.0.0 com relatório

**Critério de Aceitação:**
```bash
$ python scripts/train_pipeline.py --version v1.0.0
✅ Dataset hash: sha256:abc123...
✅ LP treinado: 12 horizontes, R² médio 0.65
✅ BVAR treinado: 2 variáveis, 2 lags
✅ Artefatos salvos em: data/models/v1.0.0/
```

---

#### 1.2 Carregar Modelos Reais na API (1 dia)

**Arquivo:** `src/services/model_service.py`

**Checklist:**
- [ ] Implementar `ModelService.load_model(version: str)`
  - [ ] Carregar `model_lp.pkl` e `model_bvar.pkl`
  - [ ] Carregar `metadata.json`
  - [ ] Cache em memória
  
- [ ] Atualizar `ModelService.list_versions()` para ler diretório real
- [ ] Implementar `ModelService.get_active_model()` com fallback

**Código Exemplo:**
```python
def load_model(self, version: str) -> Tuple[LocalProjectionsForecaster, BVARMinnesota]:
    model_dir = Path(f"data/models/{version}")
    
    with open(model_dir / "model_lp.pkl", "rb") as f:
        lp_model = pickle.load(f)
    
    with open(model_dir / "model_bvar.pkl", "rb") as f:
        bvar_model = pickle.load(f)
    
    with open(model_dir / "metadata.json") as f:
        metadata = json.load(f)
    
    self._model_cache[version] = {
        "lp": lp_model,
        "bvar": bvar_model,
        "metadata": metadata
    }
    
    return lp_model, bvar_model
```

**Critério de Aceitação:**
```python
# Teste
model_service = ModelService()
lp, bvar = await model_service.load_model("v1.0.0")
assert lp is not None
assert bvar.n_lags == 2
```

---

#### 1.3 Remover Mocks e Conectar API (1 dia)

**Arquivo:** `src/services/prediction_service.py`

**Checklist:**
- [ ] Atualizar `PredictionService.predict()` para usar modelos reais
- [ ] Implementar lógica de escolha LP vs BVAR por `regime_hint`
- [ ] Extrair IRFs dos modelos treinados
- [ ] Retornar `model_metadata` real (não mock)

**Código Exemplo:**
```python
async def predict(self, request: PredictionRequest) -> PredictionResponse:
    # Carregar modelo
    lp_model, bvar_model = await self.model_service.load_model(
        request.model_version or "latest"
    )
    
    # Escolher modelo por regime
    if request.regime_hint == "stress":
        forecasts = bvar_model.conditional_forecast([request.fed_move_bps])
    else:
        current_state = await self._get_current_state()
        forecasts = lp_model.forecast(request.fed_move_bps, current_state)
    
    # Converter IRFs em resposta
    return self._convert_to_response(forecasts, lp_model, request)
```

---

#### 1.4 Discretização e Calendário Copom (1 dia)

**Novo Arquivo:** `src/services/copom_service.py`

**Checklist:**
- [ ] Criar classe `CopomCalendar` com reuniões 2024-2026
- [ ] Implementar `discretize_distribution(irf: np.ndarray, step: int = 25)`
- [ ] Implementar `map_to_copom_meetings(distribution: List[float], ref_date: datetime)`
- [ ] Calcular `prob_move_within_next_copom`

**Código Exemplo:**
```python
class CopomCalendar:
    MEETINGS_2025 = [
        datetime(2025, 1, 31),
        datetime(2025, 3, 19),
        datetime(2025, 5, 7),
        # ... até dezembro 2025
    ]
    
    def next_meeting_after(self, date: datetime) -> datetime:
        for meeting in self.MEETINGS_2025:
            if meeting > date:
                return meeting
        return None

def discretize_distribution(mean: float, std: float, ci_lower: float, ci_upper: float) -> List[DistributionPoint]:
    # Criar distribuição normal
    # Discretizar em múltiplos de 25 bps
    # Retornar lista de {delta_bps, probability}
    ...
```

**Critério de Aceitação:**
```python
copom = CopomCalendar()
next_meeting = copom.next_meeting_after(datetime(2025, 10, 29))
assert next_meeting == datetime(2025, 11, 5)

dist = discretize_distribution(mean=25, std=15, ci_lower=0, ci_upper=50)
assert all(d.delta_bps % 25 == 0 for d in dist)
assert sum(d.probability for d in dist) == pytest.approx(1.0)
```

---

### ✅ Entregável Sprint 1

- [x] Pipeline de treino executável gerando v1.0.0
- [x] API carregando modelos reais no startup
- [x] Endpoint `/predict` retornando previsões reais
- [x] Distribuições discretizadas em 25 bps
- [x] Mapeamento para reuniões Copom

**Teste End-to-End:**
```bash
$ curl -X POST http://localhost:8000/predict/selic-from-fed \
  -H "Content-Type: application/json" \
  -d '{
    "fed_decision_date": "2025-10-29",
    "fed_move_bps": 25
  }'

{
  "expected_move_bps": 25,
  "horizon_months": "1-3",
  "prob_move_within_next_copom": 0.58,
  "per_meeting": [
    {"copom_date": "2025-11-05", "delta_bps": 25, "probability": 0.58}
  ],
  "model_metadata": {
    "version": "v1.0.0",
    "data_hash": "sha256:abc123...",
    "methodology": "LP primary, BVAR fallback"
  }
}
```

---

## 🔍 Sprint 2: Observabilidade + Segurança

**Duração:** 5 dias  
**Objetivo:** Monitoramento funcional e segurança básica

### 📋 Tarefas Detalhadas

#### 2.1 Instrumentação Prometheus (1 dia)

**Checklist:**
- [ ] Instalar `prometheus-fastapi-instrumentator`
- [ ] Adicionar instrumentação em `src/api/main.py`
- [ ] Expor endpoint `/metrics`
- [ ] Coletar métricas:
  - `http_request_duration_seconds` (histogram p50/p95/p99)
  - `http_requests_total` (counter por método/status)
  - `http_requests_in_progress` (gauge)

**Código:**
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)

# Instrumentar
Instrumentator().instrument(app).expose(app)
```

**Critério de Aceitação:**
```bash
$ curl http://localhost:8000/metrics | grep http_request_duration
http_request_duration_seconds_bucket{le="0.1",method="POST",path="/predict/selic-from-fed"} 45
http_request_duration_seconds_sum{method="POST"} 12.3
```

---

#### 2.2 Logging Estruturado Completo (1 dia)

**Arquivo:** `src/services/logging_service.py`

**Checklist:**
- [ ] Configurar `structlog` para JSON output
- [ ] Adicionar contexto em middleware:
  - `request_id`
  - `model_version`
  - `data_hash`
  - `fed_move_bps`
  - `latency_ms`
  
- [ ] Implementar spans básicos:
  - `span.validation` (entrada)
  - `span.inference` (previsão)
  - `span.postprocess` (discretização)

**Código:**
```python
import structlog

logger = structlog.get_logger()

async def predict_with_logging(request: PredictionRequest):
    log = logger.bind(
        request_id=request_id,
        fed_move_bps=request.fed_move_bps
    )
    
    log.info("validation_start")
    # ... validação
    log.info("validation_end", duration_ms=10)
    
    log.info("inference_start", model_version="v1.0.0")
    # ... previsão
    log.info("inference_end", duration_ms=120)
    
    log.info("postprocess_start")
    # ... discretização
    log.info("postprocess_end", duration_ms=5)
```

**Critério de Aceitação:**
```json
{
  "event": "inference_end",
  "request_id": "uuid-123",
  "model_version": "v1.0.0",
  "data_hash": "sha256:abc",
  "fed_move_bps": 25,
  "duration_ms": 120,
  "timestamp": "2025-10-01T10:30:00Z"
}
```

---

#### 2.3 Sistema de Chaves API (1 dia)

**Novo Arquivo:** `src/services/api_key_service.py`

**Checklist:**
- [ ] Criar classe `APIKeyService` com storage in-memory
- [ ] Gerar chaves aleatórias: `sk_test_xyz123...`
- [ ] Validar chave em `AuthenticationMiddleware`
- [ ] Implementar rate limiting por chave

**Código:**
```python
class APIKeyService:
    def __init__(self):
        # Storage in-memory para MVP Bronze
        self._keys = {
            "sk_test_bronze_123": {
                "name": "test_key",
                "rate_limit": 10,  # req/min
                "created_at": datetime.now()
            }
        }
    
    def validate_key(self, key: str) -> bool:
        return key in self._keys
    
    def get_rate_limit(self, key: str) -> int:
        return self._keys.get(key, {}).get("rate_limit", 10)

# Middleware
async def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key")
    if not api_key_service.validate_key(key):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

**Critério de Aceitação:**
```bash
# Sem chave
$ curl http://localhost:8000/predict/selic-from-fed
{"error_code": "authentication_failed"}

# Com chave válida
$ curl -H "X-API-Key: sk_test_bronze_123" \
  http://localhost:8000/predict/selic-from-fed
{"expected_move_bps": 25, ...}
```

---

#### 2.4 TLS e Rate Limiting (1 dia)

**Checklist:**
- [ ] Gerar certificado autoassinado para dev
  ```bash
  openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
  ```
- [ ] Configurar uvicorn com SSL
  ```python
  uvicorn.run(
      "src.api.main:app",
      host="0.0.0.0",
      port=8443,
      ssl_keyfile="key.pem",
      ssl_certfile="cert.pem"
  )
  ```
- [ ] Implementar rate limiting funcional (10 req/min)
- [ ] Adicionar header `X-RateLimit-Remaining`

**Critério de Aceitação:**
```bash
$ curl https://localhost:8443/predict/selic-from-fed \
  -H "X-API-Key: sk_test_bronze_123" \
  --insecure

# Header de resposta
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1633000000
```

---

#### 2.5 Rotação de Logs (1 dia)

**Arquivo:** `src/core/config.py`

**Checklist:**
- [ ] Configurar `logrotate` ou `RotatingFileHandler`
- [ ] Logs em `logs/api.log`
- [ ] Rotação: 100MB por arquivo, manter 5 arquivos
- [ ] Formato JSON para parsing

**Código:**
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/api.log",
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=5
)
```

---

### ✅ Entregável Sprint 2

- [x] Prometheus exportando p50/p95/p99
- [x] Logs estruturados com spans
- [x] Chaves API funcionais com validação
- [x] TLS configurado (cert autoassinado)
- [x] Rate limiting ativo (10 req/min)
- [x] Rotação de logs

**Teste de Observabilidade:**
```bash
# Métricas
$ curl http://localhost:8000/metrics | grep p95
http_request_duration_seconds{quantile="0.95"} 0.150

# Logs
$ tail -f logs/api.log | grep inference_end
{"event": "inference_end", "duration_ms": 120, ...}

# Rate limit
$ for i in {1..15}; do curl -H "X-API-Key: sk_test_bronze_123" \
  https://localhost:8443/health; done
# 11ª requisição retorna 429
```

---

## ✅ Sprint 3: Testes + UAT + Certificação

**Duração:** 5 dias  
**Objetivo:** Testes completos, UAT assinado, Bronze certificado

### 📋 Tarefas Detalhadas

#### 3.1 Testes Unitários (2 dias)

**Estrutura:**
```
tests/unit/
  ├── test_schemas.py          # Validação Pydantic
  ├── test_discretization.py   # Discretização 25 bps
  ├── test_copom_calendar.py   # Calendário
  ├── test_api_key.py          # Auth
  └── test_model_loading.py    # Carregar modelos
```

**Checklist:**
- [ ] `test_schemas.py` (10 testes)
  - [ ] Validar fed_move_bps múltiplo de 25
  - [ ] Rejeitar horizons fora de [1, 12]
  - [ ] Validar consistência fed_move_dir
  
- [ ] `test_discretization.py` (8 testes)
  - [ ] Distribuição soma 1.0
  - [ ] Todos delta_bps múltiplos de 25
  - [ ] CI80 dentro de CI95
  
- [ ] `test_copom_calendar.py` (5 testes)
  - [ ] Próxima reunião correta
  - [ ] Mapeamento mês → reunião
  
- [ ] `test_api_key.py` (5 testes)
  - [ ] Validar chave válida
  - [ ] Rejeitar chave inválida
  - [ ] Rate limit por chave
  
- [ ] `test_model_loading.py` (5 testes)
  - [ ] Carregar LP e BVAR
  - [ ] Cache funcional
  - [ ] Fallback para latest

**Comando:**
```bash
$ pytest tests/unit/ --cov=src --cov-report=html

---------- coverage: platform darwin, python 3.12.0 -----------
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/services/prediction_service.py    120      18    85%
src/services/copom_service.py          45       5    89%
src/api/schemas.py                    200      20    90%
-----------------------------------------------------
TOTAL                                1500     180    88%
```

**Critério de Aceitação:**
- [ ] Cobertura geral ≥ 80%
- [ ] Todos os testes passando
- [ ] Nenhum warning crítico

---

#### 3.2 Testes de Integração (1 dia)

**Estrutura:**
```
tests/integration/
  ├── test_predict_endpoint.py
  ├── test_batch_endpoint.py
  └── test_idempotency.py
```

**Checklist:**
- [ ] `test_predict_endpoint.py` (5 cenários)
  - [ ] Fed +25 bps → resposta válida
  - [ ] Fed 0 bps → resposta válida
  - [ ] Fed -25 bps → resposta válida
  - [ ] Fed +50 bps → resposta válida
  - [ ] Horizonte [1, 3, 6] → 3 previsões
  
- [ ] `test_batch_endpoint.py` (2 cenários)
  - [ ] 3 cenários simultâneos
  - [ ] Todos com model_version consistente
  
- [ ] `test_idempotency.py` (3 testes)
  - [ ] Mesma requisição → mesma resposta (seed fixo)
  - [ ] model_version fixo → mesma previsão

**Código Exemplo:**
```python
@pytest.mark.asyncio
async def test_predict_fed_plus_25(client):
    response = await client.post(
        "/predict/selic-from-fed",
        json={
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "model_version": "v1.0.0"
        },
        headers={"X-API-Key": "sk_test_bronze_123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["expected_move_bps"] > 0
    assert len(data["per_meeting"]) > 0
    assert data["model_metadata"]["version"] == "v1.0.0"
    assert all(d["delta_bps"] % 25 == 0 for d in data["distribution"])
```

---

#### 3.3 Testes de Carga (1 dia)

**Ferramenta:** Locust

**Arquivo:** `tests/load/locustfile.py`

**Checklist:**
- [ ] Instalar locust: `pip install locust`
- [ ] Criar `locustfile.py` com cenários
- [ ] Executar teste: 50 RPS por 5 minutos
- [ ] Coletar métricas: p50/p95/p99
- [ ] Validar p95 < 250ms

**Código Locust:**
```python
from locust import HttpUser, task, between

class SelicUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def predict(self):
        self.client.post(
            "/predict/selic-from-fed",
            json={
                "fed_decision_date": "2025-10-29",
                "fed_move_bps": 25
            },
            headers={"X-API-Key": "sk_test_bronze_123"}
        )

# Executar
# $ locust -f tests/load/locustfile.py --host=https://localhost:8443
```

**Critério de Aceitação:**
```
Teste: 50 RPS por 5 minutos (15,000 requests)

Resultados:
  Total requests: 15,000
  Failures: 0 (0%)
  p50: 85ms
  p95: 210ms  ✅ < 250ms
  p99: 380ms
```

---

#### 3.4 UAT Manual (1 dia)

**Documento:** `docs/UAT_BRONZE.md`

**Casos de UAT:**

| ID | Cenário | Fed Move | Esperado | Status |
|----|---------|----------|----------|--------|
| UAT-01 | Hawkish moderado | +25 bps | Selic +25 bps, prob > 50% | ⬜ |
| UAT-02 | Neutro | 0 bps | Selic 0 bps, prob > 60% | ⬜ |
| UAT-03 | Dovish moderado | -25 bps | Selic -25 bps ou 0, dist ampla | ⬜ |
| UAT-04 | Hawkish forte | +50 bps | Selic +25/+50, ci95 largo | ⬜ |
| UAT-05 | Hawkish c/ surpresa | +25 + 10 surpresa | Selic +25, prob ajustada | ⬜ |

**Checklist:**
- [ ] Executar todos os 5 casos
- [ ] Documentar resultados em tabela
- [ ] Validar rationale faz sentido
- [ ] Validar per_meeting tem Copom correto
- [ ] Assinar UAT (aprovação)

**Template de Resultado:**
```markdown
### UAT-01: Hawkish Moderado

**Input:**
- fed_decision_date: 2025-10-29
- fed_move_bps: 25

**Output:**
- expected_move_bps: 25 ✅
- prob_move_within_next_copom: 0.58 ✅ (> 50%)
- per_meeting[0].copom_date: 2025-11-05 ✅
- rationale: "Resposta estimada positiva ao choque..." ✅

**Status: APROVADO ✅**
```

---

### ✅ Entregável Sprint 3

- [x] Testes unitários com cobertura ≥ 80%
- [x] Testes de integração end-to-end
- [x] Teste de carga validando p95 < 250ms
- [x] UAT completo com 5 casos aprovados
- [x] Documentação de testes

**Certificação Bronze:**
```markdown
# 🏆 Certificação Bronze - API FED-Selic

**Data:** 21/10/2025
**Versão:** v1.0.0

## Critérios Atendidos

✅ Foundation e Dados (5/5)
✅ Modelagem e Treino (4/5)
✅ Validação Científica (suites executadas)
✅ API e Contratos (5/5)
✅ Observabilidade e SRE (5/5)
✅ MLOps e Governança (pipeline reproduzível)
✅ Segurança (TLS + chave API)
✅ Performance (p95 < 250ms)
✅ Testes (cobertura 88%)
✅ UAT (5/5 casos aprovados)

**Status: BRONZE CERTIFICADO** 🥉

Aprovado para pilotos internos controlados.
```

---

## 📊 Tracking de Progresso

### Semana 1 (Sprint 1)

| Tarefa | Esforço | Status | Owner |
|--------|---------|--------|-------|
| Pipeline de treino | 2d | ⬜ | - |
| Carregar modelos na API | 1d | ⬜ | - |
| Remover mocks | 1d | ⬜ | - |
| Discretização + Copom | 1d | ⬜ | - |

### Semana 2 (Sprint 2)

| Tarefa | Esforço | Status | Owner |
|--------|---------|--------|-------|
| Prometheus | 1d | ⬜ | - |
| Logging estruturado | 1d | ⬜ | - |
| Chaves API | 1d | ⬜ | - |
| TLS + Rate limit | 1d | ⬜ | - |
| Rotação de logs | 1d | ⬜ | - |

### Semana 3 (Sprint 3)

| Tarefa | Esforço | Status | Owner |
|--------|---------|--------|-------|
| Testes unitários | 2d | ⬜ | - |
| Testes de integração | 1d | ⬜ | - |
| Testes de carga | 1d | ⬜ | - |
| UAT | 1d | ⬜ | - |

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Dados insuficientes (~20 obs) | Alta | Alto | Bandas largas, comunicar incerteza explicitamente |
| Performance abaixo de p95 < 250ms | Média | Alto | Cache de modelos, otimizar discretização |
| Cobertura de testes < 80% | Baixa | Médio | Priorizar testes de lógica crítica |
| UAT falhar em casos | Média | Alto | Ajustar thresholds, documentar limitações |

---

## 📞 Suporte e Contatos

**Dúvidas Técnicas:**
- Modelagem: Ver `src/models/` e READMEs científicos
- API: Ver `src/api/` e `API_README.md`
- Validações: Ver `tests_scientific/` e relatórios

**Execução:**
```bash
# Sprint 1
$ python scripts/train_pipeline.py --version v1.0.0
$ python start_api.py

# Sprint 2
$ curl http://localhost:8000/metrics
$ tail -f logs/api.log

# Sprint 3
$ pytest tests/unit/ --cov=src
$ locust -f tests/load/locustfile.py
```

---

**Próxima Revisão:** Após cada sprint (sexta-feira de cada semana)  
**Documento Vivo:** Atualizar status semanalmente
