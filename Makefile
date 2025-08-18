# Makefile para Win32 API Scraper
# Facilita execução de comandos comuns de desenvolvimento

.PHONY: help install install-dev test test-unit test-integration test-cli coverage lint format security clean docs

# Cores para output
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(GREEN)Win32 API Scraper - Comandos Disponíveis$(NC)"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependências de produção
	@echo "$(GREEN)📦 Instalando dependências de produção...$(NC)"
	pip install -r requirements.txt

install-dev: ## Instala dependências de desenvolvimento
	@echo "$(GREEN)🔧 Instalando dependências de desenvolvimento...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✅ Ambiente de desenvolvimento configurado!$(NC)"

test: ## Executa todos os testes
	@echo "$(GREEN)🧪 Executando todos os testes...$(NC)"
	python -m pytest tests/ -v --tb=short

test-unit: ## Executa apenas testes unitários  
	@echo "$(GREEN)🔬 Executando testes unitários...$(NC)"
	python -m pytest tests/ -v -m "not integration"

test-integration: ## Executa testes de integração
	@echo "$(GREEN)🌐 Executando testes de integração...$(NC)"
	python -m pytest tests/ -v -m "integration"

test-cli: ## Testa interface CLI
	@echo "$(GREEN)💻 Testando interface CLI...$(NC)"
	python win32_scraper.py CreateProcessW --output json > /dev/null
	python win32_scraper.py MessageBox --output json > /dev/null
	@echo "$(GREEN)✅ CLI funcionando corretamente!$(NC)"

coverage: ## Gera relatório de cobertura
	@echo "$(GREEN)📊 Gerando relatório de cobertura...$(NC)"
	python -m pytest tests/ --cov=win32_scraper --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)📋 Relatório disponível em htmlcov/index.html$(NC)"

lint: ## Executa linting do código
	@echo "$(GREEN)🔍 Verificando qualidade do código...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Formata código com Black
	@echo "$(GREEN)🎨 Formatando código...$(NC)"
	black .
	@echo "$(GREEN)✅ Código formatado!$(NC)"

format-check: ## Verifica formatação sem modificar
	@echo "$(GREEN)🔍 Verificando formatação...$(NC)"
	black --check --diff .

security: ## Executa análise de segurança
	@echo "$(GREEN)🔒 Executando análise de segurança...$(NC)"
	bandit -r . -f json -o bandit-report.json || true
	safety check || true
	@echo "$(GREEN)📋 Relatórios gerados: bandit-report.json$(NC)"

type-check: ## Executa verificação de tipos
	@echo "$(GREEN)📝 Verificando tipos...$(NC)"
	mypy win32_scraper.py --ignore-missing-imports || true

benchmark: ## Executa benchmarks de performance
	@echo "$(GREEN)⚡ Executando benchmarks...$(NC)"
	python -c "import time; from win32_scraper import Win32APIScraper; s = Win32APIScraper(); start = time.time(); s._try_direct_url('CreateProcessW'); print(f'Direct URL: {(time.time()-start)*1000:.2f}ms')"

clean: ## Limpa arquivos temporários
	@echo "$(GREEN)🧹 Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.egg-info/
	rm -rf build/
	rm -rf dist/
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

docs: ## Gera documentação
	@echo "$(GREEN)📚 Gerando documentação...$(NC)"
	@echo "$(YELLOW)README.md está atualizado$(NC)"
	@echo "$(YELLOW)Para documentação da API, use: python -c 'import win32_scraper; help(win32_scraper)'$(NC)"

run-example: ## Executa exemplo com CreateProcessW
	@echo "$(GREEN)🚀 Executando exemplo...$(NC)"
	python win32_scraper.py CreateProcessW

run-all-examples: ## Executa exemplos com várias funções
	@echo "$(GREEN)🚀 Executando exemplos com várias funções...$(NC)"
	@echo "$(YELLOW)CreateProcessW:$(NC)"
	python win32_scraper.py CreateProcessW --output json | head -5
	@echo "\n$(YELLOW)MessageBox:$(NC)"
	python win32_scraper.py MessageBox --output json | head -5
	@echo "\n$(YELLOW)GetSystemInfo:$(NC)"
	python win32_scraper.py GetSystemInfo --output json | head -5

setup: install-dev ## Configuração completa do ambiente
	@echo "$(GREEN)🚀 Configuração completa do ambiente...$(NC)"
	@echo "$(GREEN)✅ Pronto para desenvolvimento!$(NC)"
	@echo "$(YELLOW)Comandos úteis:$(NC)"
	@echo "  make test          - Executa testes"
	@echo "  make coverage      - Gera cobertura" 
	@echo "  make lint          - Verifica código"
	@echo "  make run-example   - Testa funcionalidade"

validate: lint test coverage security ## Validação completa antes de commit
	@echo "$(GREEN)✅ Validação completa concluída!$(NC)"
	@echo "$(GREEN)🚀 Pronto para commit/deploy!$(NC)"

# Comando padrão
all: validate