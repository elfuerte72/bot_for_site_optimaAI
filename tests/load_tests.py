"""
Нагрузочные тесты с использованием Locust.
"""

from locust import HttpUser, task, between
import json
import random


class OptimaAIUser(HttpUser):
    """Пользователь для нагрузочного тестирования OptimaAI Bot."""
    
    wait_time = between(1, 3)  # Пауза между запросами 1-3 секунды
    
    def on_start(self):
        """Выполняется при старте каждого пользователя."""
        # Проверяем доступность сервиса
        response = self.client.get("/health")
        if response.status_code != 200:
            print(f"Service not available: {response.status_code}")
    
    @task(3)
    def health_check(self):
        """Проверка здоровья сервиса (высокий приоритет)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def get_status(self):
        """Получение статуса системы."""
        with self.client.get("/api/status", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "status" in data:
                        response.success()
                    else:
                        response.failure("Invalid response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status check failed: {response.status_code}")
    
    @task(1)
    def chat_request(self):
        """Тестирование чат API."""
        test_messages = [
            "Привет! Как дела?",
            "Расскажи о погоде",
            "Что ты умеешь?",
            "Помоги с задачей",
            "Объясни концепцию машинного обучения"
        ]
        
        message = random.choice(test_messages)
        payload = {
            "message": message,
            "user_id": f"test_user_{random.randint(1, 100)}"
        }
        
        with self.client.post(
            "/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "response" in data:
                        response.success()
                    else:
                        response.failure("Invalid chat response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in chat response")
            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            else:
                response.failure(f"Chat request failed: {response.status_code}")
    
    @task(1)
    def search_request(self):
        """Тестирование поиска."""
        search_queries = [
            "Python programming",
            "Machine learning",
            "Web development",
            "Data science",
            "Artificial intelligence"
        ]
        
        query = random.choice(search_queries)
        params = {"q": query, "limit": 5}
        
        with self.client.get(
            "/api/search",
            params=params,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "results" in data:
                        response.success()
                    else:
                        response.failure("Invalid search response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in search response")
            else:
                response.failure(f"Search request failed: {response.status_code}")


class AdminUser(HttpUser):
    """Администратор для тестирования админских функций."""
    
    wait_time = between(5, 10)  # Более редкие запросы
    weight = 1  # Меньше админов чем обычных пользователей
    
    @task
    def admin_stats(self):
        """Получение статистики (админская функция)."""
        headers = {"Authorization": "Bearer admin_test_token"}
        
        with self.client.get(
            "/api/admin/stats",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized admin access")
            else:
                response.failure(f"Admin stats failed: {response.status_code}")
    
    @task
    def system_metrics(self):
        """Получение системных метрик."""
        headers = {"Authorization": "Bearer admin_test_token"}
        
        with self.client.get(
            "/api/admin/metrics",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized metrics access")
            else:
                response.failure(f"Metrics request failed: {response.status_code}")


class HeavyUser(HttpUser):
    """Пользователь с тяжелыми запросами."""
    
    wait_time = between(10, 20)
    weight = 1  # Мало таких пользователей
    
    @task
    def heavy_processing(self):
        """Тяжелый запрос на обработку."""
        payload = {
            "text": "Это очень длинный текст для обработки. " * 100,
            "options": {
                "deep_analysis": True,
                "generate_summary": True,
                "extract_keywords": True
            }
        }
        
        with self.client.post(
            "/api/process",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            timeout=30  # Увеличенный таймаут для тяжелых запросов
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 408:
                response.failure("Request timeout")
            else:
                response.failure(f"Heavy processing failed: {response.status_code}")


# Конфигурация для разных сценариев нагрузки
class StressTestUser(HttpUser):
    """Пользователь для стресс-тестирования."""
    
    wait_time = between(0.1, 0.5)  # Очень частые запросы
    
    @task
    def rapid_requests(self):
        """Быстрые последовательные запросы."""
        endpoints = ["/health", "/api/status", "/api/ping"]
        endpoint = random.choice(endpoints)
        
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Rapid request failed: {response.status_code}")