.PHONY: help install test lint format build clean dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies and setup development environment
	./scripts/setup

test: ## Run tests with coverage
	./scripts/test

lint: ## Run all linting checks
	./scripts/lint

format: ## Format code with ruff
	ruff format custom_components/ tests/

build: ## Build the package
	./scripts/build

clean: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info/ htmlcov/ .coverage coverage.xml

dev: ## Start development environment
	./scripts/develop

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

update-deps: ## Update dependencies
	pip install --upgrade -r requirements.txt
	pre-commit autoupdate
