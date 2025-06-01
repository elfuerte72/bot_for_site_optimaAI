#!/usr/bin/env python3
"""
Скрипт для настройки Git hooks и pre-commit.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class HooksSetup:
    """Класс для настройки Git hooks."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.git_hooks_dir = self.project_root / ".git" / "hooks"
    
    def run_command(self, command, cwd=None):
        """Выполнить команду."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                shell=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def install_pre_commit(self):
        """Установить pre-commit."""
        print("🔧 Installing pre-commit...")
        
        # Проверяем, установлен ли pre-commit
        success, stdout, stderr = self.run_command("pre-commit --version")
        if not success:
            print("Installing pre-commit...")
            success, stdout, stderr = self.run_command("pip install pre-commit")
            if not success:
                print(f"❌ Failed to install pre-commit: {stderr}")
                return False
        
        print("✅ pre-commit is available")
        return True
    
    def setup_pre_commit_hooks(self):
        """Настроить pre-commit hooks."""
        print("🔧 Setting up pre-commit hooks...")
        
        success, stdout, stderr = self.run_command("pre-commit install")
        if not success:
            print(f"❌ Failed to install pre-commit hooks: {stderr}")
            return False
        
        print("✅ Pre-commit hooks installed")
        
        # Устанавливаем commit-msg hook
        success, stdout, stderr = self.run_command("pre-commit install --hook-type commit-msg")
        if success:
            print("✅ Commit-msg hook installed")
        
        return True
    
    def create_commit_msg_hook(self):
        """Создать commit-msg hook для проверки формата коммитов."""
        hook_content = '''#!/bin/sh
# Проверка формата commit message

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .{1,50}'

error_msg="Неправильный формат commit message!
Используйте формат: type(scope): description

Типы:
- feat: новая функциональность
- fix: исправление бага
- docs: изменения в документации
- style: форматирование кода
- refactor: рефакторинг
- test: добавление тестов
- chore: обновление зависимостей, конфигурации
- perf: улучшение производительности
- ci: изменения в CI/CD
- build: изменения в сборке
- revert: откат изменений

Пример: feat(auth): add Google OAuth integration"

if ! grep -qE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
'''
        
        hook_path = self.git_hooks_dir / "commit-msg"
        try:
            with open(hook_path, 'w') as f:
                f.write(hook_content)
            
            # Делаем файл исполняемым
            os.chmod(hook_path, 0o755)
            print("✅ Commit-msg hook created")
            return True
        except Exception as e:
            print(f"❌ Failed to create commit-msg hook: {e}")
            return False
    
    def create_pre_push_hook(self):
        """Создать pre-push hook для запуска тестов."""
        hook_content = '''#!/bin/sh
# Pre-push hook для запуска тестов

echo "🧪 Running tests before push..."

# Запускаем быстрые тесты
if ! make test-quick; then
    echo "❌ Tests failed! Push aborted."
    exit 1
fi

# Проверяем качество кода
if ! make lint-quick; then
    echo "❌ Code quality check failed! Push aborted."
    exit 1
fi

echo "✅ All checks passed. Pushing..."
'''
        
        hook_path = self.git_hooks_dir / "pre-push"
        try:
            with open(hook_path, 'w') as f:
                f.write(hook_content)
            
            os.chmod(hook_path, 0o755)
            print("✅ Pre-push hook created")
            return True
        except Exception as e:
            print(f"❌ Failed to create pre-push hook: {e}")
            return False
    
    def update_makefile(self):
        """Обновить Makefile с новыми командами."""
        makefile_additions = '''
# Быстрые команды для hooks
test-quick:
	pytest tests/ -x --tb=short -q --disable-warnings

lint-quick:
	flake8 --select=E9,F63,F7,F82 src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Команды для hooks
setup-hooks:
	python scripts/setup_hooks.py

pre-commit-run:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate
'''
        
        makefile_path = self.project_root / "Makefile"
        try:
            with open(makefile_path, 'a') as f:
                f.write(makefile_additions)
            print("✅ Makefile updated with hook commands")
            return True
        except Exception as e:
            print(f"❌ Failed to update Makefile: {e}")
            return False
    
    def setup_all(self):
        """Выполнить полную настройку hooks."""
        print("🚀 Setting up Git hooks and pre-commit...")
        
        if not self.git_hooks_dir.exists():
            print("❌ Not a Git repository or .git/hooks directory not found")
            return False
        
        success = True
        success &= self.install_pre_commit()
        success &= self.setup_pre_commit_hooks()
        success &= self.create_commit_msg_hook()
        success &= self.create_pre_push_hook()
        
        if success:
            print("\n🎉 Git hooks setup completed successfully!")
            print("\nТеперь при каждом коммите будут:")
            print("- Проверяться форматирование кода")
            print("- Запускаться линтеры")
            print("- Проверяться типы")
            print("- Проверяться формат commit message")
            print("\nПри push будут запускаться быстрые тесты")
        else:
            print("\n❌ Some hooks setup failed")
        
        return success


def main():
    """Главная функция."""
    setup = HooksSetup()
    success = setup.setup_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()