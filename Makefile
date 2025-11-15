.PHONY: help install dev-install docker-up docker-down init status start test clean

help:
	@echo "AgentKataster - Make commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install dependencies"
	@echo "  make dev-install    Install with dev dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      Start Docker services"
	@echo "  make docker-down    Stop Docker services"
	@echo "  make docker-logs    View Docker logs"
	@echo ""
	@echo "Application:"
	@echo "  make init           Initialize database"
	@echo "  make status         Show scraping status"
	@echo "  make start          Start scraping all municipalities"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run tests"
	@echo "  make clean          Clean temporary files"
	@echo "  make format         Format code with black"
	@echo "  make lint           Lint code"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services ready!"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

init:
	python -m src.main init

status:
	python -m src.main status

start:
	python -m src.main start

test:
	pytest tests/ -v --cov=src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

format:
	black src/ tests/

lint:
	flake8 src/ tests/
	mypy src/
