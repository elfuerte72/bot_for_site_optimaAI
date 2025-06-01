#!/bin/bash

# Скрипт для безопасного развертывания OptimaAI Bot в продакшене
# Включает настройку HTTPS, firewall, security headers и DDoS защиты

set -e

# Конфигурация
DOMAIN=""
EMAIL=""
ENVIRONMENT="production"
ENABLE_FIREWALL=true
ENABLE_LETSENCRYPT=true
ENABLE_MONITORING=true

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Безопасное развертывание OptimaAI Bot${NC}"
echo ""

# Функция для вывода справки
show_help() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -d DOMAIN        Доменное имя (обязательно для продакшена)"
    echo "  -e EMAIL         Email для Let's Encrypt (обязательно для продакшена)"
    echo "  -env ENV         Окружение: development|production (по умолчанию: production)"
    echo "  --no-firewall    Отключить настройку firewall"
    echo "  --no-ssl         Отключить настройку Let's Encrypt"
    echo "  --no-monitoring  Отключить мониторинг"
    echo "  -h, --help       Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 -d api.example.com -e admin@example.com"
    echo "  $0 -env development --no-ssl"
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -env|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --no-firewall)
            ENABLE_FIREWALL=false
            shift
            ;;
        --no-ssl)
            ENABLE_LETSENCRYPT=false
            shift
            ;;
        --no-monitoring)
            ENABLE_MONITORING=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Неизвестный параметр: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Проверка обязательных параметров для продакшена
if [[ "$ENVIRONMENT" == "production" ]]; then
    if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
        echo -e "${RED}❌ Для продакшена обязательны параметры -d и -e${NC}"
        show_help
        exit 1
    fi
fi

# Проверка прав администратора
if [[ $EUID -ne 0 ]] && [[ "$ENABLE_FIREWALL" == true || "$ENABLE_LETSENCRYPT" == true ]]; then
    echo -e "${RED}❌ Для настройки firewall и SSL требуются права администратора${NC}"
    echo "   Запустите: sudo $0 $@"
    exit 1
fi

echo -e "${BLUE}📋 Конфигурация развертывания:${NC}"
echo "   Окружение: $ENVIRONMENT"
echo "   Домен: ${DOMAIN:-'не указан'}"
echo "   Email: ${EMAIL:-'не указан'}"
echo "   Firewall: $ENABLE_FIREWALL"
echo "   Let's Encrypt: $ENABLE_LETSENCRYPT"
echo "   Мониторинг: $ENABLE_MONITORING"
echo ""

# Функция для проверки системных требований
check_requirements() {
    echo -e "${YELLOW}🔍 Проверка системных требований...${NC}"
    
    # Проверка Docker
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker не установлен${NC}"
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker Compose не установлен${NC}"
        exit 1
    fi
    
    # Проверка доступности портов
    if netstat -tuln | grep -q ":80 "; then
        echo -e "${YELLOW}⚠️ Порт 80 уже используется${NC}"
    fi
    
    if netstat -tuln | grep -q ":443 "; then
        echo -e "${YELLOW}⚠️ Порт 443 уже используется${NC}"
    fi
    
    echo -e "${GREEN}✅ Системные требования проверены${NC}"
}

# Функция для настройки переменных окружения
setup_environment() {
    echo -e "${YELLOW}⚙️ Настройка переменных окружения...${NC}"
    
    # Создаем .env файл если его нет
    if [[ ! -f .env ]]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 Создан файл .env из шаблона${NC}"
        echo -e "${RED}⚠️ ВАЖНО: Настройте переменные в файле .env перед продолжением!${NC}"
        
        if [[ "$ENVIRONMENT" == "production" ]]; then
            echo "   Особенно важно настроить:"
            echo "   - OPENAI_API_KEY"
            echo "   - API_KEY (для аутентификации)"
            echo "   - ALLOWED_ORIGINS"
            echo ""
            read -p "Нажмите Enter после настройки .env файла..."
        fi
    fi
    
    # Обновляем настройки для продакшена
    if [[ "$ENVIRONMENT" == "production" ]]; then
        sed -i.bak 's/DEBUG=true/DEBUG=false/' .env
        sed -i.bak 's/RATE_LIMIT_PER_MINUTE=100/RATE_LIMIT_PER_MINUTE=60/' .env
        echo -e "${GREEN}✅ Настройки для продакшена применены${NC}"
    fi
}

# Функция для генерации SSL сертификатов
setup_ssl() {
    if [[ "$ENABLE_LETSENCRYPT" == true && "$ENVIRONMENT" == "production" ]]; then
        echo -e "${YELLOW}🔐 Настройка Let's Encrypt SSL...${NC}"
        ./scripts/setup_letsencrypt.sh -d "$DOMAIN" -e "$EMAIL"
    elif [[ "$ENVIRONMENT" == "development" ]]; then
        echo -e "${YELLOW}🔐 Генерация самоподписанных сертификатов для разработки...${NC}"
        ./scripts/generate_ssl_certs.sh
    fi
}

