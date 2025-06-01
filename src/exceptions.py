"""
Кастомные исключения для приложения.
"""

from typing import Any, Dict, Optional


class AppBaseException(Exception):
    """Базовое исключение приложения."""

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppBaseException):
    """Ошибка валидации данных."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, error_code="VALIDATION_ERROR", details=details
        )


class ConfigurationError(AppBaseException):
    """Ошибка конфигурации."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, error_code="CONFIGURATION_ERROR", details=details
        )


class OpenAIError(AppBaseException):
    """Ошибка при работе с OpenAI API."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="OPENAI_ERROR", details=details)


class RAGError(AppBaseException):
    """Ошибка при работе с RAG системой."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="RAG_ERROR", details=details)


class CacheError(AppBaseException):
    """Ошибка при работе с кэшем."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="CACHE_ERROR", details=details)


class RateLimitError(AppBaseException):
    """Ошибка превышения лимита запросов."""

    def __init__(
        self,
        message: str = "Превышен лимит запросов",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, error_code="RATE_LIMIT_ERROR", details=details
        )


class AuthenticationError(AppBaseException):
    """Ошибка аутентификации."""

    def __init__(
        self,
        message: str = "Ошибка аутентификации",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, error_code="AUTHENTICATION_ERROR", details=details
        )
