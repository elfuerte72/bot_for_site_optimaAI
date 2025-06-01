#!/bin/bash
# Скрипт для настройки переменных окружения в Heroku

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔧 Настройка переменных окружения для Heroku"

# Проверка аргументов
if [ -z "$1" ]; then
    echo -e "${RED}❌ Укажите имя приложения Heroku${NC}"
    echo "Использование: ./setup-heroku-env.sh <app-name> [env-file]"
    exit 1
fi

APP_NAME=$1
ENV_FILE=${2:-.env}

# Проверка файла окружения
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Файл $ENV_FILE не найден${NC}"
    echo "Создайте файл с переменными окружения или укажите существующий"
    exit 1
fi

echo -e "${YELLOW}📱 Приложение: $APP_NAME${NC}"
echo -e "${YELLOW}📄 Файл окружения: $ENV_FILE${NC}"

# Функция для безопасного чтения значения переменной
read_secure_value() {
    local var_name=$1
    local prompt=$2
    echo -n "$prompt: "
    read -s value
    echo
    echo "$value"
}

# Чтение и установка переменных
echo -e "\n${GREEN}🔐 Настройка переменных окружения...${NC}\n"

while IFS='=' read -r key value; do
    # Пропускаем комментарии и пустые строки
    if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Удаляем пробелы
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Удаляем кавычки если есть
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    
    # Проверяем чувствительные переменные
    if [[ "$key" == "OPENAI_API_KEY" && "$value" == "sk-"* ]]; then
        echo -e "${YELLOW}⚠️  $key выглядит как placeholder${NC}"
        value=$(read_secure_value "$key" "Введите реальный OpenAI API ключ")
    elif [[ "$key" == "API_KEY" && ${#value} -lt 20 ]]; then
        echo -e "${YELLOW}⚠️  $key слишком короткий для безопасности${NC}"
        value=$(read_secure_value "$key" "Введите безопасный API ключ (минимум 20 символов)")
    fi
    
    # Устанавливаем переменную
    echo -n "Устанавливаю $key... "
    if heroku config:set "$key=$value" -a "$APP_NAME" >/dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        echo -e "${RED}Ошибка при установке $key${NC}"
    fi
done < "$ENV_FILE"

echo -e "\n${GREEN}📋 Текущие переменные окружения:${NC}"
heroku config -a "$APP_NAME"

echo -e "\n${GREEN}✅ Настройка завершена!${NC}"
echo -e "${YELLOW}💡 Совет: Используйте 'heroku config:unset VAR_NAME -a $APP_NAME' для удаления переменной${NC}"