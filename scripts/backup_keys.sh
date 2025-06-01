#!/bin/bash

# Скрипт для резервного копирования критичных ключей и конфигураций
# Использование: ./backup_keys.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Проверка, что скрипт запущен из корневой директории проекта
if [ ! -f ".env" ]; then
    error "Файл .env не найден. Запустите скрипт из корневой директории проекта."
    exit 1
fi

# Создание директории для backup'ов
BACKUP_DIR="backups/$(date +'%Y-%m-%d_%H-%M-%S')"
mkdir -p "$BACKUP_DIR"

log "Создание резервной копии в директории: $BACKUP_DIR"

# Backup .env файла (без секретных данных)
log "Создание backup конфигурации..."
cp .env.example "$BACKUP_DIR/env.example.backup"

# Создание зашифрованного backup'а .env файла
if command -v gpg &> /dev/null; then
    log "Создание зашифрованного backup'а .env файла..."
    gpg --symmetric --cipher-algo AES256 --output "$BACKUP_DIR/env.encrypted.gpg" .env
    log "Зашифрованный backup создан: $BACKUP_DIR/env.encrypted.gpg"
else
    warn "GPG не установлен. Создание незашифрованного backup'а..."
    cp .env "$BACKUP_DIR/env.backup"
    warn "ВНИМАНИЕ: Backup содержит секретные данные в открытом виде!"
fi

# Backup конфигурационных файлов
log "Создание backup конфигурационных файлов..."
cp docker-compose.yml "$BACKUP_DIR/"
cp Dockerfile "$BACKUP_DIR/"
cp requirements.txt "$BACKUP_DIR/"

if [ -f "pyproject.toml" ]; then
    cp pyproject.toml "$BACKUP_DIR/"
fi

# Создание манифеста backup'а
log "Создание манифеста backup'а..."
cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
# Backup Manifest
# Дата создания: $(date)
# Версия проекта: OptimaAI Bot v2.0.0

## Содержимое backup'а:
- env.example.backup - Пример конфигурации
- env.encrypted.gpg - Зашифрованный .env файл (если GPG доступен)
- env.backup - Незашифрованный .env файл (если GPG недоступен)
- docker-compose.yml - Docker Compose конфигурация
- Dockerfile - Docker образ конфигурация
- requirements.txt - Python зависимости
- pyproject.toml - Конфигурация проекта (если есть)

## Восстановление:
1. Для восстановления зашифрованного .env:
   gpg --decrypt env.encrypted.gpg > .env

2. Для восстановления незашифрованного .env:
   cp env.backup .env

## Безопасность:
- Храните backup в безопасном месте
- Не передавайте backup по незащищенным каналам
- Регулярно проверяйте целостность backup'ов
EOF

# Создание контрольной суммы
log "Создание контрольных сумм..."
cd "$BACKUP_DIR"
find . -type f -exec sha256sum {} \; > checksums.sha256
cd - > /dev/null

log "Backup успешно создан в: $BACKUP_DIR"
log "Размер backup'а: $(du -sh "$BACKUP_DIR" | cut -f1)"

# Показать содержимое backup'а
log "Содержимое backup'а:"
ls -la "$BACKUP_DIR"

# Рекомендации по безопасности
echo ""
warn "РЕКОМЕНДАЦИИ ПО БЕЗОПАСНОСТИ:"
warn "1. Переместите backup в безопасное место (внешний диск, облако с шифрованием)"
warn "2. Не храните backup'ы в той же системе, что и рабочие ключи"
warn "3. Регулярно тестируйте процедуру восстановления"
warn "4. Установите напоминание для регулярного создания backup'ов"

echo ""
log "Backup завершен успешно!"