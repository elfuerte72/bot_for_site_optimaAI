"""
OptimaAI Bot API - основной файл приложения.
Предоставляет API для взаимодействия с ботом на основе OpenAI.
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

from src.config import Settings, get_settings
from src.services.openai_service import OpenAIService
from src.services.cache_service import CacheService
from src.models.message import Message, MessageResponse
from src.middleware.logging import RequestLoggingMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация приложения FastAPI
app = FastAPI(
    title="OptimaAI Bot API",
    description="API для взаимодействия с ботом на основе OpenAI",
    version="1.0.0"
)

# Настройка CORS для доступа с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для логирования запросов
app.add_middleware(RequestLoggingMiddleware)

# Инициализация сервиса кэширования
cache_service = CacheService(ttl_seconds=3600)

# Модель запроса для чата
class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="История сообщений")
    stream: bool = Field(False, description="Использовать потоковую передачу ответа")
    use_cache: bool = Field(True, description="Использовать кэширование ответов")


@app.get("/health")
async def health_check():
    """Проверка работоспособности API."""
    return {"status": "ok"}


@app.post("/chat", response_model=MessageResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Обработка запроса к чат-боту.
    
    Args:
        request: Запрос с историей сообщений
        settings: Настройки приложения
        
    Returns:
        MessageResponse: Ответ бота
    """
    try:
        # Проверяем кэш, если использование кэша включено
        if request.use_cache:
            cached_response = cache_service.get(request.messages)
            if cached_response:
                return MessageResponse(**cached_response)
        
        # Если ответа нет в кэше или кэширование отключено, генерируем новый ответ
        openai_service = OpenAIService(settings)
        response = await openai_service.generate_response(request.messages, request.stream)
        
        # Сохраняем ответ в кэш, если кэширование включено
        if request.use_cache:
            cache_service.set(request.messages, response.model_dump())
            
        return response
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Получение статистики кэша.
    """
    return {
        "size": len(cache_service._cache),
        "ttl_seconds": cache_service.ttl_seconds
    }


@app.post("/cache/clear")
async def clear_cache():
    """
    Очистка кэша.
    """
    count = cache_service.clear_all()
    return {"cleared_items": count}


@app.post("/cache/clear-expired")
async def clear_expired_cache():
    """
    Очистка устаревших записей кэша.
    """
    count = cache_service.clear_expired()
    return {"cleared_items": count}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
