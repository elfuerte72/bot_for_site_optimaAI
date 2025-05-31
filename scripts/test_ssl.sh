#!/bin/bash

# Скрипт для тестирования SSL конфигурации
# Проверяет сертификаты, cipher suites, security headers и общую безопасность

set -e

DOMAIN=""
PORT=443
TIMEOUT=10
VERBOSE=false

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Тестирование SSL конфигурации${NC}"
echo ""

# Функция для вывода справки
show_help() {
    echo "Использование: $0 DOMAIN [опции]"
    echo ""
    echo "Параметры:"
    echo "  DOMAIN           Доменное имя для тестирования"
    echo ""
    echo "Опции:"
    echo "  -p, --port PORT  Порт для подключения (по умолчанию: 443)"
    echo "  -t, --timeout N  Таймаут подключения в секундах (по умолчанию: 10)"
    echo "  -v, --verbose    Подробный вывод"
    echo "  -h, --help       Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 example.com"
    echo "  $0 api.example.com -p 8443 -v"
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Неизвестная опция: $1${NC}"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$DOMAIN" ]]; then
                DOMAIN="$1"
            else
                echo -e "${RED}Слишком много аргументов${NC}"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Проверка обязательных параметров
if [[ -z "$DOMAIN" ]]; then
    echo -e "${RED}❌ Не указан домен${NC}"
    show_help
    exit 1
fi

echo -e "${BLUE}📋 Конфигурация тестирования:${NC}"
echo "   Домен: $DOMAIN"
echo "   Порт: $PORT"
echo "   Таймаут: $TIMEOUT сек"
echo "   Подробный вывод: $VERBOSE"
echo ""

# Функция для проверки доступности инструментов
check_tools() {
    local missing_tools=()
    
    if ! command -v openssl >/dev/null 2>&1; then
        missing_tools+=("openssl")
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_tools+=("curl")
    fi
    
    if ! command -v nmap >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ nmap не установлен - некоторые тесты будут пропущены${NC}"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Отсутствуют необходимые инструменты: ${missing_tools[*]}${NC}"
        echo "   Установите их перед запуском тестов"
        exit 1
    fi
}

# Функция для тестирования подключения
test_connection() {
    echo -e "${YELLOW}🔌 Тестирование подключения...${NC}"
    
    if timeout $TIMEOUT bash -c "</dev/tcp/$DOMAIN/$PORT" 2>/dev/null; then
        echo -e "${GREEN}✅ Подключение к $DOMAIN:$PORT успешно${NC}"
        return 0
    else
        echo -e "${RED}❌ Не удается подключиться к $DOMAIN:$PORT${NC}"
        return 1
    fi
}

# Функция для проверки сертификата
test_certificate() {
    echo -e "${YELLOW}📜 Проверка SSL сертификата...${NC}"
    
    local cert_info
    cert_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:$PORT" 2>/dev/null | openssl x509 -noout -text 2>/dev/null)
    
    if [[ -z "$cert_info" ]]; then
        echo -e "${RED}❌ Не удается получить информацию о сертификате${NC}"
        return 1
    fi
    
    # Проверяем срок действия
    local expiry_date
    expiry_date=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:$PORT" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    
    if [[ -n "$expiry_date" ]]; then
        local expiry_timestamp
        expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry_date" +%s 2>/dev/null)
        local current_timestamp
        current_timestamp=$(date +%s)
        local days_until_expiry
        days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_until_expiry -gt 30 ]]; then
            echo -e "${GREEN}✅ Сертификат действителен (истекает через $days_until_expiry дней)${NC}"
        elif [[ $days_until_expiry -gt 0 ]]; then
            echo -e "${YELLOW}⚠️ Сертификат скоро истечет (через $days_until_expiry дней)${NC}"
        else
            echo -e "${RED}❌ Сертификат истек${NC}"
        fi
    fi
    
    # Проверяем Subject Alternative Names
    local san
    san=$(echo "$cert_info" | grep -A1 "Subject Alternative Name" | tail -1 | sed 's/^[[:space:]]*//')
    
    if [[ -n "$san" ]]; then
        echo -e "${GREEN}✅ SAN найден: $san${NC}"
        
        if echo "$san" | grep -q "$DOMAIN"; then
            echo -e "${GREEN}✅ Домен $DOMAIN найден в SAN${NC}"
        else
            echo -e "${YELLOW}⚠️ Домен $DOMAIN не найден в SAN${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Subject Alternative Names не найдены${NC}"
    fi
    
    # Проверяем алгоритм подписи
    local signature_algorithm
    signature_algorithm=$(echo "$cert_info" | grep "Signature Algorithm" | head -1 | awk '{print $3}')
    
    if [[ "$signature_algorithm" == "sha256WithRSAEncryption" ]] || [[ "$signature_algorithm" == "ecdsa-with-SHA256" ]]; then
        echo -e "${GREEN}✅ Безопасный алгоритм подписи: $signature_algorithm${NC}"
    else
        echo -e "${YELLOW}⚠️ Алгоритм подписи: $signature_algorithm${NC}"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}📋 Детали сертификата:${NC}"
        echo "$cert_info" | grep -E "(Subject:|Issuer:|Not Before:|Not After:|Public Key Algorithm:|RSA Public-Key:|Subject Alternative Name)" | sed 's/^/   /'
    fi
}

