#!/usr/bin/env python3
"""
Скрипт для проверки готовности проекта к деплою.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple


class DeploymentChecker:
    """Класс для проверки готовности к деплою."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
    
    def log_error(self, message: str):
        """Добавить ошибку."""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message: str):
        """Добавить предупреждение."""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def log_success(self, message: str):
        """Логировать успешную проверку."""
        self.checks_passed += 1
        print(f"✅ {message}")
    
    def run_command(self, command: List[str], cwd: Path = None) -> Tuple[bool, str]:
        """Выполнить команду и вернуть результат."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_required_files(self):
        """Проверить наличие обязательных файлов."""
        print("\n🔍 Checking required files...")
        self.total_checks += 1
        
        required_files = [
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".env.example",
            "README.md",
            "main.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.log_error(f"Missing required files: {', '.join(missing_files)}")
        else:
            self.log_success("All required files present")
    
    def check_environment_variables(self):
        """Проверить переменные окружения."""
        print("\n🔍 Checking environment variables...")
        self.total_checks += 1
        
        env_example_path = self.project_root / ".env.example"
        if not env_example_path.exists():
            self.log_error(".env.example file not found")
            return
        
        try:
            with open(env_example_path, 'r') as f:
                env_vars = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        var_name = line.split('=')[0]
                        env_vars.append(var_name)
            
            missing_vars = []
            for var in env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.log_warning(f"Missing environment variables: {', '.join(missing_vars)}")
            else:
                self.log_success("All environment variables configured")
        
        except Exception as e:
            self.log_error(f"Error checking environment variables: {e}")
    
    def check_dependencies(self):
        """Проверить зависимости."""
        print("\n🔍 Checking dependencies...")
        self.total_checks += 1
        
        # Проверяем requirements.txt
        requirements_path = self.project_root / "requirements.txt"
        if not requirements_path.exists():
            self.log_error("requirements.txt not found")
            return
        
        # Проверяем установку зависимостей
        success, output = self.run_command(["pip", "check"])
        if not success:
            self.log_error(f"Dependency conflicts found: {output}")
        else:
            self.log_success("Dependencies are compatible")
    
    def check_code_quality(self):
        """Проверить качество кода."""
        print("\n🔍 Checking code quality...")
        
        # Black
        self.total_checks += 1
        success, output = self.run_command(["black", "--check", "src/", "tests/"])
        if not success:
            self.log_error("Code formatting issues found (run 'black src/ tests/')")
        else:
            self.log_success("Code formatting is correct")
        
        # isort
        self.total_checks += 1
        success, output = self.run_command(["isort", "--check-only", "src/", "tests/"])
        if not success:
            self.log_error("Import sorting issues found (run 'isort src/ tests/')")
        else:
            self.log_success("Import sorting is correct")
        
        # flake8
        self.total_checks += 1
        success, output = self.run_command(["flake8", "src/", "tests/"])
        if not success:
            self.log_error(f"Linting issues found: {output}")
        else:
            self.log_success("No linting issues found")
        
        # mypy
        self.total_checks += 1
        success, output = self.run_command(["mypy", "src/"])
        if not success:
            self.log_warning(f"Type checking issues found: {output}")
        else:
            self.log_success("Type checking passed")
    
    def check_tests(self):
        """Проверить тесты."""
        print("\n🔍 Running tests...")
        self.total_checks += 1
        
        success, output = self.run_command([
            "pytest", 
            "--cov=src", 
            "--cov-fail-under=80",
            "--tb=short"
        ])
        
        if not success:
            self.log_error(f"Tests failed: {output}")
        else:
            self.log_success("All tests passed with sufficient coverage")
    
    def check_security(self):
        """Проверить безопасность."""
        print("\n🔍 Checking security...")
        
        # bandit
        self.total_checks += 1
        success, output = self.run_command(["bandit", "-r", "src/"])
        if not success:
            self.log_warning(f"Security issues found: {output}")
        else:
            self.log_success("No security issues found")
        
        # safety
        self.total_checks += 1
        success, output = self.run_command(["safety", "check"])
        if not success:
            self.log_warning(f"Vulnerable dependencies found: {output}")
        else:
            self.log_success("No vulnerable dependencies found")
    
    def check_docker(self):
        """Проверить Docker конфигурацию."""
        print("\n🔍 Checking Docker configuration...")
        self.total_checks += 1
        
        # Проверяем сборку Docker образа
        success, output = self.run_command([
            "docker", "build", "-t", "optimaai-bot:test", "."
        ])
        
        if not success:
            self.log_error(f"Docker build failed: {output}")
            return
        
        self.log_success("Docker image builds successfully")
        
        # Проверяем запуск контейнера
        self.total_checks += 1
        success, output = self.run_command([
            "docker", "run", "--rm", "-d", 
            "--name", "deployment-test",
            "-p", "8001:8000",
            "optimaai-bot:test"
        ])
        
        if not success:
            self.log_error(f"Docker container failed to start: {output}")
            return
        
        # Ждем запуска
        time.sleep(10)
        
        # Проверяем health endpoint
        success, output = self.run_command([
            "curl", "-f", "http://localhost:8001/health"
        ])
        
        # Останавливаем контейнер
        self.run_command(["docker", "stop", "deployment-test"])
        
        if not success:
            self.log_error("Health check failed")
        else:
            self.log_success("Docker container runs and responds correctly")
    
    def check_documentation(self):
        """Проверить документацию."""
        print("\n🔍 Checking documentation...")
        self.total_checks += 1
        
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            self.log_error("README.md not found")
            return
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "installation", "usage", "api", "deployment"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section.lower() not in content.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                self.log_warning(f"README.md missing sections: {', '.join(missing_sections)}")
            else:
                self.log_success("Documentation is complete")
        
        except Exception as e:
            self.log_error(f"Error reading README.md: {e}")
    
    def check_git_status(self):
        """Проверить статус Git."""
        print("\n🔍 Checking Git status...")
        self.total_checks += 1
        
        # Проверяем, что нет незакоммиченных изменений
        success, output = self.run_command(["git", "status", "--porcelain"])
        
        if output.strip():
            self.log_warning("Uncommitted changes found")
        else:
            self.log_success("No uncommitted changes")
        
        # Проверяем текущую ветку
        success, output = self.run_command(["git", "branch", "--show-current"])
        if success:
            branch = output.strip()
            if branch in ["main", "master"]:
                self.log_success(f"On production branch: {branch}")
            else:
                self.log_warning(f"Not on production branch (current: {branch})")
    
    def generate_report(self):
        """Сгенерировать отчет о проверке."""
        print("\n" + "="*60)
        print("🚀 DEPLOYMENT READINESS REPORT")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"   Checks passed: {self.checks_passed}/{self.total_checks}")
        print(f"   Success rate: {(self.checks_passed/self.total_checks)*100:.1f}%")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Определяем готовность к деплою
        if not self.errors:
            if not self.warnings:
                print("\n🎉 READY FOR DEPLOYMENT!")
                print("   All checks passed successfully.")
                return 0
            else:
                print("\n✅ READY FOR DEPLOYMENT (with warnings)")
                print("   Consider addressing warnings before deployment.")
                return 0
        else:
            print("\n🚫 NOT READY FOR DEPLOYMENT")
            print("   Please fix all errors before deploying.")
            return 1
    
    def run_all_checks(self):
        """Запустить все проверки."""
        print("🔍 Starting deployment readiness check...")
        
        self.check_required_files()
        self.check_environment_variables()
        self.check_dependencies()
        self.check_code_quality()
        self.check_tests()
        self.check_security()
        self.check_docker()
        self.check_documentation()
        self.check_git_status()
        
        return self.generate_report()


def main():
    """Главная функция."""
    checker = DeploymentChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()