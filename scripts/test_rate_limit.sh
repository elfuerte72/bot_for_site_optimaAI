#!/bin/bash

# Скрипт для тестирования rate limiting и DDoS защиты
# Проверяет ограничения скорости запросов и блокировку IP

set -e

URL="http://localhost:8000"
ENDPOINT="/health"
REQUESTS_COUNT=100
CONCURRENT_REQUESTS=10
DELAY=0.1
API_KEY=""
VERBOSE=false

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}⚡ Тестирование Rate Limiting и DDoS защиты${NC}"
echo ""

# Функция для вывода справки
show_help() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -u, --url URL        Базовый URL сервера (по умолчанию: $URL)"
    echo "  -e, --endpoint PATH  Endpoint для тестирования (по умолчанию: $ENDPOINT)"
    echo "  -n, --requests N     Количество запросов (по умолчанию: $REQUESTS_COUNT)"
    echo "  -c, --concurrent N   Параллельные запросы (по умолчанию: $CONCURRENT_REQUESTS)"
    echo "  -d, --delay SEC      Задержка между запросами (по умолчанию: $DELAY)"
    echo "  -k, --api-key KEY    API ключ для аутентификации"
    echo "  -v, --verbose        Подробный вывод"
    echo "  -h, --help           Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0                                    # Базовое тестирование"
    echo "  $0 -u https://api.example.com -n 200 # Тест продакшен сервера"
    echo "  $0 -e /chat -k your-api-key -v       # Тест защищенного endpoint"
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            URL="$2"
            shift 2
            ;;
        -e|--endpoint)
            ENDPOINT="$2"
            shift 2
            ;;
        -n|--requests)
            REQUESTS_COUNT="$2"
            shift 2
            ;;
        -c|--concurrent)
            CONCURRENT_REQUESTS="$2"
            shift 2
            ;;
        -d|--delay)
            DELAY="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
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
        *)
            echo -e "${RED}Неизвестная опция: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

FULL_URL="$URL$ENDPOINT"

echo -e "${BLUE}📋 Конфигурация тестирования:${NC}"
echo "   URL: $FULL_URL"
echo "   Количество запросов: $REQUESTS_COUNT"
echo "   Параллельные запросы: $CONCURRENT_REQUESTS"
echo "   Задержка: $DELAY сек"
echo "   API ключ: $(if [[ -n "$API_KEY" ]]; then echo "настроен"; else echo "не настроен"; fi)"
echo "   Подробный вывод: $VERBOSE"
echo ""

# Функция для проверки доступности инструментов
check_tools() {
    local missing_tools=()
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_tools+=("curl")
    fi
    
    if ! command -v bc >/dev/null 2>&1; then
        missing_tools+=("bc")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Отсутствуют необходимые инструменты: ${missing_tools[*]}${NC}"
        echo "   Установите их перед запуском тестов"
        exit 1
    fi
}

# Функция для проверки доступности сервера
test_server_availability() {
    echo -e "${YELLOW}🔌 Проверка доступности сервера...${NC}"
    
    local headers=""
    if [[ -n "$API_KEY" ]]; then
        headers="-H \"X-API-Key: $API_KEY\""
    fi
    
    if eval curl -s -f $headers "$FULL_URL" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Сервер доступен${NC}"
        return 0
    else
        echo -e "${RED}❌ Сервер недоступен: $FULL_URL${NC}"
        return 1
    fi
}

# Функция для одиночного запроса
make_request() {
    local request_id="$1"
    local headers=""
    
    if [[ -n "$API_KEY" ]]; then
        headers="-H \"X-API-Key: $API_KEY\""
    fi
    
    local start_time
    start_time=$(date +%s.%N)
    
    local response
    local status_code
    local response_time
    
    response=$(eval curl -s -w "%{http_code}|%{time_total}" $headers "$FULL_URL" 2>/dev/null)
    status_code=$(echo "$response" | tail -1 | cut -d'|' -f1)
    response_time=$(echo "$response" | tail -1 | cut -d'|' -f2)
    
    local end_time
    end_time=$(date +%s.%N)
    local total_time
    total_time=$(echo "$end_time - $start_time" | bc)
    
    if [[ "$VERBOSE" == true ]]; then
        echo "Request $request_id: Status=$status_code, Time=${response_time}s"
    fi
    
    echo "$request_id|$status_code|$response_time|$total_time"
}

