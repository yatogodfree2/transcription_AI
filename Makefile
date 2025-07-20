.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies with Poetry"
	@echo "  make dev        - Run development server"
	@echo "  make test       - Run tests with pytest"
	@echo "  make lint       - Run linters (flake8, mypy)"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove build artifacts and cache files"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up  - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"

# Install dependencies
install:
	poetry install

# Run development server
dev:
	poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	poetry run pytest -v

# Run linters
lint:
	poetry run flake8 backend
	poetry run mypy backend

# Format code
format:
	poetry run black backend
	poetry run isort backend

# Clean build artifacts and cache files
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
