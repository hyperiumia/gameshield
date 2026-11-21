.DEFAULT_GOAL := help

.PHONY: help bootstrap up down logs test e2e dev-engine dev-web

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

bootstrap: ## Install local toolchains (Rust, uv, Node, Docker)
	bash ops/scripts/bootstrap.sh

up: ## Start local infra (Postgres + Redis)
	docker compose up -d

down: ## Stop local infra
	docker compose down

logs: ## Tail infra logs
	docker compose logs -f

test: ## Run all test suites (lua, rust, python)
	cd edge/gameshield && lua5.4 src/sha2_test.lua
	cd services/ingest && cargo test
	cd services/engine && uv run pytest -q

e2e: ## End-to-end: signed batch -> ingest -> postgres
	bash ops/scripts/e2e.sh

dev-engine: ## Run engine locally (uvicorn)
	cd services/engine && uv run uvicorn app.main:app --reload

dev-web: ## Run dashboard locally (vite)
	cd apps/web && npm run dev

dev-engine: ## Run engine locally (uvicorn)
	cd services/engine && uv run uvicorn app.main:app --reload

dev-web: ## Run dashboard locally (vite)
	cd apps/web && npm run dev
