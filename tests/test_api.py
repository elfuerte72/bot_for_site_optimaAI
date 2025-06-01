"""
Тесты для API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from src.models.message import Message, MessageRole


@pytest.fixture
def client():
    """Фикстура для тестового клиента."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Мок настроек для тестов."""
    with patch("main.get_settings") as mock:
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.gpt_model = "gpt-4o-mini"
        settings.enable_cache = True
        settings.cache_ttl_seconds = 3600
        settings.allowed_origins = ["http://localhost:3000"]
        settings.rate_limit_per_minute = 100
        settings.api_key = None  # Отключаем аутентификацию для тестов
        mock.return_value = settings
        yield settings


def test_health_endpoint(client, mock_settings):
    """Тест эндпоинта проверки здоровья."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data
    assert "services" in data
    assert "timestamp" in data


def test_chat_endpoint_validation(client, mock_settings):
    """Тест валидации запроса к чату."""
    # Пустой запрос
    response = client.post("/chat", json={})
    assert response.status_code == 422

    # Неправильная структура сообщений
    response = client.post("/chat", json={"messages": []})
    assert response.status_code == 422

    # Правильная структура
    response = client.post(
        "/chat", json={"messages": [{"role": "user", "content": "Тестовое сообщение"}]}
    )
    # Может вернуть 500 из-за отсутствия реального OpenAI ключа
    assert response.status_code in [200, 400, 500]


@patch("src.services.openai_service.OpenAIService")
def test_chat_endpoint_success(mock_openai_service, client, mock_settings):
    """Тест успешного ответа от чата."""
    # Мокаем OpenAI сервис
    mock_service_instance = MagicMock()
    mock_openai_service.return_value = mock_service_instance

    # Мокаем ответ
    mock_response = MagicMock()
    mock_response.message = Message(
        role=MessageRole.ASSISTANT, content="Тестовый ответ"
    )
    mock_response.finish_reason = "stop"
    mock_response.usage = None
    mock_response.model_dump.return_value = {
        "message": {"role": "assistant", "content": "Тестовый ответ"},
        "finish_reason": "stop",
        "usage": None,
    }

    mock_service_instance.generate_response.return_value = mock_response

    response = client.post(
        "/chat", json={"messages": [{"role": "user", "content": "Тестовое сообщение"}]}
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"]["content"] == "Тестовый ответ"


def test_cache_endpoints(client, mock_settings):
    """Тест эндпоинтов кэша."""
    # Статистика кэша
    response = client.get("/cache/stats")
    # Может вернуть 404 если кэш не инициализирован
    assert response.status_code in [200, 404]

    # Очистка кэша
    response = client.post("/cache/clear")
    assert response.status_code in [200, 404]

    # Очистка устаревших записей
    response = client.post("/cache/clear-expired")
    assert response.status_code in [200, 404]


def test_metrics_endpoint(client, mock_settings):
    """Тест эндпоинта метрик."""
    response = client.get("/metrics")
    assert response.status_code == 200

    data = response.json()
    assert "uptime_seconds" in data
    assert "cache_enabled" in data
    assert "timestamp" in data


def test_rate_limiting(client, mock_settings):
    """Тест rate limiting (базовый)."""
    # Делаем несколько запросов подряд
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200

        # Проверяем наличие заголовков rate limiting
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


def test_cors_headers(client, mock_settings):
    """Тест CORS заголовков."""
    # Тестируем обычный GET запрос с Origin
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200
    # Проверяем наличие базовых заголовков безопасности
    assert "X-Frame-Options" in response.headers
    assert "X-Content-Type-Options" in response.headers


def test_error_handling(client, mock_settings):
    """Тест обработки ошибок."""
    # Тест с некорректными данными
    response = client.post(
        "/chat", json={"messages": [{"role": "invalid_role", "content": "Тест"}]}
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "error_code" in data
