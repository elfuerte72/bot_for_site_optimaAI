# OptimaAI Bot API v2.0

Современный и безопасный API для чат-бота с интеграцией OpenAI и RAG системой.

## 🚀 Основные возможности

- **FastAPI** с автоматической документацией
- **OpenAI GPT** интеграция с поддержкой streaming
- **RAG система** с векторным поиском (FAISS/ChromaDB)
- **Кэширование** ответов для оптимизации производительности
- **Rate limiting** для защиты от злоупотреблений
- **Централизованная обработка ошибок**
- **Структурированное логирование**
- **Полная типизация** с Pydantic
- **Тесты** с покрытием
- **Docker** поддержка

## 📋 Требования

- Python 3.9+
- OpenAI API ключ
- 2GB+ RAM (для векторных индексов)

## 🛠 Установка и запуск

### Локальная разработка

1. **Клонирование и настройка окружения:**
```bash
git clone <repository>
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или .venv\Scripts\activate  # Windows
```

2. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

3. **Настройка переменных окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив ваш OpenAI API ключ
```

**Важно**: В локальной разработке `.env` файл загружается автоматически. В продакшене (Heroku) переменные читаются из Config Vars.

4. **Запуск приложения:**
```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

### Тестирование CORS и API

1. **Проверка health endpoint:**
```bash
curl http://localhost:8000/health
```

2. **Тестирование chat endpoint:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"messages": [{"role": "user", "content": "Привет!"}]}'
```

3. **Проверка CORS (из браузера):**
```javascript
fetch('http://localhost:8000/health', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

### Docker

1. **Сборка и запуск:**
```bash
docker-compose up --build
```

2. **Только основной сервис:**
```bash
docker-compose up optimaai-bot
```

3. **С дополнительными сервисами (Redis, Nginx):**
```bash
docker-compose --profile with-redis --profile with-nginx up
```

## 📚 API Документация

После запуска сервера документация доступна по адресам:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты

#### `GET /health`
Проверка работоспособности API с детальной информацией о статусе сервисов.

#### `POST /chat`
Основной эндпоинт для общения с ботом.

**Пример запроса:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Расскажи о компании OptimaAI"
    }
  ],
  "stream": false,
  "use_cache": true,
  "temperature": 0.7,
  "max_tokens": 1024
}
```

#### `GET /cache/stats`
Статистика кэша.

#### `POST /cache/clear`
Очистка кэша.

#### `GET /metrics`
Метрики приложения для мониторинга.

## ⚙️ Конфигурация

Все настройки управляются через переменные окружения:

### Основные настройки
- `OPENAI_API_KEY` - OpenAI API ключ (обязательно)
- `GPT_MODEL` - Модель GPT (по умолчанию: gpt-4o-mini)
- `DEBUG` - Режим отладки (по умолчанию: false)
- `PORT` - Порт для запуска (автоматически устанавливается Heroku)

### Безопасность
- `ALLOWED_ORIGINS` - Разрешённые домены для CORS в формате JSON массива: `["https://example.com"]`
- `RATE_LIMIT_PER_MINUTE` - Лимит запросов в минуту (по умолчанию: 100)
- `API_KEY` - Опциональный API ключ для аутентификации

### Кэширование
- `ENABLE_CACHE` - Включить кэширование (по умолчанию: true)
- `CACHE_TTL_SECONDS` - TTL кэша в секундах (по умолчанию: 3600)

### История сообщений
- `MAX_HISTORY_MESSAGES` - Максимальное количество сообщений в истории (по умолчанию: 10)

### RAG система
- `RAG_CHUNK_SIZE` - Размер чанка (по умолчанию: 1000)
- `RAG_CHUNK_OVERLAP` - Перекрытие чанков (по умолчанию: 200)
- `RAG_K_DOCUMENTS` - Количество документов для поиска (по умолчанию: 4)
- `EMBEDDING_MODEL` - Модель для эмбеддингов (по умолчанию: text-embedding-3-small)

### Пути
- `DATA_DIR` - Директория с данными (по умолчанию: rag)
- `PERSIST_DIR` - Директория для индексов (по умолчанию: rag_index)

### Системный промпт
- `SYSTEM_PROMPT` - Кастомный системный промпт (опционально)

### Примеры значений для Heroku Config Vars

```bash
# Обязательные
OPENAI_API_KEY=sk-proj-...
API_KEY=your-secure-random-key-here
ALLOWED_ORIGINS=["https://your-frontend.com"]