# Функция для проверки SSL/TLS протоколов
test_protocols() {
    echo -e "${YELLOW}🔒 Проверка поддерживаемых протоколов...${NC}"
    
    local protocols=("ssl3" "tls1" "tls1_1" "tls1_2" "tls1_3")
    local secure_protocols=()
    local insecure_protocols=()
    
    for protocol in "${protocols[@]}"; do
        if echo | openssl s_client -"$protocol" -connect "$DOMAIN:$PORT" 2>/dev/null | grep -q "Verify return code: 0"; then
            case $protocol in
                "tls1_2"|"tls1_3")
                    secure_protocols+=("$protocol")
                    ;;
                *)
                    insecure_protocols+=("$protocol")
                    ;;
            esac
        fi
    done
    
    if [[ ${#secure_protocols[@]} -gt 0 ]]; then
        echo -e "${GREEN}✅ Поддерживаемые безопасные протоколы: ${secure_protocols[*]}${NC}"
    fi
    
    if [[ ${#insecure_protocols[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Поддерживаемые небезопасные протоколы: ${insecure_protocols[*]}${NC}"
        echo -e "${YELLOW}   Рекомендуется отключить: ${insecure_protocols[*]}${NC}"
    else
        echo -e "${GREEN}✅ Небезопасные протоколы отключены${NC}"
    fi
}

# Функция для проверки cipher suites
test_cipher_suites() {
    echo -e "${YELLOW}🔐 Проверка cipher suites...${NC}"
    
    local cipher_info
    cipher_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:$PORT" -cipher 'ALL:!aNULL:!eNULL' 2>/dev/null | grep "Cipher")
    
    if [[ -n "$cipher_info" ]]; then
        local cipher
        cipher=$(echo "$cipher_info" | awk '{print $3}')
        echo -e "${GREEN}✅ Используемый cipher: $cipher${NC}"
        
        # Проверяем на слабые cipher suites
        if echo "$cipher" | grep -qE "(RC4|DES|MD5|NULL)"; then
            echo -e "${RED}❌ Обнаружен слабый cipher suite${NC}"
        elif echo "$cipher" | grep -qE "(AES256|CHACHA20)"; then
            echo -e "${GREEN}✅ Используется сильный cipher suite${NC}"
        fi
    fi
    
    # Проверяем Perfect Forward Secrecy
    local pfs_info
    pfs_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:$PORT" 2>/dev/null | grep -E "(ECDHE|DHE)")
    
    if [[ -n "$pfs_info" ]]; then
        echo -e "${GREEN}✅ Perfect Forward Secrecy поддерживается${NC}"
    else
        echo -e "${YELLOW}⚠️ Perfect Forward Secrecy не обнаружен${NC}"
    fi
}

# Функция для проверки security headers
test_security_headers() {
    echo -e "${YELLOW}🛡️ Проверка security headers...${NC}"
    
    local headers
    headers=$(curl -s -I "https://$DOMAIN:$PORT/" --connect-timeout $TIMEOUT 2>/dev/null)
    
    if [[ -z "$headers" ]]; then
        echo -e "${RED}❌ Не удается получить HTTP headers${NC}"
        return 1
    fi
    
    # Список важных security headers
    local security_headers=(
        "Strict-Transport-Security"
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Referrer-Policy"
        "Content-Security-Policy"
        "Permissions-Policy"
    )
    
    local found_headers=0
    
    for header in "${security_headers[@]}"; do
        if echo "$headers" | grep -qi "^$header:"; then
            echo -e "${GREEN}✅ $header найден${NC}"
            ((found_headers++))
            
            if [[ "$VERBOSE" == true ]]; then
                local value
                value=$(echo "$headers" | grep -i "^$header:" | cut -d: -f2- | sed 's/^[[:space:]]*//')
                echo -e "${BLUE}   Значение: $value${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ $header отсутствует${NC}"
        fi
    done
    
    echo -e "${BLUE}📊 Найдено security headers: $found_headers/${#security_headers[@]}${NC}"
    
    # Проверяем HSTS
    local hsts
    hsts=$(echo "$headers" | grep -i "^Strict-Transport-Security:" | cut -d: -f2- | sed 's/^[[:space:]]*//')
    
    if [[ -n "$hsts" ]]; then
        if echo "$hsts" | grep -q "includeSubDomains"; then
            echo -e "${GREEN}✅ HSTS включает поддомены${NC}"
        else
            echo -e "${YELLOW}⚠️ HSTS не включает поддомены${NC}"
        fi
        
        if echo "$hsts" | grep -q "preload"; then
            echo -e "${GREEN}✅ HSTS preload включен${NC}"
        else
            echo -e "${YELLOW}⚠️ HSTS preload не включен${NC}"
        fi
    fi
}

# Функция для проверки уязвимостей
test_vulnerabilities() {
    echo -e "${YELLOW}🔍 Проверка известных уязвимостей...${NC}"
    
    # Проверка Heartbleed
    local heartbleed_test
    heartbleed_test=$(echo | openssl s_client -connect "$DOMAIN:$PORT" -tlsextdebug 2>&1 | grep -i heartbeat)
    
    if [[ -z "$heartbleed_test" ]]; then
        echo -e "${GREEN}✅ Heartbleed: не уязвим${NC}"
    else
        echo -e "${YELLOW}⚠️ Heartbleed: требует дополнительной проверки${NC}"
    fi
    
    # Проверка POODLE (SSLv3)
    if echo | openssl s_client -ssl3 -connect "$DOMAIN:$PORT" 2>/dev/null | grep -q "Verify return code: 0"; then
        echo -e "${RED}❌ POODLE: уязвим (SSLv3 включен)${NC}"
    else
        echo -e "${GREEN}✅ POODLE: не уязвим (SSLv3 отключен)${NC}"
    fi
    
    # Проверка BEAST (TLS 1.0)
    if echo | openssl s_client -tls1 -connect "$DOMAIN:$PORT" 2>/dev/null | grep -q "Verify return code: 0"; then
        echo -e "${YELLOW}⚠️ BEAST: потенциально уязвим (TLS 1.0 включен)${NC}"
    else
        echo -e "${GREEN}✅ BEAST: не уязвим (TLS 1.0 отключен)${NC}"
    fi
}

# Функция для проверки с помощью nmap
test_with_nmap() {
    if command -v nmap >/dev/null 2>&1; then
        echo -e "${YELLOW}🔎 Дополнительная проверка с nmap...${NC}"
        
        local nmap_result
        nmap_result=$(nmap --script ssl-enum-ciphers -p "$PORT" "$DOMAIN" 2>/dev/null)
        
        if [[ -n "$nmap_result" ]]; then
            # Проверяем общую оценку
            local grade
            grade=$(echo "$nmap_result" | grep -o "least strength: [A-F]" | cut -d: -f2 | tr -d ' ')
            
            if [[ -n "$grade" ]]; then
                case $grade in
                    A|A+)
                        echo -e "${GREEN}✅ Общая оценка SSL: $grade${NC}"
                        ;;
                    B|C)
                        echo -e "${YELLOW}⚠️ Общая оценка SSL: $grade${NC}"
                        ;;
                    D|F)
                        echo -e "${RED}❌ Общая оценка SSL: $grade${NC}"
                        ;;
                esac
            fi
            
            if [[ "$VERBOSE" == true ]]; then
                echo -e "${BLUE}📋 Детали nmap:${NC}"
                echo "$nmap_result" | grep -E "(TLSv|SSLv|Cipher)" | sed 's/^/   /'
            fi
        fi
    fi
}

# Функция для генерации отчета
generate_report() {
    echo ""
    echo -e "${GREEN}📊 Сводка тестирования SSL для $DOMAIN:$PORT${NC}"
    echo "=================================================="
    
    # Здесь можно добавить сводную информацию
    echo -e "${BLUE}🔗 Рекомендации для дополнительной проверки:${NC}"
    echo "   • SSL Labs: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    echo "   • Security Headers: https://securityheaders.com/?q=https://$DOMAIN"
    echo "   • Mozilla Observatory: https://observatory.mozilla.org/analyze/$DOMAIN"
    echo ""
    
    echo -e "${YELLOW}📝 Рекомендации по улучшению:${NC}"
    echo "   • Используйте только TLS 1.2 и TLS 1.3"
    echo "   • Настройте все security headers"
    echo "   • Включите HSTS с preload"
    echo "   • Используйте сильные cipher suites"
    echo "   • Настройте Perfect Forward Secrecy"
    echo "   • Регулярно обновляйте сертификаты"
}

# Основная функция
main() {
    check_tools
    
    if ! test_connection; then
        exit 1
    fi
    
    test_certificate
    test_protocols
    test_cipher_suites
    test_security_headers
    test_vulnerabilities
    test_with_nmap
    
    generate_report
    
    echo ""
    echo -e "${GREEN}✅ Тестирование SSL завершено${NC}"
}

# Запуск основной функции
main