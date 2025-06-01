"""
Модуль конфигурации приложения.
Загружает настройки из переменных окружения с валидацией.
"""

import json
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Условная загрузка .env файла только для локальной разработки
# В продакшене (Heroku) переменная DYNO будет установлена
if os.getenv("DYNO") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # python-dotenv может отсутствовать в продакшене
        pass

# Константы
DEFAULT_GPT_MODEL = "gpt-4o-nano"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1024
DEFAULT_CACHE_TTL = 3600  # 1 час
DEFAULT_RATE_LIMIT = 100  # запросов в минуту
DEFAULT_MAX_HISTORY_MESSAGES = 10  # максимум сообщений в истории


class Settings(BaseSettings):
    """Класс настроек приложения с валидацией."""

    # OpenAI API настройки
    openai_api_key: str = Field(..., min_length=10, description="OpenAI API ключ")
    gpt_model: str = Field(default=DEFAULT_GPT_MODEL, description="Модель GPT")
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=0.0,
        le=2.0,
        description="Температура генерации",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=1,
        le=4000,
        description="Максимальное количество токенов",
    )

    # Системный промпт
    system_prompt: str = Field(
        default="""Ты - умный ассистент компании Optima AI.
Отвечай на запросы пользователя, основываясь на предоставленном контексте.
Если в контексте нет релевантной информации, признайся в этом и предложи
задать другой вопрос.
Твои ответы должны быть вежливыми, информативными и полезными.
Не выдумывай информацию.
Всегда отвечай на русском языке.""",
        description="Системный промпт",
    )

    # Настройки приложения
    app_name: str = Field(default="OptimaAI Bot", description="Название приложения")
    debug: bool = Field(default=False, description="Режим отладки")
    host: str = Field(default="0.0.0.0", description="Хост для запуска")
    # Порт читается из переменной окружения PORT (Heroku устанавливает автоматически)
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")), ge=1, le=65535, description="Порт для запуска")

    # Безопасность
    # CORS origins читаются из JSON строки в переменной окружения
    allowed_origins: List[str] = Field(
        default_factory=lambda: _parse_allowed_origins(),
        description="Разрешённые домены для CORS",
    )
    api_key: Optional[str] = Field(
        default=None, description="API ключ для аутентификации"
    )
    rate_limit_per_minute: int = Field(
        default=DEFAULT_RATE_LIMIT, ge=1, description="Лимит запросов в минуту"
    )

    # Кэширование
    cache_ttl_seconds: int = Field(
        default=DEFAULT_CACHE_TTL, ge=0, description="TTL кэша в секундах"
    )
    enable_cache: bool = Field(default=True, description="Включить кэширование")
    
    # История сообщений
    max_history_messages: int = Field(
        default=DEFAULT_MAX_HISTORY_MESSAGES, 
        ge=1, 
        le=50, 
        description="Максимальное количество сообщений в истории"
    )

    # RAG настройки
    rag_chunk_size: int = Field(
        default=1000, ge=100, le=2000, description="Размер чанка для RAG"
    )
    rag_chunk_overlap: int = Field(
        default=200, ge=0, le=500, description="Перекрытие чанков для RAG"
    )
    rag_k_documents: int = Field(
        default=4, ge=1, le=10, description="Количество документов для поиска"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Модель для эмбеддингов"
    )

    # Пути
    data_dir: str = Field(default="rag", description="Директория с данными")
    persist_dir: str = Field(default="rag_index", description="Директория для индексов")

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Валидация OpenAI API ключа."""
        if not v or len(v) < 10:
            raise ValueError(
                "OpenAI API ключ должен быть указан и содержать минимум 10 символов"
            )
        return v

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Валидация списка разрешённых доменов."""
        if not v:
            raise ValueError("Должен быть указан хотя бы один разрешённый домен")
        return v

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="",
    )


def _parse_allowed_origins() -> List[str]:
    """
    Парсинг ALLOWED_ORIGINS из переменной окружения.
    Ожидается JSON строка, например: '["https://example.com", "https://www.example.com"]'
    
    Returns:
        List[str]: Список разрешённых origins
    """
    origins_raw = os.getenv("ALLOWED_ORIGINS", '[]')
    
    # Если это не JSON, а строка с запятыми (для совместимости)
    if not origins_raw.startswith('['):
        origins = [origin.strip() for origin in origins_raw.split(',') if origin.strip()]
        return origins if origins else ["http://localhost:3000"]
    
    try:
        origins = json.loads(origins_raw)
        if not isinstance(origins, list):
            raise ValueError("ALLOWED_ORIGINS должен быть JSON массивом")
        return origins if origins else ["http://localhost:3000"]
    except (json.JSONDecodeError, ValueError) as e:
        # В случае ошибки парсинга используем localhost для разработки
        print(f"⚠️ Ошибка парсинга ALLOWED_ORIGINS: {e}. Используется localhost.")
        return ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    """
    Получение настроек приложения с кэшированием.

    Returns:
        Settings: Объект настроек
    """
    return Settings()
