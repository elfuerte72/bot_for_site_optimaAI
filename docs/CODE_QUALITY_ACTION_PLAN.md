# План действий по улучшению качества кода

## 🔥 КРИТИЧЕСКИЙ ПРИОРИТЕТ (Неделя 1)

### 1. Исправление JSON сериализации datetime

**Проблема:** `TypeError: Object of type datetime is not JSON serializable`

**Файлы для изменения:**
- `main.py` - добавить custom JSON encoder
- Все endpoints возвращающие datetime

**Решение:**
```python
# В main.py
from fastapi.responses import JSONResponse
from datetime import datetime
import json

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Заменить все JSONResponse на:
def create_json_response(content, status_code=200):
    return JSONResponse(
        content=json.loads(json.dumps(content, cls=DateTimeEncoder)),
        status_code=status_code
    )
```

### 2. Миграция на Pydantic V2

**Файлы для изменения:**
- `src/config.py`
- `src/models/message.py`
- `src/validators/input_validator.py`

**Изменения:**
```python
# Заменить
from pydantic import validator
@validator("field_name")

# На
from pydantic import field_validator
@field_validator("field_name")

# Заменить
class Config:
    env_file = ".env"

# На
model_config = ConfigDict(env_file=".env")
```

### 3. Исправление тестов

**Файлы для изменения:**
- `tests/test_api.py`
- `tests/test_security.py`

**Задачи:**
- [ ] Добавить моки для настроек с отключенной аутентификацией
- [ ] Исправить проблемы с datetime сериализацией в тестах
- [ ] Добавить правильные заголовки для CORS тестов
- [ ] Настроить rate limiting заголовки в тестах

### 4. Базовые аннотации типов

**Файлы с критическими ошибками типизации:**
- `src/models/message.py` - 4 ошибки
- `src/validators/input_validator.py` - 5 ошибок
- `src/config.py` - 3 ошибки

## 🔶 ВЫСОКИЙ ПРИОРИТЕТ (Неделя 2)

### 5. Увеличение покрытия тестами

**Цель:** Достичь 80% покрытия

**Модули требующие тестов:**

#### `src/services/openai_service.py` (19% → 80%)
- [ ] Тесты для `generate_response()`
- [ ] Тесты для RAG интеграции
- [ ] Тесты для retry механизма
- [ ] Тесты для stream response
- [ ] Тесты для error handling

#### `src/rag/rag_system.py` (25% → 80%)
- [ ] Тесты для инициализации
- [ ] Тесты для добавления документов
- [ ] Тесты для поиска
- [ ] Тесты для генерации ответов

#### `src/security/config_validator.py` (15% → 80%)
- [ ] Тесты для всех валидаторов
- [ ] Тесты для edge cases
- [ ] Тесты для error scenarios

#### `src/services/cache_service.py` (38% → 80%)
- [ ] Тесты для всех операций кэша
- [ ] Тесты для TTL
- [ ] Тесты для очистки

### 6. Исправление длинных строк (22 нарушения E501)

**Файлы для исправления:**
```bash
# Автоматическое исправление с помощью Black
python -m black src/ --line-length 88

# Ручное исправление для сложных случаев
src/security/config_validator.py:162-252
src/services/openai_service.py:77,85,211
src/validators/input_validator.py:61,109
```

## 🔷 СРЕДНИЙ ПРИОРИТЕТ (Неделя 3)

### 7. Полное исправление типизации (86 ошибок MyPy)

**По файлам:**

#### `src/middleware/security_headers.py` (15 ошибок)
- [ ] Добавить аннотации для всех функций
- [ ] Исправить Optional типы
- [ ] Убрать unreachable code

#### `src/middleware/sanitization.py` (8 ошибок)
- [ ] Исправить типы для dict/list операций
- [ ] Добавить аннотации функций

#### `src/services/openai_service.py` (15 ошибок)
- [ ] Исправить типы для OpenAI API
- [ ] Добавить правильные типы для MessageResponse

### 8. Интеграционные тесты

**Новые тестовые файлы:**
- [ ] `tests/test_integration_openai.py`
- [ ] `tests/test_integration_rag.py`
- [ ] `tests/test_integration_middleware.py`
- [ ] `tests/test_integration_security.py`

### 9. Улучшение обработки ошибок

**Задачи:**
- [ ] Добавить специфичные исключения для каждого модуля
- [ ] Улучшить error messages
- [ ] Добавить proper logging для всех ошибок

## 🔹 НИЗКИЙ ПРИОРИТЕТ (Неделя 4+)

### 10. Настройка CI/CD проверок

**Файл:** `.github/workflows/quality.yml`
```yaml
name: Code Quality
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests with coverage
        run: pytest --cov=src --cov-fail-under=80
      - name: Run flake8
        run: flake8 src/
      - name: Run mypy
        run: mypy src/
      - name: Run black check
        run: black --check src/
```

### 11. Метрики производительности

**Новые файлы:**
- [ ] `src/monitoring/performance.py`
- [ ] `tests/test_performance.py`

### 12. Улучшение документации

**Задачи:**
- [ ] Добавить OpenAPI описания для всех endpoints
- [ ] Улучшить README.md
- [ ] Добавить примеры использования API

## Чек-лист выполнения

### Критический уровень ✅
- [ ] JSON сериализация исправлена
- [ ] Pydantic V2 миграция завершена
- [ ] Все тесты проходят
- [ ] Базовые аннотации типов добавлены

### Высокий уровень ✅
- [ ] Покрытие тестами ≥ 80%
- [ ] Все E501 ошибки исправлены
- [ ] Критические модули покрыты тестами

### Средний уровень ✅
- [ ] MyPy ошибки < 10
- [ ] Интеграционные тесты добавлены
- [ ] Обработка ошибок улучшена

### Низкий уровень ✅
- [ ] CI/CD настроен
- [ ] Метрики производительности добавлены
- [ ] Документация обновлена

## Команды для проверки прогресса

```bash
# Проверка покрытия тестами
pytest --cov=src --cov-report=term-missing

# Проверка стиля кода
flake8 src/ --count --statistics

# Проверка типизации
mypy src/ --ignore-missing-imports

# Проверка форматирования
black --check src/

# Запуск всех тестов
pytest tests/ -v

# Проверка безопасности
bandit -r src/
```

## Критерии готовности

Проект считается готовым к продакшену когда:
- ✅ Все тесты проходят (0 failed)
- ✅ Покрытие тестами ≥ 80%
- ✅ MyPy ошибки = 0
- ✅ Flake8 ошибки = 0
- ✅ Все критические security issues исправлены
- ✅ CI/CD pipeline настроен и работает

---
*План создан: 2025-06-01*
*Ответственный: Development Team*
*Дедлайн: 4 недели*