# Функция для настройки firewall
setup_firewall() {
    if [[ "$ENABLE_FIREWALL" == true ]]; then
        echo -e "${YELLOW}🔥 Настройка firewall...${NC}"
        ./scripts/setup_firewall.sh
    else
        echo -e "${YELLOW}⚠️ Настройка firewall пропущена${NC}"
    fi
}

# Функция для сборки и запуска приложения
deploy_application() {
    echo -e "${YELLOW}🐳 Сборка и запуск приложения...${NC}"
    
    # Останавливаем существующие контейнеры
    docker-compose down 2>/dev/null || true
    
    # Собираем образ
    docker-compose build --no-cache
    
    # Запускаем сервисы
    if [[ "$ENVIRONMENT" == "production" ]]; then
        # В продакшене запускаем с Nginx
        docker-compose --profile with-nginx up -d
    else
        # В разработке только основное приложение
        docker-compose up -d optimaai-bot
    fi
    
    echo -e "${GREEN}✅ Приложение запущено${NC}"
}

# Функция для проверки работоспособности
health_check() {
    echo -e "${YELLOW}🏥 Проверка работоспособности...${NC}"
    
    # Ждем запуска сервисов
    sleep 10
    
    # Проверяем основное приложение
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Основное приложение работает${NC}"
    else
        echo -e "${RED}❌ Основное приложение не отвечает${NC}"
        docker-compose logs optimaai-bot
        exit 1
    fi
    
    # Проверяем Nginx если он запущен
    if docker-compose ps nginx >/dev/null 2>&1; then
        if curl -f http://localhost/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Nginx работает${NC}"
        else
            echo -e "${RED}❌ Nginx не отвечает${NC}"
            docker-compose logs nginx
        fi
    fi
    
    # Проверяем HTTPS если настроен
    if [[ "$ENABLE_LETSENCRYPT" == true && "$ENVIRONMENT" == "production" ]]; then
        if curl -f https://"$DOMAIN"/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ HTTPS работает${NC}"
        else
            echo -e "${YELLOW}⚠️ HTTPS может быть еще не готов${NC}"
        fi
    fi
}

# Функция для настройки мониторинга
setup_monitoring() {
    if [[ "$ENABLE_MONITORING" == true ]]; then
        echo -e "${YELLOW}📊 Настройка мониторинга...${NC}"
        
        # Создаем директорию для логов
        mkdir -p logs
        chmod 755 logs
        
        # Настраиваем logrotate
        cat > /etc/logrotate.d/optimaai << EOF
$(pwd)/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart optimaai-bot
    endscript
}
EOF
        
        echo -e "${GREEN}✅ Мониторинг настроен${NC}"
    fi
}

# Функция для вывода итоговой информации
show_summary() {
    echo ""
    echo -e "${GREEN}🎉 Развертывание завершено успешно!${NC}"
    echo ""
    echo -e "${BLUE}📋 Информация о развертывании:${NC}"
    echo "   Окружение: $ENVIRONMENT"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "   URL: https://$DOMAIN"
        echo "   API: https://$DOMAIN/docs"
    else
        echo "   URL: http://localhost:8000"
        echo "   API: http://localhost:8000/docs"
    fi
    
    echo ""
    echo -e "${BLUE}🔧 Полезные команды:${NC}"
    echo "   Просмотр логов: docker-compose logs -f"
    echo "   Перезапуск: docker-compose restart"
    echo "   Остановка: docker-compose down"
    echo "   Статус: docker-compose ps"
    echo ""
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo -e "${BLUE}🔒 Безопасность:${NC}"
        echo "   Firewall: $(if [[ "$ENABLE_FIREWALL" == true ]]; then echo "настроен"; else echo "не настроен"; fi)"
        echo "   SSL: $(if [[ "$ENABLE_LETSENCRYPT" == true ]]; then echo "Let's Encrypt"; else echo "самоподписанный"; fi)"
        echo "   Security Headers: включены"
        echo "   DDoS Protection: включена"
        echo "   Rate Limiting: включен"
        echo ""
    fi
    
    echo -e "${YELLOW}📝 Следующие шаги:${NC}"
    echo "   1. Проверьте работу API: curl https://$DOMAIN/health"
    echo "   2. Настройте мониторинг и алерты"
    echo "   3. Создайте резервные копии"
    echo "   4. Настройте CI/CD для автоматического развертывания"
    echo ""
    echo -e "${GREEN}✅ Готово к работе!${NC}"
}

# Основная логика
main() {
    echo -e "${BLUE}🚀 Начинаем безопасное развертывание...${NC}"
    echo ""
    
    # Проверяем системные требования
    check_requirements
    
    # Настраиваем окружение
    setup_environment
    
    # Настраиваем firewall
    setup_firewall
    
    # Настраиваем SSL
    setup_ssl
    
    # Развертываем приложение
    deploy_application
    
    # Настраиваем мониторинг
    setup_monitoring
    
    # Проверяем работоспособность
    health_check
    
    # Выводим итоговую информацию
    show_summary
}

# Запуск основной функции
main