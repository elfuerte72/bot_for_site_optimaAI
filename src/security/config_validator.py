"""
Валидатор конфигурации безопасности.
Проверяет настройки приложения на соответствие требованиям безопасности.
"""

import logging
from typing import Any, Dict, List, Tuple

from src.config import Settings
from src.validators.input_validator import validate_api_key_format, validate_cors_origin

logger = logging.getLogger(__name__)


class SecurityConfigValidator:
    """
    Класс для валидации конфигурации безопасности.
    """

    def __init__(self):
        """Инициализация валидатора."""
        self.issues = []
        self.warnings = []
        self.recommendations = []

    def validate_settings(self, settings: Settings) -> Dict[str, Any]:
        """
        Полная валидация настроек безопасности.

        Args:
            settings: Настройки приложения

        Returns:
            Dict[str, Any]: Результат валидации
        """
        self.issues = []
        self.warnings = []
        self.recommendations = []

        # Проверяем различные аспекты безопасности
        self._validate_cors_settings(settings)
        self._validate_api_key_settings(settings)
        self._validate_rate_limiting(settings)
        self._validate_debug_settings(settings)
        self._validate_openai_settings(settings)
        self._validate_cache_settings(settings)

        # Формируем результат
        result = {
            "is_secure": len(self.issues) == 0,
            "security_score": self._calculate_security_score(),
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "summary": self._generate_summary(),
        }

        return result

    def _validate_cors_settings(self, settings: Settings):
        """Валидация настроек CORS."""
        if not settings.allowed_origins:
            self.issues.append(
                {
                    "category": "CORS",
                    "severity": "HIGH",
                    "message": "Не настроены разрешённые домены для CORS",
                    "recommendation": "Добавьте конкретные домены в ALLOWED_ORIGINS",
                }
            )
            return

        # Проверяем каждый origin
        for origin in settings.allowed_origins:
            if origin == "*":
                self.issues.append(
                    {
                        "category": "CORS",
                        "severity": "CRITICAL",
                        "message": "Использование '*' для CORS крайне небезопасно",
                        "recommendation": "Замените '*' на конкретные домены",
                    }
                )
            else:
                is_valid, error = validate_cors_origin(origin)
                if not is_valid:
                    self.warnings.append(
                        {
                            "category": "CORS",
                            "message": f"Некорректный CORS origin '{origin}': {error}",
                        }
                    )

        # Проверяем на localhost в продакшене
        localhost_origins = [o for o in settings.allowed_origins if "localhost" in o]
        if localhost_origins and not settings.debug:
            self.warnings.append(
                {
                    "category": "CORS",
                    "message": f"Localhost origins в продакшене: {localhost_origins}",
                    "recommendation": "Удалите localhost origins для продакшена",
                }
            )

    def _validate_api_key_settings(self, settings: Settings):
        """Валидация настроек API ключа."""
        if not settings.api_key:
            self.warnings.append(
                {
                    "category": "Authentication",
                    "message": "API ключ не настроен - аутентификация отключена",
                    "recommendation": "Настройте API_KEY для защиты эндпоинтов",
                }
            )
        else:
            # Проверяем формат API ключа
            is_valid, error = validate_api_key_format(settings.api_key)
            if not is_valid:
                self.issues.append(
                    {
                        "category": "Authentication",
                        "severity": "HIGH",
                        "message": f"Некорректный формат API ключа: {error}",
                        "recommendation": "Используйте надёжный API ключ",
                    }
                )

            # Проверяем на слабые ключи
            if len(settings.api_key) < 32:
                self.warnings.append(
                    {
                        "category": "Authentication",
                        "message": "API ключ короче 32 символов",
                        "recommendation": "Используйте более длинный API ключ",
                    }
                )

            # Проверяем на простые паттерны
            if settings.api_key.lower() in [
                "test",
                "demo",
                "example",
                "your_api_key_here",
            ]:
                self.issues.append(
                    {
                        "category": "Authentication",
                        "severity": "CRITICAL",
                        "message": "Используется тестовый/демо API ключ",
                        "recommendation": "Замените на реальный безопасный API ключ",
                    }
                )

    def _validate_rate_limiting(self, settings: Settings):
        """Валидация настроек rate limiting."""
        if settings.rate_limit_per_minute <= 0:
            self.issues.append(
                {
                    "category": "Rate Limiting",
                    "severity": "HIGH",
                    "message": "Rate limiting отключён",
                    "recommendation": "Установите разумный лимит (например, 100 запросов/мин)",
                }
            )
        elif settings.rate_limit_per_minute > 1000:
            self.warnings.append(
                {
                    "category": "Rate Limiting",
                    "message": f"Очень высокий лимит: {settings.rate_limit_per_minute} запросов/мин",
                    "recommendation": "Рассмотрите снижение лимита для защиты от злоупотреблений",
                }
            )
        elif settings.rate_limit_per_minute < 10:
            self.warnings.append(
                {
                    "category": "Rate Limiting",
                    "message": f"Очень низкий лимит: {settings.rate_limit_per_minute} запросов/мин",
                    "recommendation": "Убедитесь, что лимит не слишком строгий для пользователей",
                }
            )

    def _validate_debug_settings(self, settings: Settings):
        """Валидация настроек отладки."""
        if settings.debug:
            self.warnings.append(
                {
                    "category": "Debug",
                    "message": "Режим отладки включён",
                    "recommendation": "Отключите DEBUG=false в продакшене",
                }
            )

    def _validate_openai_settings(self, settings: Settings):
        """Валидация настроек OpenAI."""
        if not settings.openai_api_key:
            self.issues.append(
                {
                    "category": "OpenAI",
                    "severity": "CRITICAL",
                    "message": "OpenAI API ключ не настроен",
                    "recommendation": "Добавьте OPENAI_API_KEY в переменные окружения",
                }
            )
        elif (
            settings.openai_api_key.startswith("your_")
            or "example" in settings.openai_api_key.lower()
        ):
            self.issues.append(
                {
                    "category": "OpenAI",
                    "severity": "CRITICAL",
                    "message": "Используется тестовый OpenAI API ключ",
                    "recommendation": "Замените на реальный OpenAI API ключ",
                }
            )

        # Проверяем параметры модели
        if settings.temperature > 1.5:
            self.warnings.append(
                {
                    "category": "OpenAI",
                    "message": f"Высокая температура: {settings.temperature}",
                    "recommendation": "Рассмотрите снижение температуры для более стабильных ответов",
                }
            )

        if settings.max_tokens > 2000:
            self.warnings.append(
                {
                    "category": "OpenAI",
                    "message": f"Большое количество токенов: {settings.max_tokens}",
                    "recommendation": "Большие значения увеличивают стоимость запросов",
                }
            )

    def _validate_cache_settings(self, settings: Settings):
        """Валидация настроек кэширования."""
        if settings.enable_cache:
            if settings.cache_ttl_seconds < 60:
                self.warnings.append(
                    {
                        "category": "Cache",
                        "message": f"Очень короткий TTL кэша: {settings.cache_ttl_seconds} сек",
                        "recommendation": "Рассмотрите увеличение TTL для лучшей производительности",
                    }
                )
            elif settings.cache_ttl_seconds > 86400:  # 24 часа
                self.warnings.append(
                    {
                        "category": "Cache",
                        "message": f"Очень длинный TTL кэша: {settings.cache_ttl_seconds} сек",
                        "recommendation": "Длинный TTL может привести к устаревшим данным",
                    }
                )

    def _calculate_security_score(self) -> int:
        """
        Вычисляет оценку безопасности от 0 до 100.

        Returns:
            int: Оценка безопасности
        """
        score = 100

        # Снижаем за критические проблемы
        critical_issues = [i for i in self.issues if i.get("severity") == "CRITICAL"]
        score -= len(critical_issues) * 30

        # Снижаем за высокие проблемы
        high_issues = [i for i in self.issues if i.get("severity") == "HIGH"]
        score -= len(high_issues) * 20

        # Снижаем за обычные проблемы
        normal_issues = [
            i for i in self.issues if i.get("severity") not in ["CRITICAL", "HIGH"]
        ]
        score -= len(normal_issues) * 10

        # Снижаем за предупреждения
        score -= len(self.warnings) * 5

        return max(0, score)

    def _generate_summary(self) -> str:
        """
        Генерирует краткое резюме проверки безопасности.

        Returns:
            str: Резюме
        """
        score = self._calculate_security_score()

        if score >= 90:
            status = "ОТЛИЧНО"
        elif score >= 70:
            status = "ХОРОШО"
        elif score >= 50:
            status = "УДОВЛЕТВОРИТЕЛЬНО"
        else:
            status = "ТРЕБУЕТ ВНИМАНИЯ"

        critical_count = len(
            [i for i in self.issues if i.get("severity") == "CRITICAL"]
        )
        high_count = len([i for i in self.issues if i.get("severity") == "HIGH"])

        summary = f"Оценка безопасности: {score}/100 ({status}). "

        if critical_count > 0:
            summary += f"Критических проблем: {critical_count}. "
        if high_count > 0:
            summary += f"Серьёзных проблем: {high_count}. "
        if len(self.warnings) > 0:
            summary += f"Предупреждений: {len(self.warnings)}."

        return summary


def validate_security_config(settings: Settings) -> Dict[str, Any]:
    """
    Проверяет конфигурацию безопасности.

    Args:
        settings: Настройки приложения

    Returns:
        Dict[str, Any]: Результат проверки
    """
    validator = SecurityConfigValidator()
    result = validator.validate_settings(settings)

    # Логируем результаты
    if result["is_secure"]:
        logger.info(f"✅ {result['summary']}")
    else:
        logger.warning(f"⚠️ {result['summary']}")

        for issue in result["issues"]:
            severity = issue.get("severity", "MEDIUM")
            logger.error(f"🔴 [{severity}] {issue['category']}: {issue['message']}")

        for warning in result["warnings"]:
            logger.warning(f"🟡 {warning['category']}: {warning['message']}")

    return result
