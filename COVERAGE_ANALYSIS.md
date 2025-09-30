# 📊 Análise de Cobertura de Testes

**Data:** 30 de Setembro de 2025  
**Sprint:** 2 - Dia 1  
**Cobertura Atual:** 55% (2,585 stmts, 1,172 miss)  
**Target:** 80% para Bronze 100%

---

## 🎯 Status Atual

```
COBERTURA GERAL: 55% ████████████████░░░░░░░░░░░░░░░  (Target: 80%)

Gap para Bronze: -25 pontos percentuais
```

---

## 📊 Cobertura por Módulo

### ✅ **ALTA COBERTURA (≥80%)**

| Arquivo | Cobertura | Stmts | Miss | Status |
|---------|-----------|-------|------|--------|
| `src/api/schemas.py` | **98%** | 177 | 4 | ✅ Excelente |
| `src/core/config.py` | **96%** | 51 | 2 | ✅ Excelente |
| `src/api/endpoints/prediction.py` | **82%** | 82 | 15 | ✅ Bom |
| `src/api/main.py` | **80%** | 117 | 23 | ✅ No target |
| `src/api/endpoints/__init__.py` | **100%** | 2 | 0 | ✅ Perfeito |

**Subtotal:** 429 stmts, 44 miss → **90% médio**

---

### 🟡 **COBERTURA MÉDIA (50-79%)**

| Arquivo | Cobertura | Stmts | Miss | Gap | Prioridade |
|---------|-----------|-------|------|-----|------------|
| `src/api/endpoints/health.py` | **76%** | 91 | 22 | -4% | 🟡 Média |
| `src/api/endpoints/models.py` | **73%** | 111 | 30 | -7% | 🟡 Média |
| `src/api/middleware.py` | **71%** | 130 | 38 | -9% | 🟡 Média |
| `src/services/prediction_service.py` | **68%** | 263 | 84 | -12% | 🟢 Alta |
| `src/services/health_service.py` | **65%** | 159 | 56 | -15% | 🟡 Média |
| `src/services/model_service.py` | **57%** | 258 | 111 | -23% | 🔴 Alta |
| `src/types/selic_types.py` | **52%** | 178 | 86 | -28% | 🟡 Baixa |
| `src/types/interest_rates.py` | **49%** | 152 | 77 | -31% | 🟡 Baixa |
| `src/services/data_service.py` | **48%** | 85 | 44 | -32% | 🟡 Média |

**Subtotal:** 1,427 stmts, 548 miss → **62% médio**

---

### 🔴 **BAIXA COBERTURA (<50%)**

| Arquivo | Cobertura | Stmts | Miss | Gap | Prioridade |
|---------|-----------|-------|------|-----|------------|
| `src/models/local_projections.py` | **24%** | 199 | 152 | -56% | 🔴 CRÍTICA |
| `src/services/selic_service.py` | **21%** | 129 | 102 | -59% | 🟡 Média |
| `src/models/bvar_minnesota.py` | **19%** | 275 | 222 | -61% | 🔴 CRÍTICA |
| `src/services/interest_rate_service.py` | **17%** | 126 | 104 | -63% | 🟡 Média |

**Subtotal:** 729 stmts, 580 miss → **20% médio** 🔴

---

## 🎯 Plano de Ação para 80%

### **Estratégia: Foco nos Maiores Impactos**

#### **Fase 1: Services (80% → 65%)**
**Impact:** +15 pontos, 3-4 horas

1. **ModelService** (57% → 85%)
   - [ ] Testar `load_model()` com diferentes versões
   - [ ] Testar `activate_model()` e `list_versions()`
   - [ ] Testar cache LRU (eviction, max size)
   - [ ] Testar self-checks (estabilidade, dimensões)
   - **Ganho:** ~100 linhas cobertas → +4%

2. **PredictionService** (68% → 85%)
   - [ ] Testar `predict()` com diferentes regimes
   - [ ] Testar `_discretize_from_model_output()`
   - [ ] Testar `_map_to_copom_meetings()`
   - [ ] Testar `_build_real_metadata()`
   - **Ganho:** ~50 linhas cobertas → +2%

