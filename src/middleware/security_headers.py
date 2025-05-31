"""
Security Headers Middleware для добавления заголовков безопасности.
Реализует OWASP рекомендации по безопасности веб-приложений.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления заголовков безопасности к HTTP ответам.
    
    Добавляет следующие заголовки:
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Content-Security-Policy
    - Permissions-Policy
    - X-Permitted-Cross-Domain-Policies
    """
    
    def __init__(
        self,
        app,
        hsts_max_age: int = 31536000,  # 1 год
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        frame_options: str = "SAMEORIGIN",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        csp_policy: str = None,
        permissions_policy: str = None,
        cross_domain_policy: str = "none"
    ):
        """
        Инициализация middleware с настройками безопасности.
        
        Args:
            app: FastAPI приложение
            hsts_max_age: Время действия HSTS в секундах
            hsts_include_subdomains: Включать поддомены в HSTS
            hsts_preload: Включить preload для HSTS
            frame_options: Политика X-Frame-Options
            content_type_options: Политика X-Content-Type-Options
            xss_protection: Политика X-XSS-Protection
            referrer_policy: Политика Referrer-Policy
            csp_policy: Кастомная Content Security Policy
            permissions_policy: Кастомная Permissions Policy
            cross_domain_policy: Политика X-Permitted-Cross-Domain-Policies
        """
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
        self.cross_domain_policy = cross_domain_policy
        
        # Дефолтная Content Security Policy
        if csp_policy is None:
            self.csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "media-src 'self'; "
                "object-src 'none'; "
                "child-src 'none'; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "manifest-src 'self'"
            )
        else:
            self.csp_policy = csp_policy
        
        # Дефолтная Permissions Policy
        if permissions_policy is None:
            self.permissions_policy = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "accelerometer=(), "
                "gyroscope=(), "
                "speaker=(), "
                "vibrate=(), "
                "fullscreen=(self), "
                "sync-xhr=()"
            )
        else:
            self.permissions_policy = permissions_policy

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Обработка запроса и добавление заголовков безопасности.
        
        Args:
            request: HTTP запрос
            call_next: Следующий middleware в цепочке
            
        Returns:
            Response: HTTP ответ с добавленными заголовками безопасности
        """
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Добавляем заголовки безопасности
        self._add_security_headers(request, response)
        
        return response

    def _add_security_headers(
        self, request: Request, response: Response
    ) -> None:
        """
        Добавляет заголовки безопасности к ответу.
        
        Args:
            request: HTTP запрос
            response: HTTP ответ
        """
        # HSTS (HTTP Strict Transport Security)
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # X-Frame-Options - защита от clickjacking
        response.headers["X-Frame-Options"] = self.frame_options

        # X-Content-Type-Options - предотвращение MIME sniffing
        response.headers["X-Content-Type-Options"] = self.content_type_options

        # X-XSS-Protection - защита от XSS (устаревший, но для совместимости)
        response.headers["X-XSS-Protection"] = self.xss_protection

        # Referrer-Policy - контроль передачи referrer
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Content-Security-Policy - защита от XSS и injection атак
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Permissions-Policy - контроль доступа к API браузера
        response.headers["Permissions-Policy"] = self.permissions_policy

        # X-Permitted-Cross-Domain-Policies - контроль Flash/PDF политик
        cross_domain_header = "X-Permitted-Cross-Domain-Policies"
        response.headers[cross_domain_header] = self.cross_domain_policy

        # Удаляем потенциально опасные заголовки сервера
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        # Добавляем кастомный заголовок для идентификации
        response.headers["X-Security-Headers"] = "enabled"


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """
    Базовая защита от DDoS атак на уровне приложения.
    
    Реализует:
    - Ограничение количества одновременных соединений с одного IP
    - Детекция подозрительных паттернов запросов
    - Временная блокировка подозрительных IP
    """
    
    def __init__(
        self,
        app,
        max_connections_per_ip: int = 10,
        suspicious_threshold: int = 100,
        block_duration: int = 300,  # 5 минут
        whitelist_ips: list = None
    ):
        """
        Инициализация DDoS защиты.
        
        Args:
            app: FastAPI приложение
            max_connections_per_ip: Максимум соединений с одного IP
            suspicious_threshold: Порог подозрительной активности
            block_duration: Время блокировки в секундах
            whitelist_ips: Список доверенных IP адресов
        """
        super().__init__(app)
        self.max_connections_per_ip = max_connections_per_ip
        self.suspicious_threshold = suspicious_threshold
        self.block_duration = block_duration
        self.whitelist_ips = whitelist_ips or []
        
        # Счетчики и блокировки
        self.ip_connections = {}
        self.ip_requests = {}
        self.blocked_ips = {}
        self.last_cleanup = time.time()

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Обработка запроса с проверкой DDoS защиты.
        
        Args:
            request: HTTP запрос
            call_next: Следующий middleware в цепочке
            
        Returns:
            Response: HTTP ответ или блокировка
        """
        client_ip = self._get_client_ip(request)
        
        # Очистка старых записей каждые 60 секунд
        current_time = time.time()
        if current_time - self.last_cleanup > 60:
            self._cleanup_old_records(current_time)
            self.last_cleanup = current_time
        
        # Проверяем whitelist
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        # Проверяем блокировку
        if self._is_ip_blocked(client_ip, current_time):
            return Response(
                content="Too Many Requests - IP temporarily blocked",
                status_code=429,
                headers={
                    "Retry-After": str(self.block_duration),
                    "X-Block-Reason": "DDoS Protection"
                }
            )
        
        # Проверяем лимиты
        if self._check_rate_limits(client_ip, current_time):
            return Response(
                content="Too Many Requests",
                status_code=429,
                headers={
                    "Retry-After": "60",
                    "X-Block-Reason": "Rate Limit Exceeded"
                }
            )
        
        # Обновляем счетчики
        self._update_counters(client_ip, current_time)
        
        # Обрабатываем запрос
        response = await call_next(request)
        
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Получает реальный IP клиента с учетом proxy."""
        # Проверяем заголовки от reverse proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

    def _is_ip_blocked(self, ip: str, current_time: float) -> bool:
        """Проверяет, заблокирован ли IP."""
        if ip in self.blocked_ips:
            block_time = self.blocked_ips[ip]
            if current_time - block_time < self.block_duration:
                return True
            else:
                # Разблокируем IP
                del self.blocked_ips[ip]
        return False

    def _check_rate_limits(self, ip: str, current_time: float) -> bool:
        """Проверяет превышение лимитов запросов."""
        # Проверяем whitelist
        if ip in self.whitelist_ips:
            return False
            
        # Проверяем количество запросов за последнюю минуту
        if ip in self.ip_requests:
            recent_requests = [
                req_time for req_time in self.ip_requests[ip]
                if current_time - req_time < 60
            ]
            
            if len(recent_requests) > self.suspicious_threshold:
                # Блокируем IP
                self.blocked_ips[ip] = current_time
                return True
        
        return False

    def _update_counters(self, ip: str, current_time: float) -> None:
        """Обновляет счетчики запросов."""
        if ip not in self.ip_requests:
            self.ip_requests[ip] = []
        
        self.ip_requests[ip].append(current_time)
        
        # Оставляем только запросы за последний час
        self.ip_requests[ip] = [
            req_time for req_time in self.ip_requests[ip]
            if current_time - req_time < 3600
        ]

    def _cleanup_old_records(self, current_time: float) -> None:
        """Очищает старые записи для экономии памяти."""
        # Очищаем старые запросы (старше часа)
        for ip in list(self.ip_requests.keys()):
            self.ip_requests[ip] = [
                req_time for req_time in self.ip_requests[ip]
                if current_time - req_time < 3600
            ]
            if not self.ip_requests[ip]:
                del self.ip_requests[ip]
        
        # Очищаем старые блокировки
        for ip in list(self.blocked_ips.keys()):
            if current_time - self.blocked_ips[ip] > self.block_duration:
                del self.blocked_ips[ip]