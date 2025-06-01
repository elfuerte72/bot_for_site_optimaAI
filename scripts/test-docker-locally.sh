#!/bin/bash
# Скрипт для локального тестирования Docker образа перед деплоем на Heroku

set -e

echo "🐳 Тестирование Docker образа локально..."

# Проверка Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker не запущен. Запустите Docker Desktop."
    exit 1
fi

# Проверка .env файла
if [ ! -f .env ]; then
    echo "⚠️  .env файл не найден. Создаю из примера..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Создан .env файл. Пожалуйста, заполните его и запустите скрипт снова."
        exit 1
    else
        echo "❌ .env.example не найден"
        exit 1
    fi
fi

# Загрузка переменных окружения
export $(cat .env | grep -v '^#' | xargs)

# Остановка предыдущих контейнеров
echo "🛑 Остановка предыдущих контейнеров..."
docker-compose -f docker-compose.test.yml down 2>/dev/null || true

# Сборка образа
echo "🔨 Сборка Docker образа..."
docker build -f Dockerfile.heroku -t fastapi-rag-heroku .

# Запуск контейнера
echo "🚀 Запуск контейнера..."
docker-compose -f docker-compose.test.yml up -d

# Ожидание запуска
echo "⏳ Ожидание запуска приложения..."
sleep 5

# Проверка здоровья
echo "🔍 Проверка здоровья API..."
if curl -f http://localhost:8000/health; then
    echo -e "\n✅ API работает корректно!"
else
    echo -e "\n❌ API не отвечает"
    echo "📋 Логи контейнера:"
    docker-compose -f docker-compose.test.yml logs
    exit 1
fi

echo -e "\n📊 Доступные эндпоинты:"
echo "- Health: http://localhost:8000/health"
echo "- Docs: http://localhost:8000/docs"
echo "- Chat: POST http://localhost:8000/chat"

echo -e "\n💡 Команды для работы:"
echo "- Просмотр логов: docker-compose -f docker-compose.test.yml logs -f"
echo "- Остановка: docker-compose -f docker-compose.test.yml down"
echo "- Перезапуск: docker-compose -f docker-compose.test.yml restart"

echo -e "\n🧪 Тест API запроса:"
echo 'curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}"'