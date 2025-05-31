#!/bin/bash

# Скрипт для настройки Let's Encrypt SSL сертификатов
# Использует certbot для автоматического получения и обновления сертификатов

set -e

# Конфигурация
DOMAIN=""
EMAIL=""
WEBROOT_PATH="/var/www/html"
NGINX_CONF_PATH="/etc/nginx/sites-available/optimaai"
SSL_PATH="/etc/letsencrypt/live"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Настройка Let's Encrypt SSL сертификатов${NC}"
echo ""

# Функция для вывода справки
show_help() {
    echo "Использование: $0 -d DOMAIN -e EMAIL [опции]"
    echo ""
    echo "Обязательные параметры:"
    echo "  -d DOMAIN    Доменное имя (например, api.example.com)"
    echo "  -e EMAIL     Email для уведомлений Let's Encrypt"
    echo ""
    echo "Опциональные параметры:"
    echo "  -w PATH      Путь к webroot (по умолчанию: $WEBROOT_PATH)"
    echo "  -n PATH      Путь к конфигурации Nginx (по умолчанию: $NGINX_CONF_PATH)"
    echo "  -h           Показать эту справку"
    echo ""
    echo "Пример:"
    echo "  $0 -d api.example.com -e admin@example.com"
}

# Парсинг аргументов командной строки
while getopts "d:e:w:n:h" opt; do
    case $opt in
        d)
            DOMAIN="$OPTARG"
            ;;
        e)
            EMAIL="$OPTARG"
            ;;
        w)
            WEBROOT_PATH="$OPTARG"
            ;;
        n)
            NGINX_CONF_PATH="$OPTARG"
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo -e "${RED}Неверный параметр: -$OPTARG${NC}" >&2
            show_help
            exit 1
            ;;
    esac
done

# Проверка обязательных параметров
if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
    echo -e "${RED}❌ Ошибка: Не указаны обязательные параметры${NC}"
    show_help
    exit 1
fi

# Проверка прав администратора
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}❌ Этот скрипт требует права администратора (sudo)${NC}"
    echo "   Запустите: sudo $0 $@"
    exit 1
fi

echo -e "${YELLOW}📋 Конфигурация:${NC}"
echo "   Домен: $DOMAIN"
echo "   Email: $EMAIL"
echo "   Webroot: $WEBROOT_PATH"
echo "   Nginx конфиг: $NGINX_CONF_PATH"
echo ""

# Функция для установки certbot
install_certbot() {
    echo -e "${YELLOW}📦 Установка certbot...${NC}"
    
    if command -v apt-get >/dev/null 2>&1; then
        # Ubuntu/Debian
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    elif command -v yum >/dev/null 2>&1; then
        # CentOS/RHEL 7
        yum install -y epel-release
        yum install -y certbot python2-certbot-nginx
    elif command -v dnf >/dev/null 2>&1; then
        # CentOS/RHEL 8+/Fedora
        dnf install -y certbot python3-certbot-nginx
    else
        echo -e "${RED}❌ Неподдерживаемая система. Установите certbot вручную.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ certbot установлен${NC}"
}

# Функция для создания webroot директории
setup_webroot() {
    echo -e "${YELLOW}📁 Настройка webroot директории...${NC}"
    
    mkdir -p "$WEBROOT_PATH"
    chown -R www-data:www-data "$WEBROOT_PATH" 2>/dev/null || chown -R nginx:nginx "$WEBROOT_PATH" 2>/dev/null || true
    chmod 755 "$WEBROOT_PATH"
    
    # Создаем тестовый файл
    echo "Let's Encrypt verification" > "$WEBROOT_PATH/test.txt"
    
    echo -e "${GREEN}✅ Webroot настроен${NC}"
}

# Функция для создания временной конфигурации Nginx
create_temp_nginx_config() {
    echo -e "${YELLOW}⚙️ Создание временной конфигурации Nginx...${NC}"
    
    cat > "$NGINX_CONF_PATH" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root $WEBROOT_PATH;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    # Создаем символическую ссылку
    ln -sf "$NGINX_CONF_PATH" "/etc/nginx/sites-enabled/" 2>/dev/null || true
    
    # Тестируем и перезагружаем Nginx
    nginx -t
    systemctl reload nginx
    
    echo -e "${GREEN}✅ Временная конфигурация Nginx создана${NC}"
}

# Функция для получения сертификата
obtain_certificate() {
    echo -e "${YELLOW}🔐 Получение SSL сертификата...${NC}"
    
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT_PATH" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ SSL сертификат успешно получен${NC}"
    else
        echo -e "${RED}❌ Ошибка при получении сертификата${NC}"
        exit 1
    fi
}

# Функция для создания финальной конфигурации Nginx
create_final_nginx_config() {
    echo -e "${YELLOW}⚙️ Создание финальной конфигурации Nginx...${NC}"
    
    cat > "$NGINX_CONF_PATH" << EOF
# Редирект с HTTP на HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS сервер
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL конфигурация Let's Encrypt
    ssl_certificate $SSL_PATH/$DOMAIN/fullchain.pem;
    ssl_certificate_key $SSL_PATH/$DOMAIN/privkey.pem;
    
    # Современные SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate $SSL_PATH/$DOMAIN/chain.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    
    # Проксирование к приложению
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Let's Encrypt renewal
    location /.well-known/acme-challenge/ {
        root $WEBROOT_PATH;
    }
    
    # Health check без rate limiting
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }
}
EOF
    
    # Тестируем и перезагружаем Nginx
    nginx -t
    systemctl reload nginx
    
    echo -e "${GREEN}✅ Финальная конфигурация Nginx создана${NC}"
}

# Функция для настройки автообновления
setup_auto_renewal() {
    echo -e "${YELLOW}🔄 Настройка автообновления сертификатов...${NC}"
    
    # Создаем скрипт для обновления
    cat > /etc/cron.d/certbot-renewal << EOF
# Автообновление Let's Encrypt сертификатов
0 12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
    
    # Тестируем обновление
    certbot renew --dry-run
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Автообновление настроено${NC}"
    else
        echo -e "${YELLOW}⚠️ Предупреждение: Проблемы с настройкой автообновления${NC}"
    fi
}

# Основная логика
main() {
    echo -e "${YELLOW}🚀 Начинаем настройку Let's Encrypt...${NC}"
    echo ""
    
    # Проверяем, установлен ли certbot
    if ! command -v certbot >/dev/null 2>&1; then
        install_certbot
    else
        echo -e "${GREEN}✅ certbot уже установлен${NC}"
    fi
    
    # Настраиваем webroot
    setup_webroot
    
    # Создаем временную конфигурацию Nginx
    create_temp_nginx_config
    
    # Получаем сертификат
    obtain_certificate
    
    # Создаем финальную конфигурацию
    create_final_nginx_config
    
    # Настраиваем автообновление
    setup_auto_renewal
    
    echo ""
    echo -e "${GREEN}🎉 Let's Encrypt успешно настроен!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Информация о сертификате:${NC}"
    certbot certificates
    echo ""
    echo -e "${YELLOW}🔍 Проверьте ваш сайт:${NC}"
    echo "   https://$DOMAIN"
    echo ""
    echo -e "${YELLOW}📝 Полезные команды:${NC}"
    echo "   Проверить статус: certbot certificates"
    echo "   Обновить вручную: certbot renew"
    echo "   Тест обновления: certbot renew --dry-run"
    echo ""
    echo -e "${GREEN}✅ Настройка завершена!${NC}"
}

# Запуск основной функции
main