# Рекомендуемые для продакшена
GPT_MODEL=gpt-4o-mini
RATE_LIMIT_PER_MINUTE=30
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
MAX_HISTORY_MESSAGES=10
```

## 🧪 Тестирование

### Запуск тестов
```bash
pytest
```

### С покрытием кода
```bash
pytest --cov=src --cov-report=html
```

### Только быстрые тесты
```bash
pytest -m "not slow"
```

## 🔧 Разработка

### Форматирование кода
```bash
black src/ tests/
isort src/ tests/
```

### Проверка типов
```bash
mypy src/
```

### Линтинг
```bash
flake8 src/ tests/
```

## 📁 Структура проекта

```
backend/
├── src/                    # Исходный код
│   ├── config.py          # Конфигурация
│   ├── exceptions.py      # Кастомные исключения
│   ├── models/            # Pydantic модели
│   ├── services/          # Бизнес-логика
│   ├── middleware/        # Middleware компоненты
│   └── rag/              # RAG система
├── tests/                 # Тесты
├── rag/                   # Документы для RAG
├── rag_index/            # Векторные индексы
├── main.py               # Точка входа
├── requirements.txt      # Зависимости
├── Dockerfile           # Docker образ
├── docker-compose.yml   # Docker Compose
└── pyproject.toml       # Конфигурация инструментов
```

## 🔒 Безопасность

### Реализованные меры безопасности:
- ✅ CORS с ограниченными доменами
- ✅ Rate limiting по IP
- ✅ Валидация входных данных
- ✅ Централизованная обработка ошибок
- ✅ Структурированное логирование
- ✅ Непривилегированный пользователь в Docker

### Рекомендации для продакшена:
- Используйте HTTPS (Heroku предоставляет автоматически)
- Настройте мониторинг и алерты
- Регулярно обновляйте зависимости
- Используйте внешний кэш (Redis) для масштабирования
- Настройте backup векторных индексов
- Используйте надёжные случайные API ключи
- Ограничьте CORS только необходимыми доменами
- Настройте rate limiting в соответствии с нагрузкой
- Мониторьте использование OpenAI API токенов

## 📊 Мониторинг

### Доступные метрики:
- Время работы сервиса
- Статус кэша
- Количество запросов
- Время обработки запросов

### Логирование:
- Структурированные логи в JSON формате
- Различные уровни логирования
- Ротация логов
- Интеграция с внешними системами мониторинга

## 🚀 Деплой

### Heroku деплой

#### Подготовка к деплою
1. Убедитесь, что все изменения закоммичены в git
2. Установите Heroku CLI
3. Войдите в аккаунт: `heroku login`

#### Создание приложения
```bash
heroku create your-app-name
heroku stack:set container -a your-app-name
```

#### Настройка Config Vars на Heroku

**Обязательные переменные:**
```bash
# OpenAI API ключ
heroku config:set OPENAI_API_KEY="sk-your-openai-api-key" -a your-app-name

# API ключ для аутентификации
heroku config:set API_KEY="your-secure-api-key" -a your-app-name

# CORS настройки (JSON массив)
heroku config:set ALLOWED_ORIGINS='["https://your-frontend.com", "https://www.your-frontend.com"]' -a your-app-name
```

**Опциональные переменные:**
```bash
# Модель GPT
heroku config:set GPT_MODEL="gpt-4o-mini" -a your-app-name

