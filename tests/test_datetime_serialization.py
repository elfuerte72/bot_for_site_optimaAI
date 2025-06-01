"""
Тесты для проверки сериализации datetime объектов.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import DateTimeEncoder, app, create_json_response
from src.models.message import Message, MessageResponse, MessageRole


# Используем fixtures из conftest.py


def test_datetime_encoder():
    """Тест DateTimeEncoder для сериализации datetime."""
    encoder = DateTimeEncoder()
    
    # Тестируем datetime объект
    test_datetime = datetime(2023, 12, 25, 15, 30, 45)
    result = encoder.default(test_datetime)
    assert result == "2023-12-25T15:30:45"
    
    # Тестируем обычный объект
    test_string = "test"
    with pytest.raises(TypeError):
        encoder.default(test_string)


def test_create_json_response():
    """Тест create_json_response с datetime объектами."""
    test_data = {
        "message": "test",
        "timestamp": datetime(2023, 12, 25, 15, 30, 45),
        "nested": {
            "created_at": datetime(2023, 12, 25, 16, 0, 0)
        }
    }
    
    response = create_json_response(test_data)
    
    assert response.status_code == 200
    
    # Проверяем, что datetime объекты сериализованы
    content = json.loads(response.body)
    assert content["timestamp"] == "2023-12-25T15:30:45"
    assert content["nested"]["created_at"] == "2023-12-25T16:00:00"


def test_health_endpoint_datetime_serialization(client):
    """Тест сериализации datetime в health endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем, что timestamp присутствует и корректно сериализован
    assert "timestamp" in data
    # Проверяем формат ISO datetime
    timestamp = data["timestamp"]
    assert isinstance(timestamp, str)
    assert "T" in timestamp  # ISO формат содержит T между датой и временем


def test_metrics_endpoint_datetime_serialization(client):
    """Тест сериализации datetime в metrics endpoint."""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем, что timestamp присутствует и корректно сериализован
    assert "timestamp" in data
    timestamp = data["timestamp"]
    assert isinstance(timestamp, str)
    assert "T" in timestamp


def test_security_status_datetime_serialization(client):
    """Тест сериализации datetime в security status endpoint."""
    response = client.get("/security/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем, что timestamp присутствует и корректно сериализован
    assert "timestamp" in data
    timestamp = data["timestamp"]
    assert isinstance(timestamp, str)
    assert "T" in timestamp


def test_error_response_datetime_serialization(client):
    """Тест сериализации datetime в error responses."""
    # Отправляем некорректный запрос для получения ошибки
    response = client.post("/chat", json={})
    
    assert response.status_code == 422
    data = response.json()
    
    # Проверяем структуру ошибки FastAPI validation
    assert "detail" in data
    assert isinstance(data["detail"], list)
    
    # Проверяем, что JSON сериализация прошла успешно
    # (нет ошибок datetime serialization)
    assert len(data["detail"]) > 0
    assert "msg" in data["detail"][0]


@patch("main.OpenAIService")
def test_chat_response_datetime_serialization(mock_openai_service, client):
    """Тест сериализации datetime в chat response."""
    # Создаем настоящий объект MessageResponse
    test_message = Message(
        role=MessageRole.ASSISTANT,
        content="Test response",
        timestamp=datetime(2023, 12, 25, 15, 30, 45)
    )
    
    mock_response = MessageResponse(
        message=test_message,
        processing_time=1.5,
        model="gpt-4o-mini",
        from_cache=False
    )
    
    # Мокаем экземпляр сервиса
    mock_service_instance = MagicMock()
    mock_service_instance.generate_response = AsyncMock(return_value=mock_response)
    mock_service_instance.temperature = 0.7
    mock_service_instance.max_tokens = 1000
    mock_openai_service.return_value = mock_service_instance
    

    
    # Отправляем корректный запрос
    response = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    })
    
    # Проверяем, что запрос обработан без ошибок сериализации
    assert response.status_code == 200
    data = response.json()
    

    
    # Проверяем структуру ответа
    assert "message" in data
    assert "processing_time" in data
    assert "model" in data
    
    # Проверяем, что datetime сериализован как строка
    if "timestamp" in data["message"]:
        timestamp = data["message"]["timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format
        assert timestamp == "2023-12-25T15:30:45"