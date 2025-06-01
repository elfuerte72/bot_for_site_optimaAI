"""
Middleware для санитизации пользовательского ввода.
Защищает от XSS, SQL injection и других атак.
"""

import html
import json
import logging
import re
from typing import Any, Dict, List, Union

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class InputSanitizer:
    """
    Класс для санитизации пользовательского ввода.
    """

    def __init__(self):
        """Инициализация санитайзера."""
        # Паттерны для обнаружения потенциально опасного контента
        self.dangerous_patterns = [
            # JavaScript
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            # SQL injection
            re.compile(
                r"\b(union|select|insert|update|delete|drop|create|alter)\b",
                re.IGNORECASE,
            ),
            re.compile(r'[\'";].*(-{2}|/\*|\*/)', re.IGNORECASE),
            # Command injection
            re.compile(r"[;&|`$(){}[\]\\]"),
            # Path traversal
            re.compile(r"\.\./"),
            re.compile(r"\.\.\\\\"),
            # HTML injection
            re.compile(r"<[^>]*>", re.IGNORECASE),
        ]

        # Максимальные длины для разных типов полей
        self.max_lengths = {
            "message_content": 32000,
            "general_string": 1000,
            "short_string": 255,
            "url": 2048,
        }

    def sanitize_string(self, value: str, field_type: str = "general_string") -> str:
        """
        Санитизация строкового значения.

        Args:
            value: Строка для санитизации
            field_type: Тип поля для определения лимитов

        Returns:
            str: Санитизированная строка
        """
        if not isinstance(value, str):
            return str(value)

        # Удаляем null байты
        value = value.replace("\x00", "")

        # Ограничиваем длину
        max_length = self.max_lengths.get(
            field_type, self.max_lengths["general_string"]
        )
        if len(value) > max_length:
            logger.warning(f"Строка обрезана с {len(value)} до {max_length} символов")
            value = value[:max_length]

        # Экранируем HTML
        value = html.escape(value, quote=True)

        # Проверяем на опасные паттерны
        for pattern in self.dangerous_patterns:
            if pattern.search(value):
                logger.warning(
                    f"Обнаружен потенциально опасный контент: {pattern.pattern}"
                )
                # Удаляем опасный контент
                value = pattern.sub("", value)

        # Удаляем лишние пробелы
        value = " ".join(value.split())

        return value

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рекурсивная санитизация словаря.

        Args:
            data: Словарь для санитизации

        Returns:
            Dict[str, Any]: Санитизированный словарь
        """
        sanitized = {}

        for key, value in data.items():
            # Санитизируем ключ
            clean_key = self.sanitize_string(str(key), "short_string")

            # Санитизируем значение
            if isinstance(value, str):
                # Определяем тип поля по ключу
                field_type = self._get_field_type(clean_key)
                sanitized[clean_key] = self.sanitize_string(value, field_type)
            elif isinstance(value, dict):
                sanitized[clean_key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[clean_key] = self.sanitize_list(value)
            else:
                sanitized[clean_key] = value

        return sanitized

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Санитизация списка.

        Args:
            data: Список для санитизации

        Returns:
            List[Any]: Санитизированный список
        """
        sanitized = []

        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)

        return sanitized

    def _get_field_type(self, field_name: str) -> str:
        """
        Определяет тип поля по его имени.

        Args:
            field_name: Имя поля

        Returns:
            str: Тип поля
        """
        field_name_lower = field_name.lower()

        if "content" in field_name_lower or "message" in field_name_lower:
            return "message_content"
        elif "url" in field_name_lower or "link" in field_name_lower:
            return "url"
        elif any(word in field_name_lower for word in ["name", "title", "id"]):
            return "short_string"
        else:
            return "general_string"


class SanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware для санитизации входящих данных.
    """

    def __init__(self, app):
        """
        Инициализация middleware.

        Args:
            app: Экземпляр приложения FastAPI
        """
        super().__init__(app)
        self.sanitizer = InputSanitizer()

        # Эндпоинты, которые не требуют санитизации
        self.excluded_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
        }

    async def dispatch(self, request: Request, call_next):
        """
        Обработка запроса с санитизацией данных.

        Args:
            request: HTTP запрос
            call_next: Следующий обработчик в цепочке

        Returns:
            Response: HTTP ответ
        """
        # Проверяем, нужна ли санитизация
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Санитизируем только POST запросы с JSON данными
        if request.method == "POST" and "application/json" in request.headers.get(
            "content-type", ""
        ):
            try:
                # Читаем тело запроса
                body = await request.body()

                if body:
                    # Парсим JSON
                    try:
                        data = json.loads(body.decode("utf-8"))

                        # Санитизируем данные
                        sanitized_data = self._sanitize_request_data(data)

                        # Создаем новый запрос с санитизированными данными
                        sanitized_body = json.dumps(sanitized_data).encode("utf-8")

                        # Заменяем тело запроса
                        async def receive():
                            return {
                                "type": "http.request",
                                "body": sanitized_body,
                                "more_body": False,
                            }

                        request._receive = receive

                        logger.debug("Данные запроса санитизированы")

                    except json.JSONDecodeError:
                        logger.warning("Не удалось распарсить JSON в запросе")
                        # Продолжаем без санитизации

            except Exception as e:
                logger.error(f"Ошибка при санитизации запроса: {str(e)}")
                # Продолжаем без санитизации

        # Продолжаем обработку запроса
        response = await call_next(request)
        return response

    def _sanitize_request_data(self, data: Any) -> Any:
        """
        Санитизация данных запроса.

        Args:
            data: Данные для санитизации

        Returns:
            Any: Санитизированные данные
        """
        if isinstance(data, dict):
            return self.sanitizer.sanitize_dict(data)
        elif isinstance(data, list):
            return self.sanitizer.sanitize_list(data)
        elif isinstance(data, str):
            return self.sanitizer.sanitize_string(data)
        else:
            return data


def sanitize_input(value: Any, field_type: str = "general_string") -> Any:
    """
    Функция для ручной санитизации входных данных.

    Args:
        value: Значение для санитизации
        field_type: Тип поля

    Returns:
        Any: Санитизированное значение
    """
    sanitizer = InputSanitizer()

    if isinstance(value, str):
        return sanitizer.sanitize_string(value, field_type)
    elif isinstance(value, dict):
        return sanitizer.sanitize_dict(value)
    elif isinstance(value, list):
        return sanitizer.sanitize_list(value)
    else:
        return value