3. **DataService** (48% → 75%)
   - [ ] Testar `validate_data_quality()`
   - [ ] Testar error handling
   - **Ganho:** ~30 linhas cobertas → +1%

**Total Fase 1:** ~180 linhas → **+7% cobertura geral**

---

#### **Fase 2: Models (Core Logic) (65% → 75%)**
**Impact:** +10 pontos, 2-3 horas

4. **BVAR Minnesota** (19% → 50%)
   - [ ] Testar `prepare_data()` e `estimate()`
   - [ ] Testar `conditional_forecast()`
   - [ ] Testar IRFs estruturais
   - [ ] Testar `to_dict()` / `from_dict()`
   - **Ganho:** ~85 linhas cobertas → +3%

5. **Local Projections** (24% → 50%)
   - [ ] Testar `fit()` e `forecast()`
   - [ ] Testar bootstrap CI
   - [ ] Testar serialização
   - **Ganho:** ~50 linhas cobertas → +2%

**Total Fase 2:** ~135 linhas → **+5% cobertura geral**

---

#### **Fase 3: Endpoints e Middlewares (75% → 80%)**
**Impact:** +5 pontos, 1-2 horas

6. **Middlewares** (71% → 85%)
   - [ ] Testar rate limiting (429)
   - [ ] Testar error handling (500)
   - [ ] Testar security headers
   - **Ganho:** ~20 linhas → +1%

7. **Endpoints /models e /health** (73-76% → 85%)
   - [ ] Testar branches de erro não cobertas
   - [ ] Testar activate com self-check failure (409)
   - **Ganho:** ~25 linhas → +1%

**Total Fase 3:** ~45 linhas → **+2% cobertura geral**

---

## 📈 Projeção de Cobertura

| Fase | Cobertura | Ganho | Tempo | Prioridade |
|------|-----------|-------|-------|------------|
| **Atual** | 55% | - | - | - |
| **Fase 1** | 62% | +7% | 3-4h | 🔴 Crítica |
| **Fase 2** | 67% | +5% | 2-3h | 🟡 Alta |
| **Fase 3** | 69% | +2% | 1-2h | 🟡 Média |
| **Otimização** | 75% | +6% | 2-3h | 🟡 Média |
| **Polimento** | 80% | +5% | 2-3h | 🟢 Baixa |

**Total Estimado:** 10-15 horas para 80%

---

## 🎯 Estratégia Otimizada

### **Caminho Rápido para 80% (6-8 horas)**

1. **Services (Prioridade Máxima)**
   - `ModelService`: 30 testes → 85% (+4%)
   - `PredictionService`: 20 testes → 85% (+2%)
   - `DataService`: 15 testes → 75% (+1%)
   - **Total:** 65 testes → **+7%**

2. **Models (Core)**
   - `BVAR`: 15 testes básicos → 40% (+2.5%)
   - `LP`: 12 testes básicos → 40% (+2%)
   - **Total:** 27 testes → **+4.5%**

3. **Endpoints + Middlewares**
   - Error paths não cobertos: 15 testes
   - Rate limiting: 5 testes
   - **Total:** 20 testes → **+3%**

**Total Otimizado:** ~112 novos testes → **55% + 14.5% = 69.5%**

Para chegar a 80%, precisamos de mais 10.5%, focando em:
4. **Polimento de Services** (mais 40 testes) → **+10.5%**

**TOTAL PARA 80%:** ~150 novos testes

---

## 📋 Próximos Passos Imediatos

### **DIA 2: Services (Target: 65%)**

**Manhã (4 horas):**
1. ✅ Criar `tests/unit/test_model_service.py`
   - load_model(), activate(), cache LRU
   - **30 testes, +4% cobertura**

2. ✅ Criar `tests/unit/test_prediction_service.py`
   - predict(), discretize(), copom mapping
   - **25 testes, +2% cobertura**

