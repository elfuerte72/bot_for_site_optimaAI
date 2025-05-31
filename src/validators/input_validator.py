"""
Расширенная валидация входных данных.
Дополнительные проверки безопасности и корректности данных.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import ValidationError, validator

from src.models.message import ChatRequest, Message, MessageRole

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Класс для проверки безопасности входных данных.
    """

    def __init__(self):
        """Инициализация валидатора."""
        # Запрещенные слова и фразы
        self.forbidden_patterns = [
            # Попытки обхода системы
            r"\b(ignore|forget|disregard)\s+(previous|above|system|instructions?)\b",
            r"\b(act\s+as|pretend\s+to\s+be|roleplay)\b",
            r"\b(jailbreak|prompt\s+injection)\b",
            # Попытки получения системной информации
            r"\b(system\s+prompt|internal\s+instructions?)\b",
            r"\b(show\s+me\s+your|reveal\s+your)\s+(prompt|instructions?|code)\b",
            # Вредоносные команды
            r"\b(rm\s+-rf|del\s+/|format\s+c:)\b",
            r"\b(sudo|chmod|passwd)\b",
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.forbidden_patterns
        ]

        # Максимальные лимиты
        self.max_message_length = 32000
        self.max_messages_count = 50
        self.max_consecutive_user_messages = 5

    def validate_message_content(self, content: str) -> tuple[bool, Optional[str]]:
        """
        Проверяет содержимое сообщения на безопасность.

        Args:
            content: Содержимое сообщения

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Проверка длины
        if len(content) > self.max_message_length:
            return (
                False,
                f"Сообщение слишком длинное (максимум {self.max_message_length} символов)",
            )

        # Проверка на пустое содержимое
        if not content.strip():
            return False, "Сообщение не может быть пустым"

        # Проверка на запрещенные паттерны
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                logger.warning(f"Обнаружен подозрительный контент: {pattern.pattern}")
                return False, "Сообщение содержит недопустимый контент"

        # Проверка на чрезмерное повторение символов
        if self._has_excessive_repetition(content):
            return False, "Сообщение содержит чрезмерное повторение символов"

        return True, None

    def validate_messages_sequence(
        self, messages: List[Message]
    ) -> tuple[bool, Optional[str]]:
        """
        Проверяет последовательность сообщений.

        Args:
            messages: Список сообщений

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if len(messages) > self.max_messages_count:
            return (
                False,
                f"Слишком много сообщений (максимум {self.max_messages_count})",
            )

        # Проверка на последовательные сообщения пользователя
        consecutive_user_count = 0
        for message in reversed(messages):
            if message.role == MessageRole.USER:
                consecutive_user_count += 1
            else:
                break

        if consecutive_user_count > self.max_consecutive_user_messages:
            return (
                False,
                f"Слишком много последовательных сообщений пользователя (максимум {self.max_consecutive_user_messages})",
            )

        # Проверка структуры диалога
        system_count = sum(1 for msg in messages if msg.role == MessageRole.SYSTEM)
        if system_count > 1:
            return False, "Может быть только одно системное сообщение"

        if system_count == 1 and messages[0].role != MessageRole.SYSTEM:
            return False, "Системное сообщение должно быть первым"

        return True, None

    def _has_excessive_repetition(self, content: str, max_repetition: int = 50) -> bool:
        """
        Проверяет на чрезмерное повторение символов или слов.

        Args:
            content: Содержимое для проверки
            max_repetition: Максимальное количество повторений

        Returns:
            bool: True, если есть чрезмерное повторение
        """
        # Проверка повторения символов
        for char in set(content):
            if content.count(char) > max_repetition and char not in " \n\t":
                return True

        # Проверка повторения слов
        words = content.split()
        for word in set(words):
            if len(word) > 2 and words.count(word) > max_repetition // 5:
                return True

        return False


class EnhancedChatRequest(ChatRequest):
    """
    Расширенная модель запроса с дополнительной валидацией.
    """

    @validator("messages")
    def validate_messages_security(cls, v):
        """Дополнительная валидация безопасности сообщений."""
        security_validator = SecurityValidator()

        # Проверяем каждое сообщение
        for message in v:
            is_valid, error = security_validator.validate_message_content(
                message.content
            )
            if not is_valid:
                raise ValueError(f"Небезопасное сообщение: {error}")

        # Проверяем последовательность сообщений
        is_valid, error = security_validator.validate_messages_sequence(v)
        if not is_valid:
            raise ValueError(f"Некорректная последовательность сообщений: {error}")

        return v

    @validator("temperature")
    def validate_temperature_range(cls, v):
        """Дополнительная валидация температуры."""
        if v is not None:
            if v < 0.0 or v > 2.0:
                raise ValueError("Температура должна быть в диапазоне от 0.0 до 2.0")
            # Предупреждение о крайних значениях
            if v > 1.5:
                logger.warning(f"Высокая температура: {v}")
        return v

    @validator("max_tokens")
    def validate_max_tokens_range(cls, v):
        """Дополнительная валидация максимального количества токенов."""
        if v is not None:
            if v < 1 or v > 4000:
                raise ValueError("max_tokens должно быть в диапазоне от 1 до 4000")
            # Предупреждение о больших значениях
            if v > 2000:
                logger.warning(f"Большое количество токенов: {v}")
        return v


def validate_request_data(
    data: Dict[str, Any],
) -> tuple[bool, Optional[str], Optional[EnhancedChatRequest]]:
    """
    Валидация данных запроса.

    Args:
        data: Данные запроса

    Returns:
        tuple[bool, Optional[str], Optional[EnhancedChatRequest]]:
        (is_valid, error_message, validated_request)
    """
    try:
        # Создаем и валидируем запрос
        validated_request = EnhancedChatRequest(**data)
        return True, None, validated_request

    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")

        error_message = "Ошибки валидации: " + "; ".join(error_details)
        logger.warning(f"Ошибка валидации запроса: {error_message}")
        return False, error_message, None

    except Exception as e:
        error_message = f"Неожиданная ошибка валидации: {str(e)}"
        logger.error(error_message)
        return False, error_message, None


def validate_api_key_format(api_key: str) -> tuple[bool, Optional[str]]:
    """
    Валидация формата API ключа.

    Args:
        api_key: API ключ для проверки

    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not api_key:
        return False, "API ключ не может быть пустым"

    # Минимальная длина
    if len(api_key) < 10:
        return False, "API ключ слишком короткий (минимум 10 символов)"

    # Максимальная длина
    if len(api_key) > 200:
        return False, "API ключ слишком длинный (максимум 200 символов)"

    # Проверка на допустимые символы
    if not re.match(r"^[a-zA-Z0-9\-_\.]+$", api_key):
        return False, "API ключ содержит недопустимые символы"

    return True, None


def validate_cors_origin(origin: str) -> tuple[bool, Optional[str]]:
    """
    Валидация CORS origin.

    Args:
        origin: Origin для проверки

    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not origin:
        return False, "Origin не может быть пустым"

    # Проверка на wildcard (небезопасно в продакшене)
    if origin == "*":
        logger.warning("Использование '*' для CORS небезопасно в продакшене")
        return True, "Wildcard CORS небезопасен"

    # Проверка формата URL
    url_pattern = re.compile(
        r"^https?://"  # http:// или https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # домен
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP адрес
        r"(?::\d+)?"  # порт
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(origin):
        return False, "Некорректный формат origin"

    return True, None
