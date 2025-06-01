"""
Конфигурация для тестов.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from main import (
    setup_exception_handlers, 
    health_check, 
    chat, 
    get_cache_stats, 
    clear_cache, 
    clear_expired_cache, 
    get_metrics, 
    get_security_status
)
from src.middleware.logging import RequestLoggingMiddleware


@pytest.fixture(autouse=True)
def mock_settings():
    """Автоматический мок настроек для всех тестов."""
    with patch("main.get_settings") as mock_get_settings, \
         patch("src.config.get_settings") as mock_config_settings, \
         patch("src.middleware.auth.get_settings") as mock_auth_settings, \
         patch("src.middleware.rate_limit.get_settings") as mock_rate_settings, \
         patch("src.services.openai_service.get_settings") as mock_service_settings:
        
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.gpt_model = "gpt-4o-mini"
        settings.enable_cache = True
        settings.cache_ttl_seconds = 3600
        settings.allowed_origins = ["http://localhost:3000"]
        settings.rate_limit_per_minute = 100
        settings.api_key = None  # Отключаем аутентификацию для тестов
        settings.debug = True
        settings.host = "localhost"
        settings.port = 8000
        settings.temperature = 0.7
        settings.max_tokens = 1000
        settings.system_prompt = "Test prompt"
        
        # Применяем мок ко всем местам, где используются настройки
        mock_get_settings.return_value = settings
        mock_config_settings.return_value = settings
        mock_auth_settings.return_value = settings
        mock_rate_settings.return_value = settings
        mock_service_settings.return_value = settings
        
        yield settings


@pytest.fixture
def test_app(mock_settings):
    """Создает тестовое приложение без аутентификации."""
    app = FastAPI(
        title="Test OptimaAI Bot API",
        description="Test API",
        version="2.0.0-test",
    )
    
    # Добавляем только необходимые middleware для тестов
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Логирование запросов
    app.add_middleware(RequestLoggingMiddleware)
    
    # Настраиваем обработчики исключений
    setup_exception_handlers(app)
    
    # Добавляем роуты
    app.get("/health")(health_check)
    app.post("/chat")(chat)
    app.get("/cache/stats")(get_cache_stats)
    app.post("/cache/clear")(clear_cache)
    app.post("/cache/clear-expired")(clear_expired_cache)
    app.get("/metrics")(get_metrics)
    app.get("/security/status")(get_security_status)
    
    return app


@pytest.fixture
def client(test_app):
    """Тестовый клиент FastAPI."""
    return TestClient(test_app)


@pytest.fixture
def auth_headers():
    """Заголовки аутентификации для тестов, где она нужна."""
    return {"X-API-Key": "test-api-key"}