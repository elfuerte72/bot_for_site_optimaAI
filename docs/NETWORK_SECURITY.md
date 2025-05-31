# Сетевая безопасность OptimaAI Bot

## Обзор

Данный документ описывает реализованные меры сетевой безопасности для OptimaAI Bot API, включая HTTPS, reverse proxy, firewall, security headers и защиту от DDoS атак.

## 🔒 Реализованные меры безопасности

### 1. HTTPS и SSL/TLS

#### Самоподписанные сертификаты (разработка)
```bash
# Генерация сертификатов для разработки
./scripts/generate_ssl_certs.sh
```

#### Let's Encrypt (продакшен)
```bash
# Настройка Let's Encrypt
sudo ./scripts/setup_letsencrypt.sh -d api.example.com -e admin@example.com
```

**Особенности SSL конфигурации:**
- Поддержка TLS 1.2 и TLS 1.3
- Современные cipher suites
- OCSP Stapling
- Perfect Forward Secrecy (DH параметры)
- HSTS с preload
- Автоматическое обновление сертификатов

### 2. Reverse Proxy (Nginx)

**Конфигурация:** `nginx.conf`

**Функции:**
- Терминация SSL
- Rate limiting
- Проксирование к приложению
- Статическая раздача файлов
- Кэширование
- Сжатие (gzip)

**Rate Limiting:**
- API: 10 запросов/сек с burst до 20
- Аутентификация: 1 запрос/сек с burst до 5
- Health checks: без ограничений

### 3. Firewall

**Скрипт настройки:** `./scripts/setup_firewall.sh`

**Поддерживаемые системы:**
- Ubuntu/Debian (ufw)
- CentOS/RHEL/Fedora (firewalld)

**Правила:**
- Разрешены: SSH (22), HTTP (80), HTTPS (443)
- Заблокированы: все остальные входящие соединения
- Защита от port scanning
- Rate limiting для SSH

```bash
# Настройка firewall
sudo ./scripts/setup_firewall.sh
```

### 4. Security Headers

**Middleware:** `SecurityHeadersMiddleware`

**Заголовки:**
- `Strict-Transport-Security` - HSTS
- `X-Frame-Options` - защита от clickjacking
- `X-Content-Type-Options` - предотвращение MIME sniffing
- `X-XSS-Protection` - защита от XSS
- `Referrer-Policy` - контроль referrer
- `Content-Security-Policy` - защита от injection атак
- `Permissions-Policy` - контроль API браузера

### 5. DDoS Protection

**Middleware:** `DDoSProtectionMiddleware`

**Функции:**
- Ограничение соединений с одного IP
- Детекция подозрительных паттернов
- Временная блокировка IP
- Whitelist для доверенных адресов
- Автоматическая очистка старых записей

**Настройки по умолчанию:**
- Максимум 20 соединений с IP
- Порог подозрительной активности: 100 запросов/минуту
- Время блокировки: 5 минут

## 🚀 Развертывание

### Быстрое развертывание

```bash
# Продакшен с полной безопасностью
sudo ./scripts/deploy_secure.sh -d api.example.com -e admin@example.com

# Разработка без SSL
./scripts/deploy_secure.sh -env development --no-ssl --no-firewall
```

### Ручное развертывание

1. **Настройка firewall:**
```bash
sudo ./scripts/setup_firewall.sh
```

2. **Генерация SSL сертификатов:**
```bash
# Для разработки
./scripts/generate_ssl_certs.sh

# Для продакшена
sudo ./scripts/setup_letsencrypt.sh -d yourdomain.com -e your@email.com
```

3. **Запуск с Nginx:**
```bash
docker-compose --profile with-nginx up -d
```

## 🔧 Конфигурация

### Переменные окружения

```env
# Основные настройки
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Безопасность
API_KEY=your-secure-api-key
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
RATE_LIMIT_PER_MINUTE=60

# SSL (для Let's Encrypt)
DOMAIN=yourdomain.com
EMAIL=admin@yourdomain.com
```

### Настройка CORS

```python
# В main.py
validated_origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://app.yourdomain.com"
]
```

### Настройка Rate Limiting

```python
# В middleware
app.add_middleware(
    RateLimitMiddleware,
    calls_per_minute=60  # Продакшен
)
```

## 🔍 Мониторинг и логирование

