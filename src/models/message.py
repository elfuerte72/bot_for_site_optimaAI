"""
Модели сообщений для чат-бота с улучшенной типизацией и валидацией.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    """Роли участников чата."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class FinishReason(str, Enum):
    """Причины завершения генерации ответа."""
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    FUNCTION_CALL = "function_call"
    TOOL_CALLS = "tool_calls"


class TokenUsage(BaseModel):
    """Статистика использования токенов."""
    prompt_tokens: int = Field(
        ..., ge=0, description="Количество токенов в промпте"
    )
    completion_tokens: int = Field(
        ..., ge=0, description="Количество токенов в ответе"
    )
    total_tokens: int = Field(
        ..., ge=0, description="Общее количество токенов"
    )
    
    @validator('total_tokens')
    def validate_total_tokens(cls, v, values):
        """Валидация общего количества токенов."""
        prompt_tokens = values.get('prompt_tokens', 0)
        completion_tokens = values.get('completion_tokens', 0)
        expected_total = prompt_tokens + completion_tokens
        
        if v != expected_total:
            raise ValueError(
                f'total_tokens ({v}) должно равняться сумме prompt_tokens '
                f'({prompt_tokens}) и completion_tokens ({completion_tokens})'
            )
        return v


class Message(BaseModel):
    """Модель сообщения для чата с валидацией."""
    
    role: MessageRole = Field(
        ..., 
        description="Роль отправителя сообщения"
    )
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=32000, 
        description="Содержание сообщения"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now, 
        description="Время создания сообщения"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Дополнительные метаданные"
    )
    
    @validator('content')
    def validate_content(cls, v, values):
        """Валидация содержимого сообщения."""
        role = values.get('role')
        
        # Системные сообщения не могут быть пустыми
        if role == MessageRole.SYSTEM and not v.strip():
            raise ValueError('Системное сообщение не может быть пустым')
        
        # Удаляем лишние пробелы
        return v.strip()


class ChatRequest(BaseModel):
    """Модель запроса к чат-боту с валидацией."""
    
    messages: List[Message] = Field(
        ..., 
        min_items=1, 
        max_items=50,
        description="История сообщений"
    )
    stream: bool = Field(
        default=False, 
        description="Использовать потоковую передачу ответа"
    )
    use_cache: bool = Field(
        default=True, 
        description="Использовать кэширование ответов"
    )
    temperature: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=2.0, 
        description="Температура генерации (переопределяет настройки)"
    )
    max_tokens: Optional[int] = Field(
        default=None, 
        ge=1, 
        le=4000, 
        description=(
            "Максимальное количество токенов (переопределяет настройки)"
        )
    )
    
    @validator('messages')
    def validate_messages(cls, v):
        """Валидация списка сообщений."""
        if not v:
            raise ValueError('Список сообщений не может быть пустым')
        
        # Проверяем, что последнее сообщение от пользователя
        if v[-1].role != MessageRole.USER:
            raise ValueError('Последнее сообщение должно быть от пользователя')
        
        # Проверяем, что нет более одного системного сообщения
        system_messages = [msg for msg in v if msg.role == MessageRole.SYSTEM]
        if len(system_messages) > 1:
            raise ValueError('Может быть только одно системное сообщение')
        
        # Если есть системное сообщение, оно должно быть первым
        if system_messages and v[0].role != MessageRole.SYSTEM:
            raise ValueError('Системное сообщение должно быть первым')
        
        return v


class MessageResponse(BaseModel):
    """Модель ответа от чат-бота с расширенной информацией."""
    
    message: Message = Field(..., description="Сообщение от бота")
    finish_reason: Optional[FinishReason] = Field(
        None, description="Причина завершения генерации"
    )
    usage: Optional[TokenUsage] = Field(
        None, description="Информация об использовании токенов"
    )
    model: Optional[str] = Field(
        None, description="Модель, использованная для генерации"
    )
    processing_time: Optional[float] = Field(
        None, ge=0.0, description="Время обработки запроса в секундах"
    )
    from_cache: bool = Field(
        default=False, description="Ответ получен из кэша"
    )
    rag_context: Optional[str] = Field(
        None, description="Контекст, полученный из RAG системы"
    )


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""
    
    error: str = Field(..., description="Описание ошибки")
    error_code: str = Field(..., description="Код ошибки")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Дополнительные детали ошибки"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Время возникновения ошибки"
    )


class HealthResponse(BaseModel):
    """Модель ответа для проверки здоровья сервиса."""
    
    status: str = Field(..., description="Статус сервиса")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Время проверки"
    )
    version: str = Field(default="1.0.0", description="Версия API")
    uptime: Optional[float] = Field(
        None, description="Время работы сервиса в секундах"
    )
    services: Optional[Dict[str, str]] = Field(
        None, description="Статус внешних сервисов"
    )
