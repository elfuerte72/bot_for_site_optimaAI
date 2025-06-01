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

# === CI/CD КОМАНДЫ ===

# Настройка Git hooks
setup-hooks:
	python scripts/setup_hooks.py

# Запуск всех pre-commit hooks
pre-commit-all:
	pre-commit run --all-files

# Обновление pre-commit hooks
pre-commit-update:
	pre-commit autoupdate

# Проверка готовности к деплою
check-deploy:
	python scripts/check_deployment.py

# Мониторинг производительности
monitor:
	python scripts/monitor_performance.py

# Мониторинг с нагрузочным тестом
monitor-load:
	python scripts/monitor_performance.py --load-test --duration 300

# === BACKUP КОМАНДЫ ===

# Создание полного бэкапа
backup:
	python scripts/backup.py create

# Создание именованного бэкапа
backup-named:
	@read -p "Enter backup name: " name; \
	python scripts/backup.py create --name "$name"

# Список бэкапов
backup-list:
	python scripts/backup.py list

# Очистка старых бэкапов
backup-cleanup:
	python scripts/backup.py cleanup

# Восстановление бэкапа
backup-restore:
	@read -p "Enter backup name: " name; \
	python scripts/backup.py restore --name "$name"

# === ТЕСТИРОВАНИЕ ===

# Быстрые тесты для CI
test-ci:
	pytest --tb=short -q --disable-warnings

# Интеграционные тесты
test-integration:
	pytest -m integration -v

# Тесты производительности
test-performance:
	pytest -m performance -v

# Нагрузочные тесты
test-load:
	locust -f tests/load_tests.py --headless -u 10 -r 2 -t 60s --host=http://localhost:8000

# Тесты памяти
test-memory:
	python tests/test_memory_usage.py

# Все типы тестов
test-all: test test-integration test-performance

# === DOCKER КОМАНДЫ ===

# Сборка для разных архитектур
docker-build-multi:
	docker buildx build --platform linux/amd64,linux/arm64 -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Запуск с мониторингом
docker-run-monitor:
	docker run -d --name optimaai-monitor -p 8000:8000 --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)
	docker stats optimaai-monitor

# Логи контейнера
docker-logs-follow:
	docker logs -f optimaai-bot

# === КАЧЕСТВО КОДА ===

# Полная проверка качества
quality-full: format-check lint security-check test-ci

# Исправление всех проблем
fix-all: format lint-fix

# Анализ сложности кода
complexity:
	radon cc src/ -a
	radon mi src/ -a

# === ДОКУМЕНТАЦИЯ ===

# Генерация документации
docs:
	sphinx-build -b html docs/ docs/_build/html

# Проверка документации
docs-check:
	sphinx-build -b linkcheck docs/ docs/_build/linkcheck

# === РЕЛИЗ ===

# Подготовка к релизу
pre-release: quality-full check-deploy backup
	@echo "Ready for release!"

# Создание тега релиза
release-tag:
	@read -p "Enter version (e.g., v1.2.3): " version; \
	git tag -a "$version" -m "Release $version"; \
	git push origin "$version"

# === УТИЛИТЫ ===

# Проверка портов
check-ports:
	lsof -i :8000 || echo "Port 8000 is free"
	lsof -i :6379 || echo "Port 6379 is free"

# Очистка всех временных файлов
clean-all: clean
	docker system prune -f
	docker volume prune -f
	rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ .coverage

# Показать размер проекта
project-size:
	du -sh .
	find . -name "*.py" | xargs wc -l | tail -1

# Статистика Git
git-stats:
	git log --oneline | wc -l
	git shortlog -sn

# === ПОМОЩЬ ===

# Показать все доступные команды
help-all:
	@echo "=== ОСНОВНЫЕ КОМАНДЫ ==="
	@echo "  install       - Установка зависимостей"
	@echo "  test          - Запуск тестов"
	@echo "  lint          - Проверка кода"
	@echo "  format        - Форматирование кода"
	@echo "  dev           - Запуск в режиме разработки"
	@echo ""
	@echo "=== CI/CD ==="
	@echo "  setup-hooks   - Настройка Git hooks"
	@echo "  check-deploy  - Проверка готовности к деплою"
	@echo "  monitor       - Мониторинг производительности"
	@echo ""
	@echo "=== ТЕСТИРОВАНИЕ ==="
	@echo "  test-ci       - Быстрые тесты для CI"
	@echo "  test-integration - Интеграционные тесты"
	@echo "  test-load     - Нагрузочные тесты"
	@echo "  test-all      - Все типы тестов"
	@echo ""
	@echo "=== BACKUP ==="
	@echo "  backup        - Создание бэкапа"
	@echo "  backup-list   - Список бэкапов"
	@echo "  backup-cleanup - Очистка старых бэкапов"
	@echo ""
	@echo "=== DOCKER ==="
	@echo "  docker-build  - Сборка образа"
	@echo "  docker-run    - Запуск контейнера"
	@echo "  docker-logs-follow - Просмотр логов"
	@echo ""
	@echo "=== РЕЛИЗ ==="
	@echo "  pre-release   - Подготовка к релизу"
	@echo "  release-tag   - Создание тега релиза"



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





# Восстановление из backup (устаревшая команда)
restore:
	@echo "Используйте: make backup-restore"