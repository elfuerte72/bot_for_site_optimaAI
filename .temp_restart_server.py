#!/usr/bin/env python3
"""
Скрипт для перезапуска сервера OptimaAI Bot.
"""

import os
import signal
import subprocess
import time
import sys
import psutil

def kill_processes_on_port(port):
    """Останавливает все процессы на указанном порту."""
    try:
        # Находим процессы на порту
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🔍 Найдены процессы на порту {port}: {pids}")
            
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    process = psutil.Process(pid)
                    print(f"⚡ Останавливаю процесс {pid} ({process.name()})")
                    process.terminate()
                    
                    # Ждем завершения
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        print(f"🔥 Принудительно завершаю процесс {pid}")
                        process.kill()
                        
                except (psutil.NoSuchProcess, ValueError) as e:
                    print(f"⚠️ Процесс {pid} уже завершен или недоступен")
                    
        else:
            print(f"✅ Порт {port} свободен")
            
    except Exception as e:
        print(f"❌ Ошибка при освобождении порта {port}: {e}")

def kill_python_main_processes():
    """Останавливает все процессы Python с main.py."""
    try:
        # Находим процессы Python с main.py
        result = subprocess.run(['pkill', '-f', 'python.*main.py'], 
                              capture_output=True, text=True)
        print("🔥 Остановлены все процессы python main.py")
        
        # Дополнительно ищем через ps
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'python' in line and 'main.py' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        process = psutil.Process(pid)
                        print(f"🔥 Дополнительно останавливаю процесс {pid}")
                        process.terminate()
                    except (psutil.NoSuchProcess, ValueError):
                        pass
                        
    except Exception as e:
        print(f"⚠️ Ошибка при остановке Python процессов: {e}")

def start_server():
    """Запускает сервер."""
    print("🚀 Запускаю OptimaAI Bot сервер...")
    
    # Переходим в директорию проекта
    os.chdir('/Users/maximpenkin/Documents/openai/site/backend')
    
    # Запускаем сервер
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
    except KeyboardInterrupt:
        print("\n⏹️ Сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске сервера: {e}")

def main():
    """Основная функция."""
    print("🔄 Перезапуск OptimaAI Bot сервера")
    print("=" * 50)
    
    # Останавливаем процессы на порту 8000
    print("1️⃣ Освобождаю порт 8000...")
    kill_processes_on_port(8000)
    
    # Останавливаем все Python процессы с main.py
    print("2️⃣ Останавливаю все процессы main.py...")
    kill_python_main_processes()
    
    # Ждем немного
    print("3️⃣ Жду 3 секунды...")
    time.sleep(3)
    
    # Проверяем, что порт свободен
    print("4️⃣ Проверяю порт 8000...")
    kill_processes_on_port(8000)
    
    print("5️⃣ Запускаю сервер...")
    start_server()

if __name__ == "__main__":
    main()