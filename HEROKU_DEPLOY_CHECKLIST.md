# ✅ Чеклист для деплоя на Heroku

## 📋 Подготовка

- [ ] Docker Desktop запущен и работает
- [ ] Heroku CLI установлен (`brew tap heroku/brew && brew install heroku`)
- [ ] Вы залогинены в Heroku (`heroku login`)
- [ ] Все изменения закоммичены в git
- [ ] .env файл создан и заполнен (но НЕ закоммичен!)

## 🔧 Конфигурация

- [ ] `Procfile` создан с командой запуска
- [ ] `runtime.txt` указывает версию Python 3.11.10
- [ ] `Dockerfile.heroku` оптимизирован для Heroku
- [ ] `heroku.yml` настроен для контейнерного деплоя
- [ ] `requirements-prod.txt` содержит только продакшн зависимости

## 🧪 Локальное тестирование

1. Запустите локальный тест Docker образа:
   ```bash
   ./scripts/test-docker-locally.sh
   ```

2. Проверьте, что API работает:
   ```bash
   curl http://localhost:8000/health
   ```

3. Протестируйте основной функционал:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{"messages": [{"role": "user", "content": "Привет!"}]}'
   ```

4. Остановите тестовые контейнеры:
   ```bash
   docker-compose -f docker-compose.test.yml down
   ```

## 🚀 Деплой на Heroku

### Автоматический деплой

Используйте готовый скрипт:
```bash
./scripts/deploy-heroku.sh your-app-name
```

### Ручной деплой

1. Создайте приложение (если еще не создано):
   ```bash
   heroku create your-app-name
   ```

2. Установите container stack:
   ```bash
   heroku stack:set container -a your-app-name
   ```

3. Настройте переменные окружения:
   ```bash
   # Обязательные
   heroku config:set OPENAI_API_KEY="sk-..." -a your-app-name
   heroku config:set API_KEY="your-secure-api-key" -a your-app-name
   heroku config:set ALLOWED_ORIGINS="https://your-frontend.com" -a your-app-name
   
   # Опциональные
   heroku config:set GPT_MODEL="gpt-4o-mini" -a your-app-name
   heroku config:set RATE_LIMIT_PER_MINUTE="30" -a your-app-name
   heroku config:set ENABLE_CACHE="true" -a your-app-name
   ```

4. Выполните деплой:
   ```bash
   git push heroku main
   ```

## 🔍 Проверка после деплоя

1. Проверьте логи:
   ```bash
   heroku logs --tail -a your-app-name
   ```

2. Проверьте статус:
   ```bash
   heroku ps -a your-app-name
   ```

3. Протестируйте API:
   ```bash
   curl https://your-app-name.herokuapp.com/health
   ```

4. Откройте документацию:
   ```bash
   heroku open /docs -a your-app-name
   ```

## ⚠️ Важные моменты

1. **Порт**: Heroku автоматически назначает порт через `$PORT`
2. **Файловая система**: Ephemeral - файлы не сохраняются между рестартами
3. **Таймаут**: 30 секунд на запрос
4. **Память**: Free tier = 512MB RAM
5. **Сон**: Free apps засыпают после 30 минут неактивности

## 🐛 Решение проблем

### Приложение не запускается
```bash
heroku logs --tail -a your-app-name
heroku restart -a your-app-name
```

### Ошибки с памятью
- Уменьшите размер кэша
- Оптимизируйте обработку запросов
- Обновитесь до платного плана

### Проблемы с RAG
- RAG индекс пересоздается при каждом запуске
- Для постоянного хранения используйте S3 или другое хранилище

## 📊 Мониторинг

- Метрики: `https://your-app-name.herokuapp.com/metrics`
- Статус безопасности: `https://your-app-name.herokuapp.com/security/status`
- Heroku Dashboard: `https://dashboard.heroku.com/apps/your-app-name`

## 🔄 Обновление

Для обновления приложения:
```bash
git add .
git commit -m "Update: описание изменений"
git push heroku main
```

## 🎉 Готово!

Ваше FastAPI приложение с RAG системой теперь доступно по адресу:
`https://your-app-name.herokuapp.com`

Не забудьте обновить ALLOWED_ORIGINS для вашего фронтенда!