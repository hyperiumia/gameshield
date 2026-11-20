.DEFAULT_GOAL := help

.PHONY: help bootstrap up down logs test

help: ## Show available targets
@grep -E '^[a-zA-Z_-]+:.?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.?## "}; {printf " %-12s %s\n", 
1
,
1,2}'

bootstrap: ## Install local toolchains (Rust, uv, Node, Docker)
bash ops/scripts/bootstrap.sh

up: ## Start local infra (Postgres + Redis)
docker compose up -d

down: ## Stop local infra
docker compose down

logs: ## Tail infra logs
docker compose logs -f

test: ## Run all test suites
cd services/ingest && cargo test
cd services/engine && uv run pytest -q