# Функция для последовательного тестирования
test_sequential_requests() {
    echo -e "${YELLOW}📈 Тестирование последовательных запросов...${NC}"
    
    local success_count=0
    local rate_limited_count=0
    local error_count=0
    local total_time=0
    
    local start_time
    start_time=$(date +%s.%N)
    
    for ((i=1; i<=REQUESTS_COUNT; i++)); do
        local result
        result=$(make_request "$i")
        
        local status_code
        status_code=$(echo "$result" | cut -d'|' -f2)
        
        local response_time
        response_time=$(echo "$result" | cut -d'|' -f3)
        total_time=$(echo "$total_time + $response_time" | bc)
        
        case $status_code in
            200)
                ((success_count++))
                ;;
            429)
                ((rate_limited_count++))
                if [[ "$VERBOSE" == true ]]; then
                    echo -e "${YELLOW}⚠️ Request $i: Rate limited${NC}"
                fi
                ;;
            *)
                ((error_count++))
                if [[ "$VERBOSE" == true ]]; then
                    echo -e "${RED}❌ Request $i: Error $status_code${NC}"
                fi
                ;;
        esac
        
        # Показываем прогресс каждые 10 запросов
        if [[ $((i % 10)) -eq 0 ]] && [[ "$VERBOSE" != true ]]; then
            echo -n "."
        fi
        
        sleep "$DELAY"
    done
    
    local end_time
    end_time=$(date +%s.%N)
    local test_duration
    test_duration=$(echo "$end_time - $start_time" | bc)
    
    echo ""
    echo -e "${BLUE}📊 Результаты последовательного тестирования:${NC}"
    echo "   Успешные запросы: $success_count"
    echo "   Rate limited: $rate_limited_count"
    echo "   Ошибки: $error_count"
    echo "   Общее время: ${test_duration}s"
    echo "   Среднее время ответа: $(echo "scale=3; $total_time / $REQUESTS_COUNT" | bc)s"
    echo "   Запросов в секунду: $(echo "scale=2; $REQUESTS_COUNT / $test_duration" | bc)"
    
    if [[ $rate_limited_count -gt 0 ]]; then
        echo -e "${GREEN}✅ Rate limiting работает (заблокировано $rate_limited_count запросов)${NC}"
    else
        echo -e "${YELLOW}⚠️ Rate limiting не сработал или лимит слишком высокий${NC}"
    fi
}

# Функция для параллельного тестирования
test_concurrent_requests() {
    echo -e "${YELLOW}⚡ Тестирование параллельных запросов...${NC}"
    
    local temp_dir
    temp_dir=$(mktemp -d)
    local pids=()
    
    local start_time
    start_time=$(date +%s.%N)
    
    # Запускаем параллельные запросы
    for ((i=1; i<=CONCURRENT_REQUESTS; i++)); do
        (
            local batch_size=$((REQUESTS_COUNT / CONCURRENT_REQUESTS))
            local start_id=$(((i-1) * batch_size + 1))
            local end_id=$((i * batch_size))
            
            for ((j=start_id; j<=end_id; j++)); do
                make_request "$j" >> "$temp_dir/results_$i.txt"
                sleep 0.01  # Минимальная задержка
            done
        ) &
        pids+=($!)
    done
    
    # Ждем завершения всех процессов
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    local end_time
    end_time=$(date +%s.%N)
    local test_duration
    test_duration=$(echo "$end_time - $start_time" | bc)
    
    # Анализируем результаты
    local success_count=0
    local rate_limited_count=0
    local error_count=0
    
    for file in "$temp_dir"/results_*.txt; do
        if [[ -f "$file" ]]; then
            while IFS='|' read -r request_id status_code response_time total_time; do
                case $status_code in
                    200)
                        ((success_count++))
                        ;;
                    429)
                        ((rate_limited_count++))
                        ;;
                    *)
                        ((error_count++))
                        ;;
                esac
            done < "$file"
        fi
    done
    
    # Очищаем временные файлы
    rm -rf "$temp_dir"
    
    echo -e "${BLUE}📊 Результаты параллельного тестирования:${NC}"
    echo "   Успешные запросы: $success_count"
    echo "   Rate limited: $rate_limited_count"
    echo "   Ошибки: $error_count"
    echo "   Общее время: ${test_duration}s"
    echo "   Запросов в секунду: $(echo "scale=2; $REQUESTS_COUNT / $test_duration" | bc)"
    
    if [[ $rate_limited_count -gt 0 ]]; then
        echo -e "${GREEN}✅ DDoS защита работает (заблокировано $rate_limited_count запросов)${NC}"
    else
        echo -e "${YELLOW}⚠️ DDoS защита не сработала или лимит слишком высокий${NC}"
    fi
}

# Функция для тестирования burst запросов
test_burst_requests() {
    echo -e "${YELLOW}💥 Тестирование burst запросов...${NC}"
    
    local burst_size=20
    local success_count=0
    local rate_limited_count=0
    
    echo "   Отправка $burst_size запросов без задержки..."
    
    for ((i=1; i<=burst_size; i++)); do
        local result
        result=$(make_request "burst_$i")
        
        local status_code
        status_code=$(echo "$result" | cut -d'|' -f2)
        
        case $status_code in
            200)
                ((success_count++))
                ;;
            429)
                ((rate_limited_count++))
                ;;
        esac
    done
    
    echo -e "${BLUE}📊 Результаты burst тестирования:${NC}"
    echo "   Успешные запросы: $success_count"
    echo "   Rate limited: $rate_limited_count"
    
    if [[ $rate_limited_count -gt 0 ]]; then
        echo -e "${GREEN}✅ Burst защита работает${NC}"
    else
        echo -e "${YELLOW}⚠️ Burst защита не сработала${NC}"
    fi
}

