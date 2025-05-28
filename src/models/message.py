"""
Модели сообщений для чат-бота.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class Message(BaseModel):
    """Модель сообщения для чата."""
    
    role: Literal["system", "user", "assistant"] = Field(
        ..., 
        description="Роль отправителя сообщения"
    )
    content: str = Field(..., description="Содержание сообщения")


class MessageResponse(BaseModel):
    """Модель ответа от чат-бота."""
    
    message: Message = Field(..., description="Сообщение от бота")
    finish_reason: Optional[str] = Field(None, description="Причина завершения генерации")
    usage: Optional[dict] = Field(None, description="Информация об использовании токенов")
