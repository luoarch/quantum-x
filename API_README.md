# 🚀 API FED-Selic Prediction

API para previsão probabilística da Selic condicionada a movimentos do Fed.

## 📋 Visão Geral

Esta API fornece previsões probabilísticas de quando e quanto a Selic tende a se mover em resposta a movimentos do Federal Reserve, com intervalos de confiança e mapeamento para reuniões do Copom.

### 🎯 Características Principais

- **Previsão Probabilística**: Retorna distribuições de probabilidade em vez de pontos únicos
- **Discretização em 25 bps**: Respeita a granularidade padrão de política monetária
- **Mapeamento Copom**: Converte horizontes em reuniões específicas do Copom
- **Intervalos de Confiança**: CI 80% e 95% para quantificar incerteza
- **Múltiplos Cenários**: Suporte a previsões em lote
- **Versionamento**: Controle de versões de modelos e API
- **Observabilidade**: Health checks, métricas e logs detalhados

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar a API

```bash
python start_api.py
```

### 3. Testar a API

```bash
python test_api.py
```

### 4. Acessar Documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 Endpoints

### 🔮 Previsão

#### `POST /predict/selic-from-fed`

Prever movimento da Selic baseado em movimento do Fed.

**Request:**
```json
{
  "fed_decision_date": "2025-01-29",
  "fed_move_bps": 25,
  "fed_move_dir": 1,
  "fed_surprise_bps": 10,
  "horizons_months": [1, 3, 6, 12],
  "model_version": "v1.0.0",
  "regime_hint": "normal"
}
```

**Response:**
```json
{
  "expected_move_bps": 25,
  "horizon_months": "1-3",
  "prob_move_within_next_copom": 0.62,
  "ci80_bps": [0, 50],
  "ci95_bps": [-25, 75],
  "per_meeting": [
    {
      "copom_date": "2025-02-05",
      "delta_bps": 25,
      "probability": 0.41
    }
  ],
  "distribution": [
    {"delta_bps": -25, "probability": 0.07},
    {"delta_bps": 0, "probability": 0.18},
    {"delta_bps": 25, "probability": 0.52}
  ],
  "model_metadata": {
    "version": "v1.0.0",
    "trained_at": "2025-01-01T00:00:00Z",
    "data_hash": "sha256:...",
    "methodology": "LP primary, BVAR fallback"
  },
  "rationale": "Resposta estimada positiva ao choque de +25 bps do Fed..."
}
```

#### `POST /predict/selic-from-fed/batch`

Previsões em lote para múltiplos cenários.

**Request:**
```json
{
  "scenarios": [
    {
      "fed_decision_date": "2025-01-29",
      "fed_move_bps": 25,
      "fed_move_dir": 1
    },
    {
      "fed_decision_date": "2025-01-29",
      "fed_move_bps": 0,
      "fed_move_dir": 0
    }
  ]
}
```

### 🏥 Health Check

#### `GET /health/`

Health check básico da API.

#### `GET /health/detailed`

Health check detalhado incluindo dependências.

#### `GET /health/ready`

Verificação de prontidão para receber tráfego.

#### `GET /health/live`

Verificação de vivacidade da API.

### 🤖 Modelos

#### `GET /models/versions`

Listar versões de modelos disponíveis.

#### `GET /models/versions/{version}`

Obter detalhes de versão específica.

#### `GET /models/active`

Obter versão ativa do modelo.

#### `POST /models/versions/{version}/activate`

Ativar versão específica do modelo.

## 🔐 Autenticação

A API utiliza autenticação por chave API no header:

```bash
curl -H "X-API-Key: dev-key-123" \
     -H "Content-Type: application/json" \
     http://localhost:8000/predict/selic-from-fed
```

### Chaves de Desenvolvimento

- `dev-key-123` - Chave de desenvolvimento
- `test-key-456` - Chave de teste

## ✅ Validação

### Regras de Validação

- **fed_move_bps**: Deve ser múltiplo de 25
- **fed_decision_date**: Formato ISO-8601, máximo 1 ano no futuro
- **horizons_months**: Valores entre 1 e 12
- **fed_move_dir**: Valores -1, 0, 1 (consistente com bps)

