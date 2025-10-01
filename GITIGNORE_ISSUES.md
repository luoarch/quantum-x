# 🚨 PROBLEMAS CRÍTICOS NO .GITIGNORE

**Data:** 2025-10-01  
**Severidade:** ALTA ⚠️  

---

## ❌ PROBLEMAS IDENTIFICADOS

### 1. **`*.json` É MUITO GENÉRICO** (Linha 134) 🚨

**Problema:**
```gitignore
*.json    # Ignora TODOS os arquivos JSON!
```

**Arquivos críticos sendo ignorados:**
```
✅ DEVEM SER VERSIONADOS:
  data/models/v1.0.0/metadata.json       (metadata do modelo)
  data/models/v1.0.1/metadata.json
  data/models/v1.0.2/metadata.json
  reports/size_power_test/*.json         (resultados científicos)
  reports/heteroskedasticity_test/*.json
  reports/structural_breaks_test/*.json
  reports/small_samples_test/*.json
  reports/lag_selection_test/*.json

❌ PODEM SER IGNORADOS:
  coverage.json                          (gerado por pytest)
  data/raw/*.json                        (dados brutos - opcional)
```

**Impacto:**
- ⚠️ Metadata de modelos NÃO está versionado
- ⚠️ Resultados de testes científicos NÃO estão versionados
- ⚠️ Auditoria e reprodutibilidade comprometidas

---

### 2. **`data/` É MUITO GENÉRICO** (Linha 135) 🚨

**Problema:**
```gitignore
data/    # Ignora TODO o diretório data/!
```

**Arquivos críticos sendo ignorados:**
```
✅ DEVEM SER VERSIONADOS:
  data/models/*/metadata.json            (metadata de modelos)
  data/raw/fed_selic_combined.csv        (dados históricos)
  data/processed/*.csv                   (dados processados)

❌ PODEM SER IGNORADOS:
  data/models/*/model_bvar.pkl           (modelo binário grande)
  data/models/*/model_lp.pkl
  data/raw/*.parquet                     (dados binários grandes)
```

**Impacto:**
- ⚠️ Dados históricos essenciais NÃO estão versionados
- ⚠️ Reprodutibilidade comprometida

---

### 3. **`*.csv` É MUITO GENÉRICO** (Linha 132) ⚠️

**Problema:**
```gitignore
*.csv    # Ignora TODOS os CSVs!
```

**Arquivos que DEVEM ser versionados:**
```
✅ Dados históricos pequenos:
  data/raw/fed_selic_combined.csv        (<1MB, essencial)
  data/processed/fed_clean_data.csv      (dados limpos)

❌ Podem ser ignorados:
  reports/*/*.csv                        (resultados - já temos JSON)
  data/temp/*.csv                        (temporários)
```

---

## ✅ SOLUÇÃO RECOMENDADA

### Novo .gitignore (Específico e Robusto)

```gitignore
# Coverage reports (gerados automaticamente)
.coverage
.coverage.*
htmlcov/
coverage.xml
coverage.json

# Pytest cache
.pytest_cache/
.cache

# Models (binários grandes)
data/models/**/*.pkl
data/models/**/*.h5
data/models/**/*.pth
data/models/**/*.joblib

# Mas VERSIONAR metadata de modelos!
!data/models/**/metadata.json
!data/models/**/model_card.md

# Data (arquivos grandes)
data/raw/**/*.parquet
data/raw/**/*.feather
data/processed/**/*.parquet

# Mas VERSIONAR dados históricos pequenos!
!data/raw/fed_selic_combined.csv
!data/raw/fed_selic_combined.json
!data/processed/fed_clean_data.csv

# Reports (CSVs grandes)
reports/**/*.csv

# Mas VERSIONAR resultados científicos JSON!
!reports/**/lag_selection_results.json
!reports/**/lag_distributions.json
!reports/**/hetero_size_results.json
!reports/**/breaks_results.json
!reports/**/small_size_results.json
!reports/**/small_power_results.json
!reports/**/size_results.json
!reports/**/power_results.json
!reports/**/benchmarks_results.json

# Logs
logs/
*.log

# Temporary files
*.tmp
*.temp
temp/
tmp/
```

---

## 🎯 PRINCÍPIOS DO NOVO .GITIGNORE

1. **Ignorar por padrão, versionar explicitamente:**
   - Ignorar diretórios grandes (`data/`, `models/`)
   - Usar `!pattern` para versionar arquivos específicos

2. **Versionar metadados e configuração:**
   - `metadata.json` de modelos
   - `model_card.md`
   - Resultados de testes científicos (JSON)

3. **Ignorar binários grandes:**
   - `*.pkl`, `*.h5`, `*.pth`
   - `*.parquet`, `*.feather`

4. **Versionar dados históricos pequenos:**
   - `fed_selic_combined.csv` (<1MB)
   - Dados essenciais para reprodução

---

## 📋 CHECKLIST DE AÇÃO

- [ ] 1. Backup do .gitignore atual
- [ ] 2. Aplicar novo .gitignore
- [ ] 3. Verificar arquivos não rastreados (`git status --ignored`)
- [ ] 4. Adicionar arquivos críticos:
  - [ ] `git add -f data/models/*/metadata.json`
  - [ ] `git add -f reports/*/*.json`
  - [ ] `git add -f data/raw/fed_selic_combined.csv`
- [ ] 5. Commit: "fix: .gitignore - versionar metadata e resultados científicos"
- [ ] 6. Documentar no README

---

## ⚠️ RISCO ATUAL

**Sem os arquivos versionados:**
- ❌ Modelos NÃO são auditáveis (sem metadata)
- ❌ Testes científicos NÃO são reproduzíveis (sem resultados)
- ❌ Dados históricos podem ser perdidos
- ❌ Não atende requisitos de Bronze (auditabilidade)

**Impacto na certificação:**
- 🟡 Bronze: Auditabilidade parcial (94% → 90%)
- 🔴 Prata: Não atende requisitos de reprodutibilidade
- 🔴 Ouro: Não atende requisitos de governança

---

## 🚀 RECOMENDAÇÃO

**AÇÃO IMEDIATA:** Aplicar novo .gitignore e versionar arquivos críticos!

**Tempo estimado:** 10 minutos  
**Prioridade:** ALTA ⚠️  

