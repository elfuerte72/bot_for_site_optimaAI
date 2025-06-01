#!/bin/bash

# Скрипт для генерации самоподписанных SSL сертификатов для разработки
# В продакшене используйте Let's Encrypt или корпоративные сертификаты

set -e

SSL_DIR="./ssl"
DAYS=365
COUNTRY="RU"
STATE="Moscow"
CITY="Moscow"
ORG="OptimaAI"
OU="IT Department"
CN="localhost"

echo "🔐 Генерация SSL сертификатов для разработки..."

# Создаем директорию для SSL если её нет
mkdir -p "$SSL_DIR"

# Генерируем приватный ключ
echo "📝 Генерация приватного ключа..."
openssl genrsa -out "$SSL_DIR/key.pem" 2048

# Генерируем сертификат
echo "📜 Генерация самоподписанного сертификата..."
openssl req -new -x509 -key "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" -days $DAYS -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=$CN"

# Генерируем DH параметры для Perfect Forward Secrecy
echo "🔑 Генерация DH параметров (это может занять несколько минут)..."
openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048

# Устанавливаем правильные права доступа
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"
chmod 644 "$SSL_DIR/dhparam.pem"

echo "✅ SSL сертификаты успешно созданы в директории $SSL_DIR"
echo ""
echo "📋 Информация о сертификате:"
openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -E "(Subject:|Not Before:|Not After:|DNS:|IP Address:)"

echo ""
echo "⚠️  ВНИМАНИЕ: Это самоподписанные сертификаты для разработки!"
echo "   В продакшене используйте сертификаты от доверенного CA (например, Let's Encrypt)"
echo ""
echo "🌐 Для использования в браузере добавьте сертификат в доверенные или игнорируйте предупреждение"