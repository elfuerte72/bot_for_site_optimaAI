# ✅ Чеклист готовности к деплою на Heroku

## 🔧 Исправленные проблемы

### ✅ 1. Переменные окружения
- **Исправлено**: Условная загрузка `.env` файла только для локальной разработки
- **Изменения**: В `src/config.py` добавлена проверка `if os.getenv("DYNO") is None:`
- **Результат**: В продакшене (Heroku) `.env` файл не загружается, используются Config Vars

### ✅ 2. CORS настройки
- **Исправлено**: Парсинг `ALLOWED_ORIGINS` из JSON строки
- **Изменения**: Добавлена функция `_parse_allowed_origins()` в `src/config.py`
- **Результат**: Поддержка формата `["https://example.com"]` из Config Vars

### ✅ 3. Порт и хост
- **Исправлено**: Динамическое чтение порта из переменной `PORT`
- **Изменения**: `port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))`
- **Результат**: Heroku автоматически устанавливает порт через переменную `PORT`

### ✅ 4. Procfile
- **Проверено**: Корректная команда `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Результат**: Готов к деплою

### ✅ 5. Requirements.txt
- **Проверено**: Все зависимости присутствуют
- **Результат**: Готов к деплою

### ✅ 6. Документация
- **Обновлено**: README.md с подробными инструкциями для Heroku
- **Добавлено**: Примеры Config Vars и команд деплоя
- **Создано**: Обновлённый `.env.heroku.example`

## 🚀 Готовность к деплою

### Команды для быстрого деплоя:

```bash
# 1. Создание приложения
heroku create your-app-name
heroku stack:set container -a your-app-name

# 2. Обязательные Config Vars
heroku config:set OPENAI_API_KEY="sk-your-key" -a your-app-name
heroku config:set API_KEY="your-secure-key" -a your-app-name
heroku config:set ALLOWED_ORIGINS='["https://your-frontend.com"]' -a your-app-name

# 3. Рекомендуемые Config Vars
heroku config:set GPT_MODEL="gpt-4o-mini" -a your-app-name
heroku config:set RATE_LIMIT_PER_MINUTE="30" -a your-app-name
heroku config:set ENABLE_CACHE="true" -a your-app-name

# 4. Деплой
git push heroku main

# 5. Проверка
heroku logs --tail -a your-app-name
curl https://your-app-name.herokuapp.com/health
```

## 🔍 Что было исправлено в коде

### src/config.py
```python
# БЫЛО:
load_dotenv()

# СТАЛО:
if os.getenv("DYNO") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
```

```python
# БЫЛО:
port: int = Field(default=8000, ...)

# СТАЛО:
port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")), ...)
```

```python
# БЫЛО:
allowed_origins: List[str] = Field(
    default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"],
    ...
)

# СТАЛО:
allowed_origins: List[str] = Field(
    default_factory=lambda: _parse_allowed_origins(),
    ...
)

def _parse_allowed_origins() -> List[str]:
    origins_raw = os.getenv("ALLOWED_ORIGINS", '[]')
    # ... парсинг JSON строки
```

## ✅ Финальное подтверждение

**Приложение готово к деплою на Heroku!**

- ✅ Все переменные читаются из Config Vars
- ✅ CORS настроен для JSON формата
- ✅ Порт читается динамически
- ✅ Procfile корректен
- ✅ Зависимости полные
- ✅ Документация обновлена

**Следующие шаги:**
1. Установите Config Vars на Heroku
2. Выполните `git push heroku main`
3. Проверьте логи и health endpoint
4. Обновите ALLOWED_ORIGINS с реальными доменами фронтенда

**Важно**: Не забудьте заменить `localhost` в ALLOWED_ORIGINS на реальные домены после деплоя!