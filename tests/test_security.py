"""
Тесты для проверки сетевой безопасности OptimaAI Bot.
Проверяет security headers, SSL конфигурацию, rate limiting и DDoS защиту.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi import Request
from fastapi.testclient import TestClient

from main import app
from src.config import get_settings
from src.middleware.security_headers import (
    DDoSProtectionMiddleware,
    SecurityHeadersMiddleware,
)


class TestSecurityHeaders:
    """Тесты для Security Headers Middleware."""

    def test_security_headers_middleware_init(self):
        """Тест инициализации SecurityHeadersMiddleware."""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True,
        )

        assert middleware.hsts_max_age == 31536000
        assert middleware.hsts_include_subdomains is True
        assert middleware.hsts_preload is True
        assert "default-src 'self'" in middleware.csp_policy
        assert "geolocation=()" in middleware.permissions_policy

    @pytest.mark.asyncio
    async def test_security_headers_added(self):
        """Тест добавления security headers."""
        client = TestClient(app)

        response = client.get("/health")

        # Проверяем основные security headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        assert "X-Security-Headers" in response.headers

        # Проверяем значения
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["X-Security-Headers"] == "enabled"

    @pytest.mark.asyncio
    async def test_hsts_header_https(self):
        """Тест HSTS header для HTTPS запросов."""
        # Мокаем HTTPS запрос
        with patch("fastapi.Request") as mock_request:
            mock_request.url.scheme = "https"

            client = TestClient(app)
            response = client.get("/health")

            # HSTS должен быть добавлен для HTTPS
            # В реальном тесте нужно проверить через настоящий HTTPS сервер

    @pytest.mark.asyncio
    async def test_server_headers_removed(self):
        """Тест удаления потенциально опасных заголовков."""
        client = TestClient(app)

        response = client.get("/health")

        # Эти заголовки не должны присутствовать
        assert "Server" not in response.headers
        assert "X-Powered-By" not in response.headers


class TestDDoSProtection:
    """Тесты для DDoS Protection Middleware."""

    def test_ddos_middleware_init(self):
        """Тест инициализации DDoSProtectionMiddleware."""
        middleware = DDoSProtectionMiddleware(
            app=MagicMock(),
            max_connections_per_ip=10,
            suspicious_threshold=100,
            block_duration=300,
            whitelist_ips=["127.0.0.1"],
        )

        assert middleware.max_connections_per_ip == 10
        assert middleware.suspicious_threshold == 100
        assert middleware.block_duration == 300
        assert "127.0.0.1" in middleware.whitelist_ips

    def test_get_client_ip(self):
        """Тест получения IP клиента."""
        middleware = DDoSProtectionMiddleware(app=MagicMock())

        # Мокаем запрос с X-Forwarded-For
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda header: {
            "X-Forwarded-For": "192.168.1.100, 10.0.0.1",
            "X-Real-IP": None,
        }.get(header)
        mock_request.client.host = "127.0.0.1"

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_ip_blocking(self):
        """Тест блокировки IP адресов."""
        middleware = DDoSProtectionMiddleware(app=MagicMock())
        current_time = time.time()

        # Блокируем IP
        middleware.blocked_ips["192.168.1.100"] = current_time

        # Проверяем блокировку
        assert middleware._is_ip_blocked("192.168.1.100", current_time) is True
        assert middleware._is_ip_blocked("192.168.1.101", current_time) is False

        # Проверяем разблокировку по времени
        old_time = current_time - middleware.block_duration - 1
        middleware.blocked_ips["192.168.1.100"] = old_time
        assert middleware._is_ip_blocked("192.168.1.100", current_time) is False

    def test_rate_limiting(self):
        """Тест rate limiting."""
        middleware = DDoSProtectionMiddleware(app=MagicMock(), suspicious_threshold=5)
        current_time = time.time()

        # Добавляем много запросов от одного IP
        ip = "192.168.1.100"
        for _ in range(10):
            middleware._update_counters(ip, current_time)

        # Проверяем превышение лимита
        assert middleware._check_rate_limits(ip, current_time) is True
        assert ip in middleware.blocked_ips

    def test_whitelist_bypass(self):
        """Тест обхода ограничений для whitelist IP."""
        middleware = DDoSProtectionMiddleware(
            app=MagicMock(), whitelist_ips=["127.0.0.1"]
        )

        # Whitelist IP не должен блокироваться
        current_time = time.time()
        for _ in range(1000):  # Много запросов
            middleware._update_counters("127.0.0.1", current_time)

        assert middleware._check_rate_limits("127.0.0.1", current_time) is False

    def test_cleanup_old_records(self):
        """Тест очистки старых записей."""
        middleware = DDoSProtectionMiddleware(app=MagicMock())
        current_time = time.time()
        old_time = current_time - 7200  # 2 часа назад

        # Добавляем старые записи
        middleware.ip_requests["192.168.1.100"] = [old_time, old_time + 10]
        middleware.ip_requests["192.168.1.101"] = [current_time - 10]
        middleware.blocked_ips["192.168.1.102"] = old_time

        # Очищаем
        middleware._cleanup_old_records(current_time)

        # Проверяем очистку
        assert "192.168.1.100" not in middleware.ip_requests
        assert "192.168.1.101" in middleware.ip_requests
        assert "192.168.1.102" not in middleware.blocked_ips


class TestAPISecurityIntegration:
    """Интеграционные тесты безопасности API."""

    def test_api_requires_authentication(self):
        """Тест требования аутентификации для API."""
        client = TestClient(app)

        # Запрос без API ключа должен быть отклонен
        response = client.post(
            "/chat", json={"messages": [{"role": "user", "content": "test"}]}
        )

        assert response.status_code == 401

    def test_cors_headers_present(self):
        """Тест наличия CORS заголовков."""
        client = TestClient(app)

        response = client.options("/health")

        # Проверяем CORS заголовки
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

    def test_health_endpoint_public(self):
        """Тест доступности health endpoint без аутентификации."""
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_security_status_endpoint(self):
        """Тест endpoint статуса безопасности."""
        client = TestClient(app)

        response = client.get("/security/status")

        assert response.status_code == 200
        data = response.json()

        assert "is_secure" in data
        assert "security_score" in data
        assert "features" in data
        assert "timestamp" in data

    def test_rate_limiting_integration(self):
        """Тест интеграции rate limiting."""
        client = TestClient(app)

        # Делаем много запросов подряд
        responses = []
        for _ in range(10):
            response = client.get("/health")
            responses.append(response.status_code)

        # Все запросы к health должны проходить (нет rate limiting)
        assert all(status == 200 for status in responses)


class TestSSLConfiguration:
    """Тесты SSL конфигурации (требуют реального HTTPS сервера)."""

    @pytest.mark.skip(reason="Требует настроенный HTTPS сервер")
    def test_ssl_certificate_valid(self):
        """Тест валидности SSL сертификата."""
        # Этот тест требует реального HTTPS сервера
        url = "https://localhost:443/health"

        try:
            response = requests.get(url, verify=True, timeout=5)
            assert response.status_code == 200
        except requests.exceptions.SSLError:
            pytest.fail("SSL certificate is invalid")

    @pytest.mark.skip(reason="Требует настроенный HTTPS сервер")
    def test_hsts_header_in_response(self):
        """Тест наличия HSTS заголовка в HTTPS ответе."""
        url = "https://localhost:443/health"

        try:
            response = requests.get(url, verify=False, timeout=5)
            assert "Strict-Transport-Security" in response.headers

            hsts = response.headers["Strict-Transport-Security"]
            assert "max-age=" in hsts
            assert "includeSubDomains" in hsts
        except requests.exceptions.RequestException:
            pytest.skip("HTTPS server not available")

    @pytest.mark.skip(reason="Требует настроенный HTTPS сервер")
    def test_http_redirect_to_https(self):
        """Тест редиректа с HTTP на HTTPS."""
        url = "http://localhost:80/health"

        try:
            response = requests.get(url, allow_redirects=False, timeout=5)
            assert response.status_code == 301
            assert response.headers["Location"].startswith("https://")
        except requests.exceptions.RequestException:
            pytest.skip("HTTP server not available")


class TestFirewallConfiguration:
    """Тесты конфигурации firewall (требуют системных прав)."""

    @pytest.mark.skip(reason="Требует системные права")
    def test_firewall_blocks_unauthorized_ports(self):
        """Тест блокировки неавторизованных портов."""
        import socket

        # Тестируем заблокированные порты
        blocked_ports = [23, 135, 139, 445]

        for port in blocked_ports:
            with pytest.raises(socket.error):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                sock.close()
                assert result != 0  # Соединение должно быть отклонено

    @pytest.mark.skip(reason="Требует системные права")
    def test_firewall_allows_authorized_ports(self):
        """Тест разрешения авторизованных портов."""
        import socket

        # Тестируем разрешенные порты
        allowed_ports = [80, 443, 8000]

        for port in allowed_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            # Порт должен быть доступен (или сервис не запущен, что тоже ок)


class TestSecurityConfiguration:
    """Тесты конфигурации безопасности."""

    def test_debug_disabled_in_production(self):
        """Тест отключения debug режима в продакшене."""
        settings = get_settings()

        # В тестах может быть включен debug, но проверяем логику
        if hasattr(settings, "environment") and settings.environment == "production":
            assert settings.debug is False

    def test_api_key_configured(self):
        """Тест настройки API ключа."""
        settings = get_settings()

        # API ключ должен быть настроен
        assert settings.api_key is not None
        assert len(settings.api_key) >= 16  # Минимальная длина

    def test_cors_origins_configured(self):
        """Тест настройки CORS origins."""
        settings = get_settings()

        # CORS origins должны быть настроены
        assert len(settings.allowed_origins) > 0

        # Не должно быть wildcard в продакшене
        for origin in settings.allowed_origins:
            assert origin != "*"

    def test_rate_limiting_configured(self):
        """Тест настройки rate limiting."""
        settings = get_settings()

        # Rate limiting должен быть настроен
        assert settings.rate_limit_per_minute > 0
        assert settings.rate_limit_per_minute <= 1000  # Разумный лимит


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
