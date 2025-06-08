#!/usr/bin/env python3
"""Тестирование RAG системы для запроса ArtDirection."""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.rag_system import RAGSystem  # noqa: E402
from src.rag.bot_interface import BotInterface  # noqa: E402


def main():
    """Тестирование RAG системы."""
    try:
        # Устанавливаем API ключ из переменной окружения
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY не установлен в переменных окружения"
            )
        
        # Пути для RAG системы
        data_dir = os.path.join(project_root, "rag")
        persist_dir = os.path.join(project_root, "rag_index")
        
        print(f"Данные: {data_dir}")
        print(f"Индекс: {persist_dir}")
        
        # Создаем RAG систему
        rag_system = RAGSystem(
            data_dir=data_dir,
            persist_dir=persist_dir,
            chunk_size=1000,
            chunk_overlap=200,
        )
        
        # Загружаем существующий индекс
        rag_system.load_and_index_documents(force_reload=False)
        
        # Тестируем поиск документов
        print("\n=== ТЕСТ 1: Поиск документов ===")
        query = "ArtDirection"
        results = rag_system.query(query, k=4)
        
        print(f"Найдено {len(results)} результатов для запроса '{query}':")
        for i, doc in enumerate(results, 1):
            print(f"\nРезультат {i}:")
            print(f"Источник: {doc.metadata.get('source', 'Неизвестно')}")
            print(f"Содержимое: {doc.page_content}")
            print("-" * 50)
        
        # Тестируем бот интерфейс
        print("\n=== ТЕСТ 2: Ответ бота ===")
        bot_interface = BotInterface(
            rag_system=rag_system,
            model_name="gpt-4o-mini",
            temperature=0.7,
        )
        
        test_queries = [
            "Расскажи подробнее про ArtDirection",
            "Сколько стоит курс ArtDirection?",
            "Что входит в курс ArtDirection?",
            "Сколько длится курс ArtDirection?"
        ]
        
        for query in test_queries:
            print(f"\nЗапрос: {query}")
            response = bot_interface.process_query(query, k=4)
            print(f"Ответ: {response}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

