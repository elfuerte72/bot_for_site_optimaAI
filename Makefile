# Makefile для OptimaAI Bot

.PHONY: help install test lint format clean docker-build docker-run deploy-check

# Переменные
PYTHON := python3
PIP := pip
DOCKER_IMAGE := optimaai-bot
DOCKER_TAG := latest

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  install       - Установка зависимостей"
	@echo "  test          - Запуск тестов"
	@echo "  test-cov      - Запуск тестов с покрытием"
	@echo "  lint          - Проверка кода (flake8, mypy)"
	@echo "  format        - Форматирование кода (black, isort)"
	@echo "  clean         - Очистка временных файлов"
	@echo "  docker-build  - Сборка Docker образа"
	@echo "  docker-run    - Запуск в Docker"
	@echo "  deploy-check  - Проверка готовности к деплою"
	@echo "  dev           - Запуск в режиме разработки"

# Установка зависимостей
install:
	$(PIP) install -r requirements.txt

# Установка dev зависимостей
install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov httpx
	$(PIP) install black isort flake8 mypy

# Запуск тестов
test:
	pytest

# Запуск тестов с покрытием
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Проверка кода
lint:
	flake8 .
	mypy src/ --ignore-missing-imports

# Форматирование кода
format:
	black .
	isort .

# Проверка форматирования
check-format:
	black --check .
	isort --check-only .

# Быстрая проверка линтинга
lint-quick:
	flake8 --select=E9,F63,F7,F82 .

# Исправление основных проблем линтинга
lint-fix:
	black .
	isort .
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place . || true

# Полная проверка качества кода
quality: check-format lint test

# Очистка временных файлов
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

# Сборка Docker образа
docker-build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Запуск в Docker
docker-run:
	docker run -p 8000:8000 --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

# Запуск с docker-compose
docker-compose-up:
	docker-compose up --build

# Остановка docker-compose
docker-compose-down:
	docker-compose down

# Проверка готовности к деплою
deploy-check:
	$(PYTHON) scripts/check_deployment.py

# Запуск в режиме разработки
dev:
	$(PYTHON) main.py

# Запуск с автоперезагрузкой
dev-reload:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Создание .env файла из примера
setup-env:
	cp .env.example .env
	@echo "Отредактируйте .env файл и добавьте ваши настройки"

# Инициализация проекта
init: setup-env install-dev
	@echo "Проект инициализирован!"
	@echo "1. Отредактируйте .env файл"
	@echo "2. Запустите: make dev"

# Подготовка к коммиту
pre-commit: format quality
	@echo "Код готов к коммиту!"

# Полная проверка перед деплоем
pre-deploy: quality docker-build deploy-check
	@echo "Готов к деплою!"

# Обновление зависимостей
update-deps:
	$(PIP) list --outdated
	@echo "Обновите requirements.txt при необходимости"

# Генерация requirements.txt из текущего окружения
freeze:
	$(PIP) freeze > requirements.txt

# Проверка безопасности зависимостей
security-check:
	$(PIP) install safety
	safety check

# Запуск линтера с автоисправлениями
lint-fix:
	black src/ tests/
	isort src/ tests/
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src/ tests/

# Создание миграций (если используется Alembic)
migrate:
	alembic revision --autogenerate -m "Auto migration"

# Применение миграций
migrate-up:
	alembic upgrade head

# Откат миграций
migrate-down:
	alembic downgrade -1

# Просмотр логов Docker
logs:
	docker-compose logs -f optimaai-bot

# Мониторинг ресурсов
monitor:
	docker stats

# Backup данных
backup:
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz rag/ rag_index/

# Восстановление из backup
restore:
	@echo "Укажите файл backup для восстановления:"
	@echo "tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz"