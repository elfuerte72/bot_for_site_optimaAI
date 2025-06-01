#!/usr/bin/env python3
"""
Быстрый тест RAG системы.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from src.rag.bot_interface import BotInterface
from src.rag.rag_system import RAGSystem


def quick_test():
    """Быстрый тест RAG системы."""
    # Определяем пути
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "rag"))
    persist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "rag_index"))

    print(f"Директория с данными: {data_dir}")
    print(f"Директория для индекса: {persist_dir}")

    # Создаем RAG систему
    rag_system = RAGSystem(
        data_dir=data_dir, persist_dir=persist_dir, chunk_size=1000, chunk_overlap=200
    )

    # Загружаем существующий индекс (без пересоздания)
    try:
        print("Загрузка существующего индекса...")
        rag_system.load_and_index_documents(force_reload=False)
        print("Индекс успешно загружен!")
    except Exception as e:
        print(f"Ошибка при загрузке индекса: {str(e)}")
        return

    # Создаем интерфейс бота
    bot = BotInterface(rag_system=rag_system)

    # Тестовые запросы
    test_queries = [
        "Расскажи о компании Optima AI",
        "Какие услуги предлагает Академия?",
        "Сколько стоит обучение?",
    ]

    # Тестируем запросы
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Тестовый запрос #{i}: {query}")
        print(f"{'=' * 60}")

        try:
            # Получаем ответ от бота
            response = bot.process_query(query=query, k=3)
            print("\nОтвет бота:")
            print(response)
            print(f"\nДлина ответа: {len(response)} символов")
            
            # Проверяем, что markdown символы удалены
            markdown_symbols = ['**', '*', '#', '`', '[', ']', '(', ')', '>', '|', '-', '+']
            found_markdown = [symbol for symbol in markdown_symbols if symbol in response]
            if found_markdown:
                print(f"⚠️ Найдены markdown символы: {found_markdown}")
            else:
                print("✅ Markdown символы успешно удалены")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке запроса: {str(e)}")

    print("\n" + "=" * 60)
    print("Тест завершен!")


if __name__ == "__main__":
    quick_test()