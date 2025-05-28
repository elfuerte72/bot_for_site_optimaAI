"""
Middleware для логирования запросов и ответов API.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования входящих запросов и ответов.
    Отслеживает время выполнения запросов и логирует основную информацию.
    """
    
    def __init__(self, app):
        """
        Инициализация middleware.
        
        Args:
            app: Экземпляр приложения FastAPI
        """
        super().__init__(app)
        self.logger = logging.getLogger("api")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с логированием.
        
        Args:
            request: Входящий HTTP запрос
            call_next: Функция для передачи запроса следующему обработчику
            
        Returns:
            Response: HTTP ответ
        """
        start_time = time.time()
        
        # Логирование запроса
        client_host = request.client.host if request.client else "unknown"
        self.logger.info(
            f"Request: {request.method} {request.url.path} from {client_host}"
        )
        
        # Обработка запроса
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Логирование ответа
            self.logger.info(
                f"Response: {request.method} {request.url.path} "
                f"completed in {process_time:.3f}s with status {response.status_code}"
            )
            
            # Добавление заголовка с временем обработки запроса
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(
                f"Error: {request.method} {request.url.path} "
                f"failed after {process_time:.3f}s: {str(e)}"
            )
            raise