# Rate limiting
heroku config:set RATE_LIMIT_PER_MINUTE="30" -a your-app-name

# Кэширование
heroku config:set ENABLE_CACHE="true" -a your-app-name
heroku config:set CACHE_TTL_SECONDS="3600" -a your-app-name

# История сообщений
heroku config:set MAX_HISTORY_MESSAGES="10" -a your-app-name

# RAG настройки
heroku config:set RAG_CHUNK_SIZE="1000" -a your-app-name
heroku config:set RAG_CHUNK_OVERLAP="200" -a your-app-name
heroku config:set RAG_K_DOCUMENTS="4" -a your-app-name
heroku config:set EMBEDDING_MODEL="text-embedding-3-small" -a your-app-name

# Системный промпт (опционально)
heroku config:set SYSTEM_PROMPT="Ваш кастомный системный промпт" -a your-app-name
```

#### Деплой
```bash
git push heroku main
```

#### Проверка после деплоя
```bash
# Проверка логов
heroku logs --tail -a your-app-name

# Проверка статуса
heroku ps -a your-app-name

# Тест API
curl https://your-app-name.herokuapp.com/health

# Открыть документацию
heroku open /docs -a your-app-name
```

### Локальная разработка с Heroku переменными

Для тестирования с теми же переменными, что и на Heroku:

1. Создайте `.env` файл:
```bash
cp .env.heroku.example .env
```

2. Заполните переменные в `.env`:
```bash
OPENAI_API_KEY=sk-your-openai-api-key
API_KEY=your-secure-api-key
ALLOWED_ORIGINS=["http://localhost:3000"]
GPT_MODEL=gpt-4o-mini
RATE_LIMIT_PER_MINUTE=100
ENABLE_CACHE=true
```

### Docker в продакшене:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Важные моменты для Heroku

1. **Порт**: Heroku автоматически устанавливает переменную `PORT`
2. **CORS**: Обязательно укажите реальные домены вашего фронтенда
3. **API ключ**: Используйте надёжный случайный ключ
4. **Файловая система**: Ephemeral - файлы не сохраняются между рестартами
5. **Таймаут**: 30 секунд на HTTP запрос
6. **Память**: Free tier = 512MB RAM

## 🤝 Вклад в разработку

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Добавьте тесты для новой функциональности
4. Убедитесь, что все тесты проходят
5. Отправьте Pull Request

## 📄 Лицензия

MIT License

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:

### Локальная разработка
1. Проверьте, что все переменные в `.env` файле заполнены
2. Убедитесь, что OpenAI API ключ действителен
3. Проверьте логи в консоли или файле `app.log`

### Heroku деплой
1. Проверьте логи: `heroku logs --tail -a your-app-name`
2. Убедитесь, что все Config Vars установлены: `heroku config -a your-app-name`
3. Проверьте статус приложения: `heroku ps -a your-app-name`
4. Перезапустите приложение: `heroku restart -a your-app-name`

### Частые проблемы

**Ошибка CORS:**
- Убедитесь, что домен фронтенда добавлен в `ALLOWED_ORIGINS`
- Формат должен быть JSON массивом: `["https://example.com"]`

**Ошибка аутентификации:**
- Проверьте, что `X-API-Key` заголовок передаётся с запросом
- Убедитесь, что значение совпадает с `API_KEY` в Config Vars

**Ошибка OpenAI API:**
- Проверьте, что `OPENAI_API_KEY` установлен и действителен
- Убедитесь, что у вас есть доступ к указанной модели

**Приложение не запускается на Heroku:**
- Проверьте, что `Procfile` содержит правильную команду
- Убедитесь, что все зависимости указаны в `requirements.txt`
- Проверьте логи на наличие ошибок импорта

### Создание issue
Если проблема не решается:
1. Приложите логи ошибки
2. Укажите версию Python и зависимостей
3. Опишите шаги для воспроизведения
4. Создайте issue в репозитории