### Логи безопасности

**Файлы логов:**
- `app.log` - основные логи приложения
- `/var/log/nginx/access.log` - логи Nginx
- `/var/log/nginx/error.log` - ошибки Nginx

**Мониторинг атак:**
```bash
# Просмотр заблокированных IP
grep "DDoS Protection" app.log

# Анализ rate limiting
grep "Rate Limit" /var/log/nginx/access.log

# Подозрительная активность
grep "429" /var/log/nginx/access.log
```

### Метрики безопасности

**Эндпоинты:**
- `/security/status` - статус безопасности
- `/metrics` - метрики приложения
- `/health` - проверка работоспособности

```bash
# Проверка статуса безопасности
curl https://yourdomain.com/security/status
```

## 🛡️ Рекомендации по безопасности

### Обязательные меры

1. **Используйте сильные API ключи:**
```bash
# Генерация случайного ключа
openssl rand -hex 32
```

2. **Настройте CORS правильно:**
```python
# Только доверенные домены
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

3. **Регулярно обновляйте зависимости:**
```bash
pip list --outdated
pip install --upgrade package_name
```

4. **Мониторинг логов:**
```bash
# Настройка logrotate
sudo cp /etc/logrotate.d/optimaai /etc/logrotate.d/
```

### Дополнительные меры

1. **WAF (Web Application Firewall):**
   - Cloudflare
   - AWS WAF
   - ModSecurity

2. **Мониторинг:**
   - Prometheus + Grafana
   - ELK Stack
   - Datadog

3. **Backup и восстановление:**
```bash
# Backup конфигурации
tar -czf backup-$(date +%Y%m%d).tar.gz .env nginx.conf ssl/
```

## 🔧 Устранение неполадок

### Проблемы с SSL

```bash
# Проверка сертификата
openssl x509 -in ssl/cert.pem -text -noout

# Тест SSL соединения
openssl s_client -connect yourdomain.com:443

# Обновление Let's Encrypt
sudo certbot renew --dry-run
```

### Проблемы с Nginx

```bash
# Проверка конфигурации
nginx -t

# Просмотр логов
docker-compose logs nginx

# Перезагрузка конфигурации
docker-compose exec nginx nginx -s reload
```

### Проблемы с Firewall

```bash
# Статус UFW
sudo ufw status verbose

# Статус firewalld
sudo firewall-cmd --list-all

# Временное отключение (ОСТОРОЖНО!)
sudo ufw disable
sudo systemctl stop firewalld
```

## 📊 Тестирование безопасности

### Автоматические тесты

```bash
# Запуск тестов безопасности
python -m pytest tests/test_security.py -v

# Тест SSL конфигурации
./scripts/test_ssl.sh yourdomain.com

# Тест rate limiting
./scripts/test_rate_limit.sh
```

### Ручное тестирование

```bash
# Тест HTTPS
curl -I https://yourdomain.com

# Тест security headers
curl -I https://yourdomain.com | grep -E "(Strict-Transport|X-Frame|X-Content)"

# Тест rate limiting
for i in {1..100}; do curl https://yourdomain.com/health; done
```

### Внешние инструменты

- **SSL Labs:** https://www.ssllabs.com/ssltest/
- **Security Headers:** https://securityheaders.com/
- **Mozilla Observatory:** https://observatory.mozilla.org/

## 📝 Чек-лист развертывания

- [ ] ✅ **HTTPS настроен** (Let's Encrypt или корпоративные сертификаты)
- [ ] ✅ **Firewall правила настроены** (UFW/firewalld)
- [ ] ✅ **Reverse proxy настроен** (Nginx с SSL терминацией)
- [ ] ✅ **Security headers добавлены** (HSTS, CSP, X-Frame-Options и др.)
- [ ] ✅ **DDoS защита настроена** (Rate limiting, IP блокировка)
- [ ] ✅ **Мониторинг настроен** (Логи, метрики, алерты)
- [ ] ✅ **Автообновление сертификатов** (Cron job для Let's Encrypt)
- [ ] ✅ **Backup конфигурации** (Регулярные резервные копии)

## 🔗 Полезные ссылки

- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Security Guide](https://nginx.org/en/docs/http/securing_http.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Важно:** Регулярно обновляйте все компоненты системы и следите за новыми уязвимостями через CVE базы данных.