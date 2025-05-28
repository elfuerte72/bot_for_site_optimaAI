"""
Модуль конфигурации приложения.
Загружает настройки из переменных окружения.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()


class Settings(BaseSettings):
    """Класс настроек приложения."""
    
    # OpenAI API настройки
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gpt_model: str = os.getenv("GPT_MODEL", "gpt-4.1-nano")
    system_prompt: str = os.getenv("SYSTEM_PROMPT", "")
    
    # Настройки приложения
    app_name: str = "OptimaAI Bot"
    debug: bool = False
    
    class Config:
        """Конфигурация настроек."""
        
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Получение настроек приложения с кэшированием.
    
    Returns:
        Settings: Объект настроек
    """
    return Settings()
