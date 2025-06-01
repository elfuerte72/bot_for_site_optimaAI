# 🔑 ПРОЦЕДУРА ВОССТАНОВЛЕНИЯ КЛЮЧЕЙ

## 📋 ОБЗОР

Данный документ описывает процедуры резервного копирования и восстановления критичных API ключей и секретов для OptimaAI Bot.

## 🔄 СОЗДАНИЕ BACKUP'А

### Автоматический backup
```bash
# Запуск скрипта backup'а
./scripts/backup_keys.sh
```

### Ручной backup
```bash
# Создание директории
mkdir -p backups/manual-$(date +'%Y-%m-%d')

# Зашифрованный backup .env файла
gpg --symmetric --cipher-algo AES256 --output backups/manual-$(date +'%Y-%m-%d')/env.encrypted.gpg .env

# Backup конфигураций
cp .env.example docker-compose.yml Dockerfile requirements.txt backups/manual-$(date +'%Y-%m-%d')/
```

## 🔧 ВОССТАНОВЛЕНИЕ КЛЮЧЕЙ

### 1. Восстановление из зашифрованного backup'а
```bash
# Расшифровка .env файла
gpg --decrypt backups/YYYY-MM-DD_HH-MM-SS/env.encrypted.gpg > .env

# Проверка содержимого
cat .env | grep -E "^[A-Z_]+=.*" | head -5
```

### 2. Восстановление из незашифрованного backup'а
```bash
# Копирование файла
cp backups/YYYY-MM-DD_HH-MM-SS/env.backup .env

# Установка правильных прав доступа
chmod 600 .env
```

### 3. Проверка целостности
```bash
# Проверка контрольных сумм
cd backups/YYYY-MM-DD_HH-MM-SS/
sha256sum -c checksums.sha256
```

## 🧪 ТЕСТИРОВАНИЕ ВОССТАНОВЛЕНИЯ

### 1. Проверка конфигурации
```bash
# Запуск проверки конфигурации
python -c "from src.config import get_settings; print('Config OK:', get_settings().openai_api_key[:10] + '...')"
```

### 2. Тест API подключения
```bash
# Запуск health check
python -c "
import asyncio
from src.services.openai_service import OpenAIService
from src.config import get_settings

async def test():
    service = OpenAIService(get_settings())
    print('OpenAI service initialized successfully')

asyncio.run(test())
"
```

### 3. Полный тест приложения
```bash
# Запуск приложения в тестовом режиме
python main.py &
sleep 5

# Проверка health endpoint
curl -f http://localhost:8000/health

# Остановка тестового сервера
pkill -f "python main.py"
```

## 🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ

### Сценарий: Потеря .env файла

1. **Немедленные действия:**
   ```bash
   # Остановка сервиса
   docker-compose down
   
   # Восстановление из последнего backup'а
   gpg --decrypt backups/latest/env.encrypted.gpg > .env
   chmod 600 .env
   ```

2. **Проверка восстановления:**
   ```bash
   # Проверка конфигурации
   python -c "from src.config import get_settings; print('OpenAI key:', get_settings().openai_api_key[:10] + '...')"
   
   # Запуск сервиса
   docker-compose up -d
   
   # Проверка работоспособности
   curl http://localhost:8000/health
   ```

### Сценарий: Компрометация ключей

1. **Немедленные действия:**
   ```bash
   # Остановка всех сервисов
   docker-compose down
   
   # Генерация новых ключей в OpenAI Dashboard
   # Обновление .env файла с новыми ключами
   ```

2. **Обновление конфигурации:**
   ```bash
   # Создание backup старой конфигурации
   cp .env .env.compromised.$(date +'%Y%m%d')
   
   # Обновление ключей
   nano .env
   
   # Создание нового backup'а
   ./scripts/backup_keys.sh
   ```

## 📅 РЕГУЛЯРНОЕ ОБСЛУЖИВАНИЕ

### Еженедельные задачи:
- [ ] Создание backup'а ключей
- [ ] Проверка целостности существующих backup'ов
- [ ] Тестирование процедуры восстановления

### Ежемесячные задачи:
- [ ] Ротация backup'ов (удаление старых)
- [ ] Проверка безопасности хранения backup'ов
- [ ] Обновление документации восстановления

### Ежеквартальные задачи:
- [ ] Полное тестирование disaster recovery
- [ ] Обзор и обновление процедур безопасности
- [ ] Аудит доступа к backup'ам

## 🔐 БЕЗОПАСНОСТЬ BACKUP'ОВ

### Требования к хранению:
1. **Шифрование**: Все backup'ы должны быть зашифрованы
2. **Разделение**: Backup'ы хранятся отдельно от рабочей системы
3. **Доступ**: Ограниченный доступ только для авторизованного персонала
4. **Версионность**: Хранение нескольких версий backup'ов

### Рекомендуемые места хранения:
- ✅ Зашифрованное облачное хранилище
- ✅ Внешние зашифрованные диски
- ✅ Корпоративные системы управления секретами
- ❌ Незашифрованные облачные сервисы
- ❌ Локальные незащищенные диски

## 📞 КОНТАКТЫ ЭКСТРЕННОГО РЕАГИРОВАНИЯ

В случае критических проблем с ключами:

1. **Технический администратор**: [Ваш контакт]
2. **Команда безопасности**: [Контакт команды безопасности]
3. **OpenAI Support**: https://help.openai.com/

---

**Последнее обновление:** $(date)
**Версия документа:** 1.0
**Ответственный:** Команда разработки OptimaAI