# Функция для тестирования восстановления после блокировки
test_recovery_after_blocking() {
    echo -e "${YELLOW}🔄 Тестирование восстановления после блокировки...${NC}"
    
    # Сначала вызываем блокировку
    echo "   Вызываем блокировку..."
    for ((i=1; i<=50; i++)); do
        make_request "block_$i" >/dev/null
    done
    
    # Проверяем, что заблокированы
    local result
    result=$(make_request "check_block")
    local status_code
    status_code=$(echo "$result" | cut -d'|' -f2)
    
    if [[ $status_code -eq 429 ]]; then
        echo -e "${GREEN}✅ IP успешно заблокирован${NC}"
        
        # Ждем некоторое время
        echo "   Ожидание 10 секунд для восстановления..."
        sleep 10
        
        # Проверяем восстановление
        result=$(make_request "check_recovery")
        status_code=$(echo "$result" | cut -d'|' -f2)
        
        if [[ $status_code -eq 200 ]]; then
            echo -e "${GREEN}✅ Восстановление после блокировки работает${NC}"
        else
            echo -e "${YELLOW}⚠️ Восстановление может занять больше времени${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Блокировка не сработала или лимит слишком высокий${NC}"
    fi
}

# Функция для анализа заголовков rate limiting
analyze_rate_limit_headers() {
    echo -e "${YELLOW}📋 Анализ заголовков rate limiting...${NC}"
    
    local headers=""
    if [[ -n "$API_KEY" ]]; then
        headers="-H \"X-API-Key: $API_KEY\""
    fi
    
    local response_headers
    response_headers=$(eval curl -s -I $headers "$FULL_URL" 2>/dev/null)
    
    if [[ -n "$response_headers" ]]; then
        echo -e "${BLUE}📊 Найденные заголовки:${NC}"
        
        # Ищем заголовки rate limiting
        local rate_limit_headers=(
            "X-RateLimit-Limit"
            "X-RateLimit-Remaining"
            "X-RateLimit-Reset"
            "Retry-After"
            "X-Rate-Limit"
        )
        
        for header in "${rate_limit_headers[@]}"; do
            local value
            value=$(echo "$response_headers" | grep -i "^$header:" | cut -d: -f2- | sed 's/^[[:space:]]*//')
            
            if [[ -n "$value" ]]; then
                echo -e "${GREEN}✅ $header: $value${NC}"
            fi
        done
        
        # Проверяем другие полезные заголовки
        local security_headers=(
            "X-Security-Headers"
            "X-Process-Time"
        )
        
        for header in "${security_headers[@]}"; do
            local value
            value=$(echo "$response_headers" | grep -i "^$header:" | cut -d: -f2- | sed 's/^[[:space:]]*//')
            
            if [[ -n "$value" ]]; then
                echo -e "${BLUE}ℹ️ $header: $value${NC}"
            fi
        done
    fi
}

# Функция для генерации отчета
generate_report() {
    echo ""
    echo -e "${GREEN}📊 Сводка тестирования Rate Limiting${NC}"
    echo "=================================================="
    echo -e "${BLUE}🎯 Цель тестирования:${NC}"
    echo "   Проверить работу rate limiting и DDoS защиты"
    echo ""
    echo -e "${BLUE}🔧 Рекомендации:${NC}"
    echo "   • Настройте rate limiting в соответствии с нагрузкой"
    echo "   • Используйте whitelist для доверенных IP"
    echo "   • Мониторьте заблокированные запросы"
    echo "   • Настройте алерты на превышение лимитов"
    echo "   • Регулярно тестируйте защиту"
    echo ""
    echo -e "${YELLOW}📝 Следующие шаги:${NC}"
    echo "   1. Проанализируйте логи сервера"
    echo "   2. Настройте мониторинг rate limiting"
    echo "   3. Протестируйте с разных IP адресов"
    echo "   4. Настройте алерты на DDoS атаки"
}

# Основная функция
main() {
    check_tools
    
    if ! test_server_availability; then
        exit 1
    fi
    
    analyze_rate_limit_headers
    test_sequential_requests
    test_burst_requests
    test_concurrent_requests
    test_recovery_after_blocking
    
    generate_report
    
    echo ""
    echo -e "${GREEN}✅ Тестирование Rate Limiting завершено${NC}"
}

# Запуск основной функции
main