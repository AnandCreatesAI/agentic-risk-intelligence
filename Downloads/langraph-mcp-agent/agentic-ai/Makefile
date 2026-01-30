# Makefile
# Common commands for Agentic Risk Intelligence Platform

.PHONY: help install dev test lint format docker-build docker-run docker-stop clean

# Default target
help:
	@echo "Agentic Risk Intelligence Platform"
	@echo "==================================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  dev          Install development dependencies"
	@echo "  venv         Create virtual environment"
	@echo ""
	@echo "Run:"
	@echo "  run          Run the main assessment"
	@echo "  mcp-server   Start the MCP server"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run in Docker container"
	@echo "  docker-stop  Stop Docker containers"
	@echo "  docker-logs  View container logs"
	@echo "  compose-up   Start with docker-compose"
	@echo "  compose-down Stop docker-compose"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  lint         Run linters"
	@echo "  format       Format code"
	@echo "  typecheck    Run type checker"
	@echo "  clean        Remove build artifacts"
	@echo ""

# ============================================================================
# Setup
# ============================================================================

venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install:
	pip install --upgrade pip
	pip install -e .

dev:
	pip install --upgrade pip
	pip install -e ".[all]"
	pre-commit install

# ============================================================================
# Run
# ============================================================================

run:
	python main.py

mcp-server:
	python mcp/real_mcp_server.py

# ============================================================================
# Docker
# ============================================================================

DOCKER_IMAGE = agentic-risk-intelligence
DOCKER_TAG = latest

docker-build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run:
	docker run --rm -it \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		-e LANGCHAIN_API_KEY=$(LANGCHAIN_API_KEY) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-stop:
	docker stop $$(docker ps -q --filter ancestor=$(DOCKER_IMAGE)) 2>/dev/null || true

docker-logs:
	docker logs -f $$(docker ps -q --filter ancestor=$(DOCKER_IMAGE))

docker-shell:
	docker run --rm -it $(DOCKER_IMAGE):$(DOCKER_TAG) /bin/bash

# Docker Compose
compose-up:
	docker-compose up -d

compose-down:
	docker-compose down

compose-logs:
	docker-compose logs -f

compose-ps:
	docker-compose ps

# Full stack with all services
compose-full:
	docker-compose --profile api --profile cache --profile database up -d

# ============================================================================
# Development
# ============================================================================

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

lint:
	ruff check .
	mypy .

format:
	black .
	ruff check --fix .

typecheck:
	mypy . --ignore-missing-imports

# ============================================================================
# Clean
# ============================================================================

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-docker:
	docker-compose down -v --rmi local
	docker system prune -f

# ============================================================================
# Release
# ============================================================================

build:
	python -m build

publish-test:
	python -m twine upload --repository testpypi dist/*

publish:
	python -m twine upload dist/*
