"""
Middleware для аутентификации и авторизации.
Проверяет API ключи и управляет доступом к эндпоинтам.
"""

import logging
from typing import Optional, Set

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class APIKeyAuth:
    """
    Класс для проверки API ключей.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация аутентификации.

        Args:
            api_key: API ключ для проверки (если None, аутентификация отключена)
        """
        self.api_key = api_key
        self.enabled = api_key is not None and len(api_key.strip()) > 0

        # Публичные эндпоинты, не требующие аутентификации
        self.public_endpoints: Set[str] = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
            "/favicon.ico",
            "/security/status",
        }

        logger.info(
            f"API Key аутентификация: {'включена' if self.enabled else 'отключена'}"
        )

    def is_public_endpoint(self, path: str) -> bool:
        """
        Проверяет, является ли эндпоинт публичным.

        Args:
            path: Путь эндпоинта

        Returns:
            bool: True, если эндпоинт публичный
        """
        return path in self.public_endpoints

    def verify_api_key(self, provided_key: str) -> bool:
        """
        Проверяет корректность API ключа.

        Args:
            provided_key: Предоставленный API ключ

        Returns:
            bool: True, если ключ корректный
        """
        if not self.enabled:
            return True

        return provided_key == self.api_key


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware для проверки аутентификации.
    """

    def __init__(self, app, api_key: Optional[str] = None):
        """
        Инициализация middleware.

        Args:
            app: Экземпляр приложения FastAPI
            api_key: API ключ для аутентификации
        """
        super().__init__(app)
        self.auth = APIKeyAuth(api_key)

    async def dispatch(self, request: Request, call_next):
        """
        Обработка запроса с проверкой аутентификации.

        Args:
            request: HTTP запрос
            call_next: Следующий обработчик в цепочке

        Returns:
            Response: HTTP ответ
        """
        # Проверяем, нужна ли аутентификация
        if not self.auth.enabled or self.auth.is_public_endpoint(request.url.path):
            return await call_next(request)

        # Получаем API ключ из заголовков
        api_key = self._extract_api_key(request)

        if not api_key:
            logger.warning(f"Отсутствует API ключ для {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "API ключ обязателен",
                    "error_code": "MISSING_API_KEY",
                    "details": {
                        "required_header": "Authorization: Bearer <api_key> или X-API-Key: <api_key>"
                    },
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем корректность API ключа
        if not self.auth.verify_api_key(api_key):
            logger.warning(f"Неверный API ключ для {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Неверный API ключ",
                    "error_code": "INVALID_API_KEY",
                    "details": {"message": "Предоставленный API ключ недействителен"},
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Логируем успешную аутентификацию
        logger.info(f"Успешная аутентификация для {request.url.path}")

        # Продолжаем обработку запроса
        response = await call_next(request)
        return response

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Извлекает API ключ из заголовков запроса.

        Args:
            request: HTTP запрос

        Returns:
            Optional[str]: API ключ или None
        """
        # Проверяем заголовок Authorization (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Убираем "Bearer "

        # Проверяем заголовок X-API-Key
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            return api_key_header

        # Проверяем query параметр (менее безопасно, но для совместимости)
        api_key_param = request.query_params.get("api_key")
        if api_key_param:
            logger.warning("API ключ передан через query параметр - небезопасно!")
            return api_key_param

        return None


# Dependency для FastAPI
security = HTTPBearer(auto_error=False)


async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> Optional[str]:
    """
    Dependency для получения API ключа в FastAPI эндпоинтах.

    Args:
        credentials: Учетные данные из заголовка Authorization

    Returns:
        Optional[str]: API ключ или None
    """
    if credentials:
        return credentials.credentials
    return None


def require_api_key(api_key: str, valid_api_key: Optional[str]) -> bool:
    """
    Проверяет корректность API ключа.

    Args:
        api_key: Предоставленный API ключ
        valid_api_key: Действительный API ключ

    Returns:
        bool: True, если ключ корректный

    Raises:
        HTTPException: Если ключ неверный или отсутствует
    """
    if not valid_api_key:
        return True  # Аутентификация отключена

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API ключ обязателен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if api_key != valid_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API ключ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
