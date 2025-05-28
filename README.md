# OptimaAI Bot

Бот с интеграцией OpenAI API для компании OptimaAI.

## Структура проекта

```
backend/
├── .env                # Файл с переменными окружения
├── .venv/              # Виртуальное окружение Python
├── main.py             # Основной файл приложения
├── requirements.txt    # Зависимости проекта
└── src/                # Исходный код
    ├── config.py       # Конфигурация приложения
    ├── models/         # Модели данных
    │   └── message.py  # Модели сообщений
    └── services/       # Сервисы
        └── openai_service.py  # Сервис для работы с OpenAI API
```

## Установка и запуск

1. Активировать виртуальное окружение:
```bash
source .venv/bin/activate
```

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Настроить переменные окружения в файле `.env`:
```
OPENAI_API_KEY=ваш_ключ_api
SYSTEM_PROMPT=системный_промпт
GPT_MODEL=gpt-4.1-nano
```

4. Запустить сервер:
```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

## API Endpoints

### GET /health
Проверка работоспособности API.

### POST /chat
Отправка сообщения боту и получение ответа.

Пример запроса:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Расскажи о компании OptimaAI"
    }
  ],
  "stream": false
}
```

## Документация API

После запуска сервера документация Swagger доступна по адресу:
http://localhost:8000/docs