### Códigos de Erro

- `400` - `invalid_request`: Campos ausentes/inválidos
- `401` - `authentication_failed`: Chave API inválida
- `422` - `validation_error`: Valores fora dos ranges permitidos
- `429` - `rate_limited`: Limite de requests excedido
- `500` - `internal_error`: Erro interno do servidor
- `503` - `model_unavailable`: Modelo não disponível

## 📊 Exemplos de Uso

### Cenário 1: Fed +25 bps

```bash
curl -X POST "http://localhost:8000/predict/selic-from-fed" \
     -H "X-API-Key: dev-key-123" \
     -H "Content-Type: application/json" \
     -d '{
       "fed_decision_date": "2025-01-29",
       "fed_move_bps": 25,
       "fed_move_dir": 1,
       "regime_hint": "normal"
     }'
```

### Cenário 2: Fed 0 bps (Manutenção)

```bash
curl -X POST "http://localhost:8000/predict/selic-from-fed" \
     -H "X-API-Key: dev-key-123" \
     -H "Content-Type: application/json" \
     -d '{
       "fed_decision_date": "2025-01-29",
       "fed_move_bps": 0,
       "fed_move_dir": 0,
       "regime_hint": "normal"
     }'
```

### Cenário 3: Fed -25 bps (Corte)

```bash
curl -X POST "http://localhost:8000/predict/selic-from-fed" \
     -H "X-API-Key: dev-key-123" \
     -H "Content-Type: application/json" \
     -d '{
       "fed_decision_date": "2025-01-29",
       "fed_move_bps": -25,
       "fed_move_dir": -1,
       "regime_hint": "recovery"
     }'
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# API
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Autenticação
API_KEYS=dev-key-123,test-key-456

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Dados
DATA_DIR=data
FED_SELIC_DATA_PATH=raw/fed_selic_combined.csv

# Logging
LOG_LEVEL=INFO
```

### Configuração via Arquivo

Crie um arquivo `.env` na raiz do projeto:

```env
HOST=0.0.0.0
PORT=8000
DEBUG=false
API_KEYS=dev-key-123,test-key-456
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
DATA_DIR=data
LOG_LEVEL=INFO
```

## 📈 Monitoramento

### Health Checks

- **Básico**: `/health/` - Status geral da API
- **Detalhado**: `/health/detailed` - Inclui dependências e métricas
- **Readiness**: `/health/ready` - Prontidão para tráfego
- **Liveness**: `/health/live` - Vivacidade da API

### Métricas

- **Latência**: P50, P95, P99
- **Throughput**: Requests por minuto
- **Erro**: Taxa de erro por código
- **Sistema**: CPU, memória, disco

### Logs

- **Request/Response**: Logs de todas as requisições
- **Erros**: Logs detalhados de erros
- **Performance**: Métricas de latência
- **Auditoria**: Rastreamento de decisões

## 🧪 Testes

### Teste Automatizado

```bash
python test_api.py
```

### Teste Manual

1. **Swagger UI**: http://localhost:8000/docs
2. **Cenários de Exemplo**: `/predict/scenarios`
3. **Regras de Validação**: `/predict/validation-rules`

### Cenários de Teste

- ✅ Fed +25 bps (aumento padrão)
- ✅ Fed +50 bps (aumento agressivo)
- ✅ Fed 0 bps (manutenção)
- ✅ Fed -25 bps (corte)
- ❌ BPS inválido (não múltiplo de 25)
- ❌ Data futura inválida (> 1 ano)
- ❌ Sem autenticação

## 🚀 Deploy

### Desenvolvimento

```bash
python start_api.py
```

### Produção

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "start_api.py"]
```

## 📚 Documentação Adicional

- **Especificação Completa**: `REQUISITOS.md`
- **Checklist de Aceitação**: `REQUISITOS.md` (seção final)
- **Arquitetura**: `src/` (código fonte)
- **Exemplos**: `examples/` (scripts de exemplo)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

- **Issues**: GitHub Issues
- **Documentação**: `/docs` (Swagger UI)
- **Health Check**: `/health` (status da API)
- **Logs**: Console/arquivo de log

---

**Desenvolvido com ❤️ para análise de spillovers FED-Selic**
