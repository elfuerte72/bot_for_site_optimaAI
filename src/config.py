"""
Модуль конфигурации приложения.
Загружает настройки из переменных окружения с валидацией.
"""

from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, validator
from pydantic_settings import BaseSettings

# Загрузка переменных окружения из файла .env
load_dotenv()

# Константы
DEFAULT_GPT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024
DEFAULT_CACHE_TTL = 3600  # 1 час
DEFAULT_RATE_LIMIT = 100  # запросов в минуту


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
    port: int = Field(default=8000, ge=1, le=65535, description="Порт для запуска")

    # Безопасность
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"],
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

    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        """Валидация OpenAI API ключа."""
        if not v or len(v) < 10:
            raise ValueError(
                "OpenAI API ключ должен быть указан и содержать минимум 10 символов"
            )
        return v

    @validator("allowed_origins")
    def validate_origins(cls, v):
        """Валидация списка разрешённых доменов."""
        if not v:
            raise ValueError("Должен быть указан хотя бы один разрешённый домен")
        return v

    class Config:
        """Конфигурация настроек."""

        env_file = ".env"
        case_sensitive = False
        env_prefix = ""


@lru_cache()
def get_settings() -> Settings:
    """
    Получение настроек приложения с кэшированием.

    Returns:
        Settings: Объект настроек
    """
    return Settings()
