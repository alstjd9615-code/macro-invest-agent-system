# =============================================================================
# macro-invest-agent-platform — developer Makefile
# =============================================================================
# Prerequisites: Python 3.12, uv
#
# Usage:
#   make install      Install all project dependencies (including dev extras)
#   make format       Auto-format code with ruff
#   make lint         Lint code with ruff (no auto-fix)
#   make typecheck    Run mypy static type checker
#   make test         Run the full test suite
#   make test-unit    Run only unit tests (tests/core, tests/domain)
#   make test-contract Run only MCP contract/schema tests (tests/mcp)
#   make up           Start local infrastructure (docker compose up -d)
#   make down         Stop local infrastructure (docker compose down)
#   make logs         Tail docker compose logs
# =============================================================================

.PHONY: help install format lint typecheck test test-unit test-contract up down logs

# Show this help message.
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' \
		| sort

install: ## Install all dependencies (dev included)
	uv sync --all-extras

format: ## Auto-format source with ruff
	uv run ruff format .
	uv run ruff check --fix .

lint: ## Lint source with ruff (no auto-fix)
	uv run ruff check .
	uv run ruff format --check .

typecheck: ## Run mypy static analysis
	uv run mypy .

test: ## Run the full test suite with coverage
	uv run pytest --cov=. --cov-report=term-missing

test-unit: ## Run unit tests for core and domain layers
	uv run pytest tests/core/ tests/domain/ -v

test-contract: ## Run MCP contract and schema tests
	uv run pytest tests/mcp/ -v

up: ## Start local infrastructure (postgres + minio)
	docker compose up -d

down: ## Stop local infrastructure
	docker compose down

logs: ## Tail docker compose logs (Ctrl-C to stop)
	docker compose logs -f