**Tarde (3 horas):**
3. ✅ Criar `tests/unit/test_data_service.py`
   - validate_data_quality(), error handling
   - **15 testes, +1% cobertura**

**Meta Dia 2:** 55% → 62% (+7%)

---

### **DIA 3: Models Core (Target: 72%)**

**Manhã (3 horas):**
4. ✅ Criar `tests/unit/test_bvar.py`
   - prepare_data(), estimate(), conditional_forecast()
   - **20 testes, +3% cobertura**

**Tarde (2 horas):**
5. ✅ Criar `tests/unit/test_lp.py`
   - fit(), forecast(), bootstrap
   - **15 testes, +2.5% cobertura**

**Meta Dia 3:** 62% → 69.5% (+7.5%)

---

### **DIA 4-5: Polimento (Target: 80%)**

6. ✅ Error paths em endpoints
7. ✅ Middlewares (rate limit, errors)
8. ✅ Types (opcional, se necessário)

**Meta Dia 4-5:** 69.5% → 80% (+10.5%)

---

## 🔴 Gaps Críticos (Prioridade Máxima)

### **1. BVAR Minnesota (19% → 50%)**
**Missing Lines:** 222/275

**Funções Não Cobertas:**
- `prepare_data()` (linhas 64-100)
- `estimate()` (linhas 108-159)
- `conditional_forecast()` (linhas 228-300)
- `_compute_structural_irfs()` (linhas 334-379)
- `to_dict()` / `from_dict()` (linhas 630-692)

**Plano:**
```python
# tests/unit/test_bvar.py
def test_bvar_prepare_data()
def test_bvar_estimate()
def test_bvar_stability_check()
def test_bvar_conditional_forecast()
def test_bvar_irfs()
def test_bvar_serialization()
```

---

### **2. Local Projections (24% → 50%)**
**Missing Lines:** 152/199

**Funções Não Cobertas:**
- `fit()` (linhas 90-114)
- `forecast()` (linhas 182-235)
- `_bootstrap_confidence_intervals()` (linhas 263-290)

**Plano:**
```python
# tests/unit/test_lp.py
def test_lp_fit()
def test_lp_forecast()
def test_lp_bootstrap()
def test_lp_horizons()
```

---

### **3. ModelService (57% → 85%)**
**Missing Lines:** 111/258

**Funções Não Cobertas:**
- Error paths em `load_model()`
- Cache eviction
- Self-check failures

**Plano:**
```python
# tests/unit/test_model_service.py
def test_load_model_not_found()
def test_cache_eviction()
def test_self_check_failure()
```

---

## 📝 Recomendações

### **Rápido para 80%:**
1. ✅ Criar testes de `ModelService` (30 testes) → +4%
2. ✅ Criar testes de `PredictionService` (25 testes) → +2%
3. ✅ Testes básicos de BVAR (20 testes) → +3%
4. ✅ Testes básicos de LP (15 testes) → +2.5%
5. ✅ Error paths em endpoints (15 testes) → +1.5%
6. ✅ Middlewares completos (10 testes) → +1%
7. ✅ DataService (15 testes) → +1%

**Total:** ~130 novos testes → **80% cobertura**

### **Alternativa Pragmática:**
- Excluir `types/` da cobertura obrigatória (são data classes)
- Focar 80% em `src/api/` e `src/services/` e `src/models/`
- Ajustar pytest.ini para omit `src/types/*`

---

## 🚀 Next Steps

**Opção A: Caminho Completo (80% total)**
- 2-3 dias
- ~150 novos testes
- Cobertura abrangente

**Opção B: Caminho Pragmático (80% core)**
- 1-2 dias  
- ~80 novos testes
- Focar em src/api, src/services, src/models
- Excluir types/ da cobertura obrigatória

**Recomendação:** Opção B para atingir Bronze 100% mais rápido,  
depois refinar para Prata.

---

## 📊 Coverage HTML Report

Visualizar detalhes completos:
```bash
open htmlcov/index.html
```

Identificar linhas específicas não cobertas por arquivo.

