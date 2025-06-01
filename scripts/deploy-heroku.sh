#!/bin/bash
# Скрипт для деплоя на Heroku

set -e

echo "🚀 Начинаем деплой на Heroku..."

# Проверка наличия Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI не установлен. Установите его с https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Проверка Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker не запущен. Запустите Docker Desktop."
    exit 1
fi

# Проверка аргументов
if [ -z "$1" ]; then
    echo "❌ Укажите имя приложения Heroku"
    echo "Использование: ./deploy-heroku.sh <app-name>"
    exit 1
fi

APP_NAME=$1

echo "📦 Приложение: $APP_NAME"

# Проверка git
if [ ! -d .git ]; then
    echo "❌ Это не git репозиторий. Инициализируйте git."
    exit 1
fi

# Установка Heroku remote
echo "🔗 Настройка Heroku remote..."
heroku git:remote -a $APP_NAME 2>/dev/null || {
    echo "❓ Приложение не найдено. Создать новое? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        heroku create $APP_NAME
    else
        exit 1
    fi
}

# Установка stack на container
echo "🐳 Настройка container stack..."
heroku stack:set container -a $APP_NAME

# Проверка переменных окружения
echo "🔐 Проверка переменных окружения..."
REQUIRED_VARS=("OPENAI_API_KEY" "API_KEY")

for var in "${REQUIRED_VARS[@]}"; do
    if ! heroku config:get $var -a $APP_NAME &> /dev/null; then
        echo "⚠️  Переменная $var не установлена"
        echo -n "Введите значение для $var: "
        read -s value
        echo
        heroku config:set $var="$value" -a $APP_NAME
    else
        echo "✅ $var установлена"
    fi
done

# Коммит изменений
echo "📝 Коммит изменений..."
git add -A
git commit -m "Deploy to Heroku" || echo "Нет изменений для коммита"

# Деплой
echo "🚀 Деплой приложения..."
git push heroku main || git push heroku master

# Проверка статуса
echo "🔍 Проверка статуса..."
heroku ps -a $APP_NAME

# Открытие логов
echo "📋 Открытие логов (Ctrl+C для выхода)..."
heroku logs --tail -a $APP_NAME