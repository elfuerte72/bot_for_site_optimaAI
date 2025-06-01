# 🚀 Быстрый старт CI/CD

## Первоначальная настройка

### 1. Установка Git hooks
```bash
make setup-hooks
```

### 2. Установка зависимостей
```bash
pip install -r requirements-dev.txt
```

### 3. Настройка переменных окружения
```bash
cp .env.example .env.test
# Отредактируйте .env.test для тестов
```

## Основные команды

### 🧪 Тестирование
```bash
make test-ci          # Быстрые тесты
make test-all         # Все тесты
make test-load        # Нагрузочные тесты
```

### 🔍 Качество кода
```bash
make lint             # Проверка кода
make format           # Форматирование
make quality-full     # Полная проверка
```

### 📊 Мониторинг
```bash
make monitor          # Мониторинг производительности
make monitor-load     # Мониторинг с нагрузкой
```

### 💾 Бэкапы
```bash
make backup           # Создать бэкап
make backup-list      # Список бэкапов
make backup-cleanup   # Очистить старые
```

### 🐳 Docker
```bash
make docker-build     # Сборка образа
make docker-run       # Запуск контейнера
make docker-logs-follow # Просмотр логов
```

### 🚀 Релиз
```bash
make pre-release      # Подготовка к релизу
make release-tag      # Создание релиза
```

## GitHub Actions

### Автоматические проверки
- ✅ Качество кода при каждом push
- ✅ Тесты на Python 3.10, 3.11, 3.12
- ✅ Проверки безопасности
- ✅ Сборка Docker образов

### Релизы
- 🏷️ Создание тега → автоматический релиз
- 📦 Публикация Docker образа
- 📝 Генерация changelog

### Обновления
- 📅 Еженедельная проверка зависимостей
- 🔒 Проверка уязвимостей
- 📈 Мониторинг производительности

## Полезные команды

```bash
make help-all         # Все доступные команды
make check-deploy     # Проверка готовности к деплою
make clean-all        # Очистка временных файлов
make project-size     # Размер проекта
make git-stats        # Статистика Git
```

## Структура файлов

```
.github/workflows/    # GitHub Actions
├── ci-cd.yml        # Основной CI/CD
├── dependency-update.yml # Обновления
├── performance.yml  # Производительность
└── release.yml      # Релизы

scripts/             # Скрипты автоматизации
├── setup_hooks.py   # Настройка hooks
├── monitor_performance.py # Мониторинг
├── backup.py        # Бэкапы
└── check_deployment.py # Проверка деплоя

tests/               # Тесты
├── test_integration.py # Интеграционные
├── test_memory_usage.py # Память
└── load_tests.py    # Нагрузочные
```

## Troubleshooting

### Проблемы с тестами
```bash
# Проверить переменные окружения
cat .env.test

# Запустить отдельные тесты
pytest tests/test_api.py -v

# Пропустить проблемные тесты
pytest -m "not integration"
```

### Проблемы с Docker
```bash
# Проверить Docker
docker --version

# Очистить кэш
make clean-all
```

### Проблемы с Git hooks
```bash
# Переустановить hooks
make setup-hooks

# Проверить pre-commit
pre-commit run --all-files
```

## Следующие шаги

1. 🔧 Исправить тесты
2. 🔑 Настроить GitHub Secrets
3. 🚀 Создать первый релиз
4. 📊 Настроить мониторинг
5. 🔄 Автоматизировать деплой