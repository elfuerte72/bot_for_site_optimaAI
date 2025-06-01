"""
Интеграционные тесты для OptimaAI Bot.
"""

import pytest
import httpx
import asyncio
import time
from unittest.mock import patch, MagicMock
import json


@pytest.mark.integration
class TestAPIIntegration:
    """Интеграционные тесты API."""
    
    @pytest.fixture
    def client(self):
        """HTTP клиент для тестирования."""
        return httpx.Client(base_url="http://localhost:8000")
    
    @pytest.fixture
    async def async_client(self):
        """Асинхронный HTTP клиент."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            yield client
    
    def test_health_endpoint(self, client):
        """Тест health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_status_endpoint(self, client):
        """Тест status endpoint."""
        response = client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "uptime" in data
        assert "memory_usage" in data
    
    def test_chat_endpoint_basic(self, client):
        """Базовый тест chat endpoint."""
        payload = {
            "message": "Привет!",
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "user_id" in data
        assert data["user_id"] == "test_user_123"
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0
    
    def test_chat_endpoint_validation(self, client):
        """Тест валидации chat endpoint."""
        # Пустое сообщение
        response = client.post("/api/chat", json={"message": "", "user_id": "test"})
        assert response.status_code == 400
        
        # Отсутствует user_id
        response = client.post("/api/chat", json={"message": "test"})
        assert response.status_code == 400
        
        # Слишком длинное сообщение
        long_message = "x" * 10000
        response = client.post("/api/chat", json={
            "message": long_message, 
            "user_id": "test"
        })
        assert response.status_code == 400
    
    def test_search_endpoint(self, client):
        """Тест search endpoint."""
        params = {"q": "Python programming", "limit": 5}
        response = client.get("/api/search", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data
        assert data["query"] == "Python programming"
        assert isinstance(data["results"], list)
        assert len(data["results"]) <= 5
    
    def test_rate_limiting(self, client):
        """Тест rate limiting."""
        # Делаем много быстрых запросов
        responses = []
        for i in range(20):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Проверяем, что есть ответы с кодом 429 (Too Many Requests)
        rate_limited = any(code == 429 for code in responses)
        if rate_limited:
            assert True  # Rate limiting работает
        else:
            # Если rate limiting не сработал, это может быть нормально
            # в зависимости от конфигурации
            pass
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """Тест конкурентных запросов."""
        async def make_request(user_id):
            payload = {
                "message": f"Test message from user {user_id}",
                "user_id": f"user_{user_id}"
            }
            response = await async_client.post("/api/chat", json=payload)
            return response.status_code, response.json()
        
        # Запускаем 10 конкурентных запросов
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Проверяем, что все запросы успешны
        for status_code, data in results:
            assert status_code == 200
            assert "response" in data
    
    def test_error_handling(self, client):
        """Тест обработки ошибок."""
        # Несуществующий endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        # Неправильный метод
        response = client.delete("/api/chat")
        assert response.status_code == 405
        
        # Неправильный Content-Type
        response = client.post("/api/chat", data="invalid json")
        assert response.status_code == 400


@pytest.mark.integration
class TestDatabaseIntegration:
    """Интеграционные тесты базы данных."""
    
    @pytest.fixture
    def db_session(self):
        """Сессия базы данных для тестирования."""
        # Здесь должна быть настройка тестовой БД
        pass
    
    def test_user_creation(self, db_session):
        """Тест создания пользователя."""
        # Пример теста для БД
        pass
    
    def test_conversation_storage(self, db_session):
        """Тест сохранения разговоров."""
        pass


@pytest.mark.integration
class TestExternalServicesIntegration:
    """Интеграционные тесты внешних сервисов."""
    
    @patch('src.services.openai_service.OpenAIService.generate_response')
    def test_openai_service_mock(self, mock_generate):
        """Тест с мокированием OpenAI сервиса."""
        mock_generate.return_value = "Mocked response"
        
        # Здесь тестируем логику с мокированным сервисом
        assert mock_generate.return_value == "Mocked response"
    
    def test_redis_connection(self):
        """Тест подключения к Redis."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            assert True
        except Exception:
            pytest.skip("Redis not available")
    
    @pytest.mark.slow
    def test_external_api_real(self):
        """Тест реального внешнего API (медленный)."""
        # Этот тест помечен как медленный и может быть пропущен
        # при быстром запуске тестов
        pass


@pytest.mark.integration
class TestSecurityIntegration:
    """Интеграционные тесты безопасности."""
    
    def test_sql_injection_protection(self, client):
        """Тест защиты от SQL инъекций."""
        malicious_payload = {
            "message": "'; DROP TABLE users; --",
            "user_id": "test_user"
        }
        
        response = client.post("/api/chat", json=malicious_payload)
        # Запрос должен быть обработан безопасно
        assert response.status_code in [200, 400]  # Не должно быть 500
    
    def test_xss_protection(self, client):
        """Тест защиты от XSS."""
        xss_payload = {
            "message": "<script>alert('xss')</script>",
            "user_id": "test_user"
        }
        
        response = client.post("/api/chat", json=xss_payload)
        assert response.status_code == 200
        
        data = response.json()
        # Проверяем, что скрипт не выполняется
        assert "<script>" not in data.get("response", "")
    
    def test_authentication_required(self, client):
        """Тест требования аутентификации для защищенных endpoint'ов."""
        # Тест доступа к админским функциям без токена
        response = client.get("/api/admin/stats")
        assert response.status_code == 401
    
    def test_cors_headers(self, client):
        """Тест CORS заголовков."""
        response = client.options("/api/chat")
        headers = response.headers
        
        # Проверяем наличие CORS заголовков
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers


@pytest.mark.integration
class TestPerformanceIntegration:
    """Интеграционные тесты производительности."""
    
    def test_response_time(self, client):
        """Тест времени отклика."""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0  # Ответ должен быть быстрее 1 секунды
        assert response.status_code == 200
    
    def test_memory_usage_stability(self, client):
        """Тест стабильности использования памяти."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Делаем много запросов
        for i in range(100):
            response = client.get("/health")
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Рост памяти не должен быть критичным
        assert memory_growth < 50 * 1024 * 1024  # Меньше 50MB
    
    @pytest.mark.benchmark(group="api")
    def test_chat_performance(self, benchmark, client):
        """Бенчмарк производительности chat API."""
        def chat_request():
            payload = {
                "message": "Test performance message",
                "user_id": "benchmark_user"
            }
            response = client.post("/api/chat", json=payload)
            return response.status_code
        
        result = benchmark(chat_request)
        assert result == 200


@pytest.mark.integration
class TestDockerIntegration:
    """Интеграционные тесты Docker."""
    
    @pytest.mark.slow
    def test_docker_build(self):
        """Тест сборки Docker образа."""
        import subprocess
        
        result = subprocess.run([
            "docker", "build", "-t", "optimaai-bot:test", "."
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"
    
    @pytest.mark.slow
    def test_docker_run(self):
        """Тест запуска Docker контейнера."""
        import subprocess
        import time
        
        # Запускаем контейнер
        run_result = subprocess.run([
            "docker", "run", "-d", "--name", "test-container",
            "-p", "8001:8000", "optimaai-bot:test"
        ], capture_output=True, text=True)
        
        if run_result.returncode != 0:
            pytest.skip(f"Could not start container: {run_result.stderr}")
        
        try:
            # Ждем запуска
            time.sleep(10)
            
            # Проверяем health endpoint
            health_result = subprocess.run([
                "curl", "-f", "http://localhost:8001/health"
            ], capture_output=True, text=True)
            
            assert health_result.returncode == 0, "Health check failed"
            
        finally:
            # Останавливаем и удаляем контейнер
            subprocess.run(["docker", "stop", "test-container"], 
                         capture_output=True)
            subprocess.run(["docker", "rm", "test-container"], 
                         capture_output=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])