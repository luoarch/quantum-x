# Makefile para Global Economic Regime Analysis & Brazil Spillover Prediction System
# Conforme especificação do DRS

.PHONY: help install dev test lint format clean docker-up docker-down

# Variáveis
PYTHON := python3.11
PIP := pip
NPM := npm
DOCKER_COMPOSE := docker-compose

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Mostrar esta ajuda
	@echo "$(BLUE)Global Economic Regime Analysis & Brazil Spillover Prediction System$(NC)"
	@echo "$(BLUE)================================================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponíveis:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Instalar dependências
	@echo "$(BLUE)Instalando dependências Python...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(BLUE)Instalando dependências Node.js...$(NC)"
	cd dashboard && $(NPM) install
	@echo "$(GREEN)✓ Dependências instaladas com sucesso!$(NC)"

dev: ## Executar em modo desenvolvimento
	@echo "$(BLUE)Iniciando modo desenvolvimento...$(NC)"
	$(DOCKER_COMPOSE) up -d postgres redis
	@echo "$(YELLOW)Aguardando bancos de dados...$(NC)"
	sleep 10
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Executar frontend em modo desenvolvimento
	@echo "$(BLUE)Iniciando frontend...$(NC)"
	cd dashboard && $(NPM) run dev

test: ## Executar testes
	@echo "$(BLUE)Executando testes Python...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(BLUE)Executando testes Node.js...$(NC)"
	cd dashboard && $(NPM) test

test-backend: ## Executar apenas testes do backend
	@echo "$(BLUE)Executando testes do backend...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

test-frontend: ## Executar apenas testes do frontend
	@echo "$(BLUE)Executando testes do frontend...$(NC)"
	cd dashboard && $(NPM) test

lint: ## Executar linting
	@echo "$(BLUE)Executando linting Python...$(NC)"
	black --check app/
	isort --check-only app/
	mypy app/
	@echo "$(BLUE)Executando linting Node.js...$(NC)"
	cd dashboard && $(NPM) run lint

format: ## Formatar código
	@echo "$(BLUE)Formatando código Python...$(NC)"
	black app/
	isort app/
	@echo "$(BLUE)Formatando código Node.js...$(NC)"
	cd dashboard && $(NPM) run format

clean: ## Limpar arquivos temporários
	@echo "$(BLUE)Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	cd dashboard && rm -rf .next/ node_modules/.cache/
	@echo "$(GREEN)✓ Limpeza concluída!$(NC)"

docker-up: ## Subir containers Docker
	@echo "$(BLUE)Subindo containers Docker...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Containers iniciados!$(NC)"

docker-down: ## Parar containers Docker
	@echo "$(BLUE)Parando containers Docker...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Containers parados!$(NC)"

docker-build: ## Build das imagens Docker
	@echo "$(BLUE)Construindo imagens Docker...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Imagens construídas!$(NC)"

db-migrate: ## Executar migrações do banco
	@echo "$(BLUE)Executando migrações...$(NC)"
	alembic upgrade head
	@echo "$(GREEN)✓ Migrações executadas!$(NC)"

db-reset: ## Resetar banco de dados
	@echo "$(RED)ATENÇÃO: Isso irá apagar todos os dados!$(NC)"
	@read -p "Tem certeza? (y/N): " confirm && [ "$$confirm" = "y" ]
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d postgres
	sleep 10
	$(MAKE) db-migrate

logs: ## Mostrar logs dos containers
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Mostrar logs da API
	$(DOCKER_COMPOSE) logs -f api

logs-frontend: ## Mostrar logs do frontend
	$(DOCKER_COMPOSE) logs -f frontend

status: ## Mostrar status dos containers
	$(DOCKER_COMPOSE) ps

shell: ## Abrir shell no container da API
	$(DOCKER_COMPOSE) exec api /bin/bash

shell-db: ## Abrir shell no banco de dados
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d global_regime_analysis

# Comando padrão
.DEFAULT_GOAL := help
