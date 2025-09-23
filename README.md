# Quantum X - CLI Trading Signal Generator

Sistema de geração de sinais de trading baseado em indicadores de ciclo de negócios (CLI), combinando metodologia científica da OECD com machine learning para otimização de pesos.

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.9+
- PostgreSQL 13+
- Redis (opcional)

### Instalação

1. **Clone o repositório**
```bash
git clone <repository-url>
cd quantum-x
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**
```bash
cp env.example .env
# Edite o arquivo .env com suas configurações
```

4. **Configure o banco de dados**
```bash
# Crie o banco PostgreSQL
createdb quantum_x_db

# As tabelas serão criadas automaticamente na primeira execução
```

5. **Execute a aplicação**
```bash
python run.py
```

A API estará disponível em: `http://localhost:8000`

## 📊 Funcionalidades Implementadas

### ✅ Semana 1-2: Setup e Data Pipeline

- [x] Configuração FastAPI + PostgreSQL
- [x] Coletores de dados (BCB, OECD, IPEA)
- [x] Schema de database para séries temporais
- [x] Testes básicos de coleta de dados

### 🔄 Em Desenvolvimento

- [ ] Core CLI Engine (Semana 3-4)
- [ ] Signal Generation (Semana 5-6)
- [ ] Frontend Dashboard (Semana 7-8)
- [ ] Testing e Deployment (Semana 9-10)

## 🛠️ API Endpoints

### Dados Econômicos

- `POST /api/v1/data/collect` - Inicia coleta de dados
- `GET /api/v1/data/series` - Lista séries disponíveis
- `GET /api/v1/data/series/{series_code}` - Dados de série específica
- `GET /api/v1/data/collection-log` - Log de coletas
- `GET /api/v1/data/stats` - Estatísticas dos dados

### Sinais de Trading

- `GET /api/v1/signals/` - Lista sinais (em desenvolvimento)
- `GET /api/v1/signals/health` - Health check

## 📈 Fontes de Dados

### Banco Central do Brasil (BCB)
- IPCA (433)
- Taxa Selic (432)
- PIB (4380)
- Câmbio USD/BRL (1)
- Produção Industrial (21859)

### OECD
- CLI Brasil, EUA, China, Global

### IPEA
- Dados econômicos brasileiros

## 🏗️ Arquitetura

```
app/
├── core/           # Configurações e utilitários
├── models/         # Modelos do banco de dados
├── services/       # Lógica de negócio
├── api/           # Endpoints da API
├── schemas/       # Schemas Pydantic
└── main.py        # Aplicação principal
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/quantum_x_db
REDIS_URL=redis://localhost:6379/0

# APIs (opcional)
BCB_API_KEY=
OECD_API_KEY=

# Aplicação
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

## 📝 Próximos Passos

1. **Testar coleta de dados** - Execute a coleta e verifique os dados
2. **Implementar CLI Engine** - Processamento de fatores dinâmicos
3. **Desenvolver sinais** - Sistema de geração de sinais
4. **Criar dashboard** - Interface web para visualização

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.