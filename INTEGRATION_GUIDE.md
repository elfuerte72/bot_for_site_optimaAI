# 🤖 Руководство по интеграции OptimaAI Bot

## 📋 Статус системы

✅ **RAG система настроена и работает**
✅ **API ключ OpenAI действителен** 
✅ **Векторные индексы созданы**
✅ **Документы загружены и проиндексированы**
✅ **Markdown символы удаляются из ответов**
✅ **Сервер запущен и отвечает**

## 🚀 Быстрый старт

### 1. Запуск сервера

```bash
cd /Users/maximpenkin/Documents/openai/site/backend
python main.py
```

Сервер будет доступен по адресу: `http://localhost:8000`

### 2. Проверка работоспособности

```bash
curl -X GET "http://localhost:8000/health"
```

## 🔗 API Endpoints

### Health Check
```
GET /health
```
Проверка работоспособности сервера.

### Chat API
```
POST /chat
POST /api/chat  # Альтернативный эндпоинт для фронтенда
```

**Headers:**
```
Content-Type: application/json
X-API-Key: your_optional_api_key_for_authentication
```

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Расскажи о компании Optima AI"}
  ],
  "use_cache": false,
  "stream": false
}
```

**Response:**
```json
{
  "message": {
    "role": "assistant",
    "content": "Optima AI — это компания..."
  },
  "finish_reason": "stop",
  "processing_time": 2.5,
  "from_cache": false,
  "model": "gpt-4o-mini"
}
```

## 🌐 Интеграция с фронтендом

### JavaScript/TypeScript пример

```javascript
class OptimaAIBot {
  constructor(apiUrl = 'http://localhost:8000', apiKey = 'your_optional_api_key_for_authentication') {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  async sendMessage(message, conversationHistory = []) {
    const messages = [
      ...conversationHistory,
      { role: 'user', content: message }
    ];

    try {
      const response = await fetch(`${this.apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify({
          messages: messages,
          use_cache: true,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        message: data.message.content,
        processingTime: data.processing_time,
        fromCache: data.from_cache
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Использование
const bot = new OptimaAIBot();

async function handleUserMessage(userMessage) {
  const result = await bot.sendMessage(userMessage);
  
  if (result.success) {
    console.log('Ответ бота:', result.message);
    console.log('Время обработки:', result.processingTime, 'сек');
  } else {
    console.error('Ошибка:', result.error);
  }
}
```

### React Hook пример

```jsx
import { useState, useCallback } from 'react';

const useOptimaAIBot = (apiUrl = 'http://localhost:8000') => {
  const [isLoading, setIsLoading] = useState(false);
  const [conversation, setConversation] = useState([]);

  const sendMessage = useCallback(async (message) => {
    setIsLoading(true);
    
    const newUserMessage = { role: 'user', content: message };
    setConversation(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'your_optional_api_key_for_authentication'
        },
        body: JSON.stringify({
          messages: [...conversation, newUserMessage],
          use_cache: true,
          stream: false
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        const botMessage = { role: 'assistant', content: data.message.content };
        setConversation(prev => [...prev, botMessage]);
        return { success: true, message: data.message.content };
      } else {
        throw new Error(data.error || 'Ошибка API');
      }
    } catch (error) {
      console.error('Ошибка при отправке сообщения:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, conversation]);

  const clearConversation = useCallback(() => {
    setConversation([]);
  }, []);

  return {
    conversation,
    isLoading,
    sendMessage,
    clearConversation
  };
};

// Компонент чата
const ChatComponent = () => {
  const { conversation, isLoading, sendMessage, clearConversation } = useOptimaAIBot();
  const [inputMessage, setInputMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const result = await sendMessage(inputMessage);
    setInputMessage('');
    
    if (!result.success) {
      alert('Ошибка: ' + result.error);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {conversation.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'Вы' : 'OptimaAI'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
        {isLoading && <div className="loading">Бот печатает...</div>}
      </div>
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Введите ваш вопрос..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !inputMessage.trim()}>
          Отправить
        </button>
      </form>
      
      <button onClick={clearConversation}>Очистить чат</button>
    </div>
  );
};
```

## 🔧 Настройки CORS

Для подключения с фронтенда обновите `ALLOWED_ORIGINS` в `.env`:

```env
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

## 🛡️ Безопасность

1. **API Key**: Используйте API ключ для аутентификации
2. **CORS**: Настройте разрешенные домены
3. **Rate Limiting**: Настроен лимит 100 запросов в минуту
4. **Input Sanitization**: Входные данные автоматически очищаются

## 📊 Мониторинг

### Метрики
```
GET /metrics
```

### Статус безопасности
```
GET /security/status
```

### Статистика кэша
```
GET /cache/stats
```

## 🔄 Управление кэшем

### Очистка кэша
```
POST /cache/clear
```

### Очистка устаревших записей
```
POST /cache/clear-expired
```

## 🐛 Отладка

### Логи
Логи сохраняются в файл `app.log`

### Тестирование API
```bash
python test_chat_api.py
```

### Тестирование RAG системы
```bash
python src/rag_test.py
```

## 📝 Примеры запросов

### Простой запрос (основной эндпоинт)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_optional_api_key_for_authentication" \
  -d '{
    "messages": [
      {"role": "user", "content": "Расскажи о компании Optima AI"}
    ]
  }'
```

### Простой запрос (фронтенд эндпоинт)
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_optional_api_key_for_authentication" \
  -d '{
    "messages": [
      {"role": "user", "content": "Расскажи о компании Optima AI"}
    ]
  }'
```

### Запрос с историей
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_optional_api_key_for_authentication" \
  -d '{
    "messages": [
      {"role": "user", "content": "Расскажи о компании"},
      {"role": "assistant", "content": "Optima AI — это компания..."},
      {"role": "user", "content": "А какие у вас курсы?"}
    ]
  }'
```

## 🚀 Продакшен

### Переменные окружения для продакшена
```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["https://yourdomain.com"]
API_KEY=secure_production_api_key
RATE_LIMIT_PER_MINUTE=60
```

### Docker
```bash
docker-compose up -d
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `app.log`
2. Убедитесь, что сервер запущен: `curl http://localhost:8000/health`
3. Проверьте API ключ OpenAI
4. Убедитесь, что RAG индексы созданы

---

**Статус:** ✅ Готов к использованию
**Последнее обновление:** 01.06.2025