.PHONY: help install init run test clean docker-build docker-up docker-down logs

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python dependencies
	pip install -r requirements.txt

init:  ## Initialize database and default data
	python scripts/init_db.py

run:  ## Run the Flask application
	python run.py

test:  ## Run tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage
	pytest tests/ --cov=backend --cov-report=html --cov-report=term

lint:  ## Run linters
	flake8 backend/ --max-line-length=120
	black backend/ --check
	mypy backend/ --ignore-missing-imports

format:  ## Format code with black
	black backend/
	isort backend/

clean:  ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf htmlcov/ .coverage .pytest_cache/

docker-build:  ## Build Docker images
	docker-compose build

docker-up:  ## Start Docker containers
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@echo "Initializing database..."
	docker-compose exec web python scripts/init_db.py || true
	@echo "SOAR Platform is running at http://localhost:5000"

docker-down:  ## Stop Docker containers
	docker-compose down

docker-logs:  ## Show Docker logs
	docker-compose logs -f

docker-shell:  ## Open shell in web container
	docker-compose exec web /bin/bash

docker-clean:  ## Remove Docker containers and volumes
	docker-compose down -v
	docker system prune -f

db-migrate:  ## Create database migration
	flask db migrate -m "$(message)"

db-upgrade:  ## Apply database migrations
	flask db upgrade

db-downgrade:  ## Rollback last migration
	flask db downgrade

celery-worker:  ## Run Celery worker
	celery -A backend.celery_app.celery_app worker --loglevel=info

celery-beat:  ## Run Celery beat scheduler
	celery -A backend.celery_app.celery_app beat --loglevel=info

dev:  ## Run development server with auto-reload
	FLASK_ENV=development FLASK_DEBUG=1 python run.py

prod:  ## Run production server
	FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
