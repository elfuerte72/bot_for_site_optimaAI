#!/bin/bash

# Скрипт для настройки базовых правил firewall
# Поддерживает ufw (Ubuntu/Debian) и firewalld (CentOS/RHEL/Fedora)

set -e

echo "🔥 Настройка правил firewall для OptimaAI Bot..."

# Определяем тип системы и firewall
if command -v ufw >/dev/null 2>&1; then
    FIREWALL="ufw"
    echo "📋 Обнаружен UFW (Ubuntu/Debian)"
elif command -v firewall-cmd >/dev/null 2>&1; then
    FIREWALL="firewalld"
    echo "📋 Обнаружен firewalld (CentOS/RHEL/Fedora)"
else
    echo "❌ Не найден поддерживаемый firewall (ufw или firewalld)"
    echo "   Настройте правила firewall вручную:"
    echo "   - Разрешить порты: 22 (SSH), 80 (HTTP), 443 (HTTPS)"
    echo "   - Заблокировать все остальные входящие соединения"
    echo "   - Разрешить все исходящие соединения"
    exit 1
fi

# Функция для настройки UFW
setup_ufw() {
    echo "🔧 Настройка UFW..."
    
    # Сброс правил
    sudo ufw --force reset
    
    # Политики по умолчанию
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # SSH (важно разрешить до включения firewall!)
    sudo ufw allow 22/tcp comment 'SSH'
    
    # HTTP и HTTPS
    sudo ufw allow 80/tcp comment 'HTTP'
    sudo ufw allow 443/tcp comment 'HTTPS'
    
    # Разрешить loopback
    sudo ufw allow in on lo
    sudo ufw allow out on lo
    
    # Дополнительные правила безопасности
    # Защита от port scanning
    sudo ufw deny 23/tcp comment 'Block Telnet'
    sudo ufw deny 135/tcp comment 'Block RPC'
    sudo ufw deny 139/tcp comment 'Block NetBIOS'
    sudo ufw deny 445/tcp comment 'Block SMB'
    
    # Rate limiting для SSH
    sudo ufw limit ssh/tcp comment 'Rate limit SSH'
    
    # Включаем firewall
    sudo ufw --force enable
    
    echo "✅ UFW настроен и активирован"
}

# Функция для настройки firewalld
setup_firewalld() {
    echo "🔧 Настройка firewalld..."
    
    # Запускаем и включаем firewalld
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    
    # Устанавливаем зону по умолчанию
    sudo firewall-cmd --set-default-zone=public
    
    # Добавляем сервисы
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    
    # Дополнительные правила безопасности
    # Блокируем опасные порты
    sudo firewall-cmd --permanent --add-rich-rule='rule port port="23" protocol="tcp" reject'
    sudo firewall-cmd --permanent --add-rich-rule='rule port port="135" protocol="tcp" reject'
    sudo firewall-cmd --permanent --add-rich-rule='rule port port="139" protocol="tcp" reject'
    sudo firewall-cmd --permanent --add-rich-rule='rule port port="445" protocol="tcp" reject'
    
    # Перезагружаем правила
    sudo firewall-cmd --reload
    
    echo "✅ firewalld настроен и активирован"
}

# Проверяем права администратора
if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
    echo "❌ Этот скрипт требует права администратора (sudo)"
    echo "   Запустите: sudo $0"
    exit 1
fi

# Настраиваем соответствующий firewall
case $FIREWALL in
    "ufw")
        setup_ufw
        ;;
    "firewalld")
        setup_firewalld
        ;;
esac

echo ""
echo "🔍 Текущие правила firewall:"
case $FIREWALL in
    "ufw")
        sudo ufw status verbose
        ;;
    "firewalld")
        sudo firewall-cmd --list-all
        ;;
esac

echo ""
echo "✅ Настройка firewall завершена!"
echo ""
echo "📋 Разрешенные порты:"
echo "   - 22/tcp  : SSH"
echo "   - 80/tcp  : HTTP (редирект на HTTPS)"
echo "   - 443/tcp : HTTPS"
echo ""
echo "🔒 Все остальные входящие соединения заблокированы"
echo ""
echo "⚠️  ВАЖНО: Убедитесь, что SSH соединение работает перед отключением!"
echo "   Если потеряете доступ, используйте консоль сервера для восстановления"