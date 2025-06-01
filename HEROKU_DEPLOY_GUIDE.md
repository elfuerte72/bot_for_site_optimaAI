# Руководство по деплою на Heroku

## Предварительные требования

1. Установленный Heroku CLI
2. Docker Desktop запущен
3. Аккаунт на Heroku
4. Настроенные переменные окружения

## Шаг 1: Подготовка проекта

### Проверка Docker
```bash
docker --version
docker ps
```

### Создание .env файла для продакшена
Убедитесь, что у вас есть все необходимые переменные окружения:
- `OPENAI_API_KEY`
- `API_KEY` (для защиты API)
- `ALLOWED_ORIGINS` (домены фронтенда)

## Шаг 2: Создание приложения на Heroku

```bash
# Войдите в Heroku
heroku login

# Создайте новое приложение
heroku create your-app-name

# Или используйте существующее
heroku git:remote -a your-app-name
```

## Шаг 3: Настройка переменных окружения

```bash
# Основные переменные
heroku config:set OPENAI_API_KEY="your-openai-api-key"
heroku config:set API_KEY="your-secure-api-key"
heroku config:set ALLOWED_ORIGINS="https://your-frontend.com,https://www.your-frontend.com"

# Дополнительные настройки
heroku config:set GPT_MODEL="gpt-4o-mini"
heroku config:set RATE_LIMIT_PER_MINUTE="30"
heroku config:set ENABLE_CACHE="true"
heroku config:set CACHE_TTL_SECONDS="3600"
heroku config:set MAX_HISTORY_MESSAGES="10"

# Проверка переменных
heroku config
```

## Шаг 4: Деплой через Container Registry

### Вариант 1: Использование heroku.yml (рекомендуется)

```bash
# Установка stack на container
heroku stack:set container

# Коммит изменений
git add .
git commit -m "Подготовка для Heroku деплоя"

# Деплой
git push heroku main
```

### Вариант 2: Прямой push в Container Registry

```bash
# Логин в Container Registry
heroku container:login

# Сборка и push образа
heroku container:push web --arg-file Dockerfile.heroku

# Релиз образа
heroku container:release web
```

## Шаг 5: Проверка деплоя

```bash
# Проверка логов
heroku logs --tail

# Открытие приложения
heroku open

# Проверка здоровья API
curl https://your-app-name.herokuapp.com/health
```

## Шаг 6: Мониторинг и обслуживание

### Просмотр логов
```bash
heroku logs --tail -a your-app-name
```

### Перезапуск приложения
```bash
heroku restart -a your-app-name
```

### Масштабирование
```bash
# Проверка текущих dynos
heroku ps

# Масштабирование
heroku ps:scale web=1
```

## Устранение проблем

### 1. Ошибка с портом
Heroku автоматически назначает порт через переменную окружения `$PORT`. Убедитесь, что в Dockerfile используется:
```dockerfile
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### 2. Проблемы с памятью
Если приложение превышает лимиты памяти:
- Оптимизируйте размер модели
- Уменьшите размер кэша
- Используйте более мощный dyno тип

### 3. Таймауты
Heroku имеет 30-секундный таймаут для запросов. Для длительных операций:
- Используйте фоновые задачи
- Реализуйте streaming ответы
- Оптимизируйте запросы к OpenAI

### 4. RAG индекс
Heroku использует ephemeral файловую систему. Для постоянного хранения RAG индекса:
- Используйте внешнее хранилище (S3, CloudStorage)
- Или пересоздавайте индекс при каждом запуске

## Безопасность

1. **Никогда не коммитьте .env файл**
2. Используйте сильные API ключи
3. Ограничьте CORS только вашими доменами
4. Регулярно обновляйте зависимости
5. Мониторьте использование API

## Полезные команды

```bash
# Проверка состояния
heroku ps -a your-app-name

# Просмотр конфигурации
heroku config -a your-app-name

# Bash в контейнере
heroku run bash -a your-app-name

# Проверка использования ресурсов
heroku ps:type -a your-app-name
```

## Автоматизация деплоя

### GitHub Actions
Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Heroku

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "your-app-name"
        heroku_email: "your-email@example.com"
        usedocker: true
        docker_build_args: |
          --file Dockerfile.heroku
```

## Проверка готовности к продакшену

- [ ] Все переменные окружения настроены
- [ ] API защищен ключом
- [ ] CORS настроен правильно
- [ ] Логирование работает
- [ ] Health check endpoint доступен
- [ ] Rate limiting активен
- [ ] Обработка ошибок настроена
- [ ] Docker образ оптимизирован