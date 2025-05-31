"""
OptimaAI Bot API - улучшенный основной файл приложения.
Предоставляет API для взаимодействия с ботом на основе OpenAI с улучшенной безопасностью.
"""

import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import ValidationError as PydanticValidationError
import uvicorn

from src.config import Settings, get_settings
from src.services.openai_service import OpenAIService
from src.services.cache_service import CacheService
from src.models.message import (
    ChatRequest, MessageResponse, ErrorResponse, HealthResponse
)
from src.validators.input_validator import (
    validate_request_data, validate_cors_origin
)
from src.security.config_validator import validate_security_config
from src.middleware.logging import RequestLoggingMiddleware
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.auth import AuthMiddleware
from src.middleware.sanitization import SanitizationMiddleware
from src.exceptions import (
    AppBaseException, ValidationError, ConfigurationError,
    OpenAIError, RAGError, CacheError, RateLimitError
)

# Глобальные переменные для сервисов
cache_service: CacheService = None
start_time: float = time.time()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    Инициализация и очистка ресурсов.
    """
    global cache_service
    
    # Инициализация при запуске
    logger.info("Запуск приложения OptimaAI Bot")
    
    try:
        settings = get_settings()
        
        # Инициализация кэша
        if settings.enable_cache:
            cache_service = CacheService(ttl_seconds=settings.cache_ttl_seconds)
            logger.info("Кэш-сервис инициализирован")
        
        # Проверяем конфигурацию безопасности
        security_result = validate_security_config(settings)
        if not security_result["is_secure"]:
            logger.warning("⚠️ Обнаружены проблемы безопасности в конфигурации")
            for issue in security_result["issues"]:
                logger.error(f"🔴 {issue['category']}: {issue['message']}")
        
        logger.info("Приложение успешно запущено")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации приложения: {str(e)}")
        raise ConfigurationError(f"Не удалось инициализировать приложение: {str(e)}")
    
    yield
    
    # Очистка при завершении
    logger.info("Завершение работы приложения")
    if cache_service:
        cache_service.clear_all()
        logger.info("Кэш очищен")


# Инициализация приложения FastAPI
app = FastAPI(
    title="OptimaAI Bot API",
    description="API для взаимодействия с ботом на основе OpenAI с RAG системой",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


def setup_middleware(app: FastAPI, settings: Settings):
    """
    Настройка middleware для приложения.
    
    Args:
        app: Экземпляр FastAPI приложения
        settings: Настройки приложения
    """
    # Валидация CORS origins
    validated_origins = []
    for origin in settings.allowed_origins:
        is_valid, warning = validate_cors_origin(origin)
        if is_valid:
            validated_origins.append(origin)
            if warning:
                logger.warning(f"CORS origin '{origin}': {warning}")
        else:
            logger.error(f"Недопустимый CORS origin '{origin}': {warning}")
    
    if not validated_origins:
        logger.warning("Нет валидных CORS origins, добавляем localhost по умолчанию")
        validated_origins = ["http://localhost:3000"]
    
    # CORS middleware с проверенными настройками
    app.add_middleware(
        CORSMiddleware,
        allow_origins=validated_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        expose_headers=["X-Process-Time", "X-RateLimit-*"]
    )
    
    # Аутентификация (должна быть перед rate limiting)
    app.add_middleware(
        AuthMiddleware,
        api_key=settings.api_key
    )
    
    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        calls_per_minute=settings.rate_limit_per_minute
    )
    
    # Санитизация входных данных
    app.add_middleware(SanitizationMiddleware)
    
    # Логирование запросов (должно быть последним)
    app.add_middleware(RequestLoggingMiddleware)


def setup_exception_handlers(app: FastAPI):
    """
    Настройка обработчиков исключений.
    
    Args:
        app: Экземпляр FastAPI приложения
    """
    
    @app.exception_handler(AppBaseException)
    async def app_exception_handler(request: Request, exc: AppBaseException):
        """Обработчик кастомных исключений приложения."""
        logger.error(f"Ошибка приложения: {exc.message}", extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path
        })
        
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=exc.message,
                error_code=exc.error_code,
                details=exc.details
            ).model_dump()
        )
    
    @app.exception_handler(PydanticValidationError)
    async def validation_exception_handler(request: Request, exc: PydanticValidationError):
        """Обработчик ошибок валидации Pydantic."""
        logger.warning(f"Ошибка валидации: {str(exc)}", extra={
            "path": request.url.path,
            "errors": exc.errors()
        })
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="Ошибка валидации данных",
                error_code="VALIDATION_ERROR",
                details={"validation_errors": exc.errors()}
            ).model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        """Кастомный обработчик HTTP исключений."""
        if exc.status_code == 429:
            # Специальная обработка для rate limiting
            return JSONResponse(
                status_code=429,
                content=exc.detail,
                headers=exc.headers
            )
        
        return await http_exception_handler(request, exc)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Обработчик общих исключений."""
        logger.error(f"Неожиданная ошибка: {str(exc)}", extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }, exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Внутренняя ошибка сервера",
                error_code="INTERNAL_SERVER_ERROR",
                details={"exception_type": type(exc).__name__}
            ).model_dump()
        )


# Настройка приложения
settings = get_settings()
setup_middleware(app, settings)
setup_exception_handlers(app)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка работоспособности API с детальной информацией.
    
    Returns:
        HealthResponse: Статус сервиса и дополнительная информация
    """
    uptime = time.time() - start_time
    
    # Проверка статуса внешних сервисов
    services_status = {}
    
    try:
        # Проверка OpenAI API
        settings = get_settings()
        if settings.openai_api_key:
            services_status["openai"] = "ok"
        else:
            services_status["openai"] = "not_configured"
    except Exception:
        services_status["openai"] = "error"
    
    # Проверка кэша
    if cache_service:
        services_status["cache"] = "ok"
    else:
        services_status["cache"] = "disabled"
    
    return HealthResponse(
        status="ok",
        uptime=uptime,
        services=services_status
    )


@app.post("/chat", response_model=MessageResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Обработка запроса к чат-боту с улучшенной обработкой ошибок.
    
    Args:
        request: Запрос с историей сообщений
        settings: Настройки приложения
        
    Returns:
        MessageResponse: Ответ бота
        
    Raises:
        ValidationError: При некорректных данных запроса
        OpenAIError: При ошибках OpenAI API
        RAGError: При ошибках RAG системы
        CacheError: При ошибках кэширования
    """
    start_time_request = time.time()
    
    try:
        # Проверяем кэш, если использование кэша включено
        cached_response = None
        if request.use_cache and cache_service and settings.enable_cache:
            try:
                cached_response = cache_service.get(request.messages)
                if cached_response:
                    logger.info("Ответ получен из кэша")
                    response = MessageResponse(**cached_response)
                    response.from_cache = True
                    response.processing_time = time.time() - start_time_request
                    return response
            except Exception as e:
                logger.warning(f"Ошибка при получении из кэша: {str(e)}")
                # Продолжаем без кэша
        
        # Если ответа нет в кэше, генерируем новый ответ
        try:
            openai_service = OpenAIService(settings)
            
            # Переопределяем параметры из запроса, если они указаны
            if request.temperature is not None:
                openai_service.temperature = request.temperature
            if request.max_tokens is not None:
                openai_service.max_tokens = request.max_tokens
            
            response = await openai_service.generate_response(
                request.messages, 
                request.stream
            )
            
            # Добавляем информацию о времени обработки и модели
            response.processing_time = time.time() - start_time_request
            response.model = settings.gpt_model
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            raise OpenAIError(
                f"Не удалось сгенерировать ответ: {str(e)}",
                details={"model": settings.gpt_model}
            )
        
        # Сохраняем ответ в кэш, если кэширование включено
        if (request.use_cache and cache_service and 
            settings.enable_cache and not response.from_cache):
            try:
                cache_service.set(request.messages, response.model_dump())
                logger.debug("Ответ сохранён в кэш")
            except Exception as e:
                logger.warning(f"Ошибка при сохранении в кэш: {str(e)}")
                # Не прерываем выполнение из-за ошибки кэширования
        
        return response
        
    except AppBaseException:
        # Перебрасываем кастомные исключения как есть
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка в chat endpoint: {str(e)}", exc_info=True)
        raise OpenAIError(f"Внутренняя ошибка при обработке запроса: {str(e)}")


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Получение статистики кэша.
    
    Returns:
        Dict: Статистика кэша
    """
    if not cache_service:
        raise HTTPException(
            status_code=404, 
            detail="Кэш не инициализирован или отключён"
        )
    
    return {
        "size": len(cache_service._cache),
        "ttl_seconds": cache_service.ttl_seconds,
        "enabled": True
    }


@app.post("/cache/clear")
async def clear_cache():
    """
    Очистка кэша.
    
    Returns:
        Dict: Количество очищенных записей
    """
    if not cache_service:
        raise HTTPException(
            status_code=404, 
            detail="Кэш не инициализирован или отключён"
        )
    
    count = cache_service.clear_all()
    logger.info(f"Кэш очищен, удалено записей: {count}")
    
    return {"cleared_items": count}


@app.post("/cache/clear-expired")
async def clear_expired_cache():
    """
    Очистка устаревших записей кэша.
    
    Returns:
        Dict: Количество очищенных записей
    """
    if not cache_service:
        raise HTTPException(
            status_code=404, 
            detail="Кэш не инициализирован или отключён"
        )
    
    count = cache_service.clear_expired()
    logger.info(f"Очищены устаревшие записи кэша: {count}")
    
    return {"cleared_items": count}


@app.get("/metrics")
async def get_metrics():
    """
    Получение метрик приложения для мониторинга.
    
    Returns:
        Dict: Метрики приложения
    """
    uptime = time.time() - start_time
    
    metrics = {
        "uptime_seconds": uptime,
        "cache_enabled": cache_service is not None,
        "cache_size": len(cache_service._cache) if cache_service else 0,
        "timestamp": datetime.now().isoformat()
    }
    
    return metrics


@app.get("/security/status")
async def get_security_status(
    settings: Settings = Depends(get_settings)
):
    """
    Получение статуса безопасности приложения.
    
    Returns:
        Dict: Статус безопасности
    """
    security_result = validate_security_config(settings)
    
    # Убираем чувствительную информацию для публичного API
    public_result = {
        "is_secure": security_result["is_secure"],
        "security_score": security_result["security_score"],
        "summary": security_result["summary"],
        "issues_count": len(security_result["issues"]),
        "warnings_count": len(security_result["warnings"]),
        "timestamp": datetime.now().isoformat(),
        "features": {
            "cors_configured": len(settings.allowed_origins) > 0,
            "api_key_auth": settings.api_key is not None,
            "rate_limiting": settings.rate_limit_per_minute > 0,
            "cache_enabled": settings.enable_cache,
            "debug_mode": settings.debug
        }
    }
    
    return public_result


if __name__ == "__main__":
    # Проверяем безопасность перед запуском
    security_result = validate_security_config(settings)
    if not security_result["is_secure"]:
        print("\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ БЕЗОПАСНОСТИ!")
        print(f"Оценка: {security_result['security_score']}/100")
        for issue in security_result["issues"]:
            print(f"  • {issue['category']}: {issue['message']}")
        print("\nРекомендуется устранить проблемы перед запуском в продакшен.\n")
    
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug,
        log_level="info"
    )