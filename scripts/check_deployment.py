#!/usr/bin/env python3
"""
Скрипт для автоматической проверки готовности к деплою.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests


# Цвета для вывода
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_status(message: str, status: str):
    """Печать статуса с цветом."""
    if status == "PASS":
        print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")
    elif status == "FAIL":
        print(f"{Colors.RED}❌ {message}{Colors.ENDC}")
    elif status == "WARN":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")
    else:
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")


def run_command(command: str) -> Tuple[bool, str]:
    """Выполнение команды и возврат результата."""
    try:
        result = subprocess.run(
            command.split(), capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_environment_variables() -> bool:
    """Проверка переменных окружения."""
    print(f"\n{Colors.BOLD}🔧 Проверка переменных окружения{Colors.ENDC}")

    required_vars = ["OPENAI_API_KEY"]

    optional_vars = ["GPT_MODEL", "DEBUG", "ALLOWED_ORIGINS", "RATE_LIMIT_PER_MINUTE"]

    all_good = True

    for var in required_vars:
        if os.getenv(var):
            print_status(f"{var} установлена", "PASS")
        else:
            print_status(f"{var} НЕ УСТАНОВЛЕНА (обязательная)", "FAIL")
            all_good = False

    for var in optional_vars:
        if os.getenv(var):
            print_status(f"{var} установлена", "PASS")
        else:
            print_status(f"{var} не установлена (опциональная)", "WARN")

    return all_good


def check_dependencies() -> bool:
    """Проверка зависимостей."""
    print(f"\n{Colors.BOLD}📦 Проверка зависимостей{Colors.ENDC}")

    success, output = run_command("pip check")
    if success:
        print_status("Все зависимости совместимы", "PASS")
        return True
    else:
        print_status(f"Проблемы с зависимостями: {output}", "FAIL")
        return False


def check_code_quality() -> bool:
    """Проверка качества кода."""
    print(f"\n{Colors.BOLD}🧪 Проверка качества кода{Colors.ENDC}")

    checks = [
        ("black --check src/ tests/", "Black форматирование"),
        ("isort --check-only src/ tests/", "isort импорты"),
        ("flake8 src/ tests/", "flake8 линтинг"),
        ("mypy src/", "mypy типизация"),
    ]

    all_good = True

    for command, description in checks:
        success, output = run_command(command)
        if success:
            print_status(description, "PASS")
        else:
            print_status(f"{description}: {output[:100]}...", "FAIL")
            all_good = False

    return all_good


def check_tests() -> bool:
    """Проверка тестов."""
    print(f"\n{Colors.BOLD}🧪 Запуск тестов{Colors.ENDC}")

    success, output = run_command("pytest --tb=short")
    if success:
        print_status("Все тесты прошли", "PASS")

        # Проверка покрытия
        success_cov, output_cov = run_command(
            "pytest --cov=src --cov-report=term-missing"
        )
        if "TOTAL" in output_cov:
            # Извлекаем процент покрытия
            lines = output_cov.split("\n")
            for line in lines:
                if "TOTAL" in line:
                    coverage = line.split()[-1].replace("%", "")
                    try:
                        coverage_percent = int(coverage)
                        if coverage_percent >= 80:
                            print_status(f"Покрытие тестами: {coverage}%", "PASS")
                        else:
                            print_status(
                                f"Покрытие тестами: {coverage}% (< 80%)", "WARN"
                            )
                    except:
                        print_status("Не удалось определить покрытие", "WARN")
                    break

        return True
    else:
        print_status(f"Тесты не прошли: {output[:200]}...", "FAIL")
        return False


def check_security() -> bool:
    """Проверка безопасности."""
    print(f"\n{Colors.BOLD}🔒 Проверка безопасности{Colors.ENDC}")

    all_good = True

    # Проверка DEBUG режима
    debug = os.getenv("DEBUG", "false").lower()
    if debug in ["false", "0", ""]:
        print_status("DEBUG режим отключён", "PASS")
    else:
        print_status("DEBUG режим включён (небезопасно для продакшена)", "FAIL")
        all_good = False

    # Проверка CORS
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
    if "*" in allowed_origins:
        print_status("CORS разрешён для всех доменов (небезопасно)", "FAIL")
        all_good = False
    elif allowed_origins:
        print_status("CORS настроен для конкретных доменов", "PASS")
    else:
        print_status("CORS не настроен", "WARN")

    # Проверка rate limiting
    rate_limit = os.getenv("RATE_LIMIT_PER_MINUTE")
    if rate_limit and int(rate_limit) > 0:
        print_status(f"Rate limiting: {rate_limit} запросов/мин", "PASS")
    else:
        print_status("Rate limiting не настроен", "WARN")

    return all_good


def check_docker() -> bool:
    """Проверка Docker конфигурации."""
    print(f"\n{Colors.BOLD}🐳 Проверка Docker{Colors.ENDC}")

    # Проверка наличия Dockerfile
    if Path("Dockerfile").exists():
        print_status("Dockerfile найден", "PASS")
    else:
        print_status("Dockerfile не найден", "FAIL")
        return False

    # Проверка docker-compose.yml
    if Path("docker-compose.yml").exists():
        print_status("docker-compose.yml найден", "PASS")
    else:
        print_status("docker-compose.yml не найден", "WARN")

    # Попытка сборки образа
    print_status("Проверка сборки Docker образа...", "INFO")
    success, output = run_command("docker build -t optimaai-bot-test .")
    if success:
        print_status("Docker образ собирается успешно", "PASS")
        return True
    else:
        print_status(f"Ошибка сборки Docker: {output[:200]}...", "FAIL")
        return False


def check_api_health(url: str = "http://localhost:8000") -> bool:
    """Проверка работоспособности API."""
    print(f"\n{Colors.BOLD}🌐 Проверка API{Colors.ENDC}")

    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_status(f"API доступен: {data.get('status')}", "PASS")

            # Проверка сервисов
            services = data.get("services", {})
            for service, status in services.items():
                if status == "ok":
                    print_status(f"Сервис {service}: {status}", "PASS")
                else:
                    print_status(f"Сервис {service}: {status}", "WARN")

            return True
        else:
            print_status(f"API недоступен: HTTP {response.status_code}", "FAIL")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Не удалось подключиться к API: {str(e)}", "FAIL")
        return False


def generate_report(results: Dict[str, bool]) -> None:
    """Генерация итогового отчёта."""
    print(f"\n{Colors.BOLD}📊 ИТОГОВЫЙ ОТЧЁТ{Colors.ENDC}")
    print("=" * 50)

    total_checks = len(results)
    passed_checks = sum(results.values())

    for check, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print_status(check, status)

    print("=" * 50)
    print(f"Пройдено: {passed_checks}/{total_checks} проверок")

    if passed_checks == total_checks:
        print(
            f"\n{Colors.GREEN}{Colors.BOLD}🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! ГОТОВ К ДЕПЛОЮ!{Colors.ENDC}"
        )
        return True
    else:
        print(
            f"\n{Colors.RED}{Colors.BOLD}❌ ЕСТЬ ПРОБЛЕМЫ! НЕ ГОТОВ К ДЕПЛОЮ!{Colors.ENDC}"
        )
        return False


def main():
    """Основная функция."""
    print(f"{Colors.BOLD}🚀 ПРОВЕРКА ГОТОВНОСТИ К ДЕПЛОЮ OptimaAI Bot{Colors.ENDC}")
    print("=" * 60)

    # Проверка рабочей директории
    if not Path("main.py").exists():
        print_status("Запустите скрипт из корневой директории проекта", "FAIL")
        sys.exit(1)

    results = {}

    # Выполнение всех проверок
    results["Переменные окружения"] = check_environment_variables()
    results["Зависимости"] = check_dependencies()
    results["Качество кода"] = check_code_quality()
    results["Тесты"] = check_tests()
    results["Безопасность"] = check_security()
    results["Docker"] = check_docker()

    # Опциональная проверка API (если сервер запущен)
    api_available = check_api_health()
    if api_available:
        results["API"] = True

    # Генерация отчёта
    all_passed = generate_report(results)

    # Возврат кода выхода
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
