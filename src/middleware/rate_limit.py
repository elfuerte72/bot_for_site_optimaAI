"""
Middleware для контроля частоты запросов (rate limiting).
"""

import time
from collections import defaultdict, deque
from typing import Callable, Dict

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения частоты запросов.
    Использует алгоритм sliding window для точного подсчёта запросов.
    """

    def __init__(self, app, calls_per_minute: int = 100, burst_limit: int = 10):
        """
        Инициализация middleware.

        Args:
            app: Экземпляр приложения FastAPI
            calls_per_minute: Максимальное количество запросов в минуту
            burst_limit: Максимальное количество запросов в очереди
        """
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.burst_limit = burst_limit
        self.window_size = 60  # 60 секунд

        # Хранилище временных меток запросов для каждого IP
        self.request_times: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=calls_per_minute * 2)
        )

        # Список путей, исключённых из rate limiting
        self.excluded_paths = {"/health", "/docs", "/openapi.json", "/redoc"}

    def _get_client_id(self, request: Request) -> str:
        """
        Получение идентификатора клиента для rate limiting.

        Args:
            request: HTTP запрос

        Returns:
            str: Идентификатор клиента
        """
        # Проверяем заголовки для реального IP (за прокси/балансировщиком)
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")

        if forwarded_for:
            # Берём первый IP из списка
            client_ip = forwarded_for.split(",")[0].strip()
        elif real_ip:
            client_ip = real_ip
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        return client_ip

    def _is_rate_limited(self, client_id: str) -> bool:
        """
        Проверка, не превышен ли лимит запросов для клиента.

        Args:
            client_id: Идентификатор клиента

        Returns:
            bool: True, если лимит превышен
        """
        now = time.time()
        window_start = now - self.window_size

        # Получаем очередь запросов для клиента
        client_requests = self.request_times[client_id]

        # Удаляем старые запросы (вне окна)
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        # Проверяем лимит
        if len(client_requests) >= self.calls_per_minute:
            return True

        # Добавляем текущий запрос
        client_requests.append(now)
        return False

    def _cleanup_old_entries(self):
        """
        Очистка старых записей для освобождения памяти.
        Запускается периодически.
        """
        current_time = time.time()
        cleanup_threshold = current_time - (self.window_size * 2)

        # Удаляем клиентов, которые не делали запросы длительное время
        clients_to_remove = []
        for client_id, requests in self.request_times.items():
            if not requests or requests[-1] < cleanup_threshold:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.request_times[client_id]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с проверкой rate limiting.

        Args:
            request: HTTP запрос
            call_next: Следующий обработчик в цепочке

        Returns:
            Response: HTTP ответ
        """
        # Проверяем, нужно ли применять rate limiting
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Получаем идентификатор клиента
        client_id = self._get_client_id(request)

        # Проверяем лимит запросов
        if self._is_rate_limited(client_id):
            # Вычисляем время до следующего разрешённого запроса
            client_requests = self.request_times[client_id]
            oldest_request = client_requests[0]
            retry_after = int(oldest_request + self.window_size - time.time())
            retry_after = max(1, retry_after)  # Минимум 1 секунда

            # Возвращаем ошибку 429
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Превышен лимит запросов",
                    "error_code": "RATE_LIMIT_ERROR",
                    "retry_after": retry_after,
                    "limit": self.calls_per_minute,
                    "window": self.window_size,
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Периодическая очистка (каждые 100 запросов)
        if len(self.request_times) > 0 and len(self.request_times) % 100 == 0:
            self._cleanup_old_entries()

        # Продолжаем обработку запроса
        response = await call_next(request)

        # Добавляем заголовки с информацией о лимитах
        remaining = max(0, self.calls_per_minute - len(self.request_times[client_id]))
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_size))

        return response
