#!/usr/bin/env python3
"""
Скрипт для принудительного переиндексирования RAG системы.
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.rag_system import RAGSystem

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Основная функция для переиндексирования."""
    try:
        # Пути для RAG системы
        data_dir = os.path.join(project_root, "rag")
        persist_dir = os.path.join(project_root, "rag_index")
        
        logger.info(f"Данные: {data_dir}")
        logger.info(f"Индекс: {persist_dir}")
        
        # Проверяем, что директория с данными существует
        if not os.path.exists(data_dir):
            logger.error(f"Директория с данными не найдена: {data_dir}")
            return False
            
        # Создаем директорию для индекса, если она не существует
        os.makedirs(persist_dir, exist_ok=True)
        
        # Создаем RAG систему
        rag_system = RAGSystem(
            data_dir=data_dir,
            persist_dir=persist_dir,
            chunk_size=1000,
            chunk_overlap=200,
        )
        
        # Принудительно переиндексируем документы
        logger.info("Начинаем принудительное переиндексирование...")
        rag_system.load_and_index_documents(force_reload=True)
        
        logger.info("Переиндексирование завершено успешно!")
        
        # Тестируем запрос
        logger.info("Тестируем запрос...")
        test_query = "ArtDirection"
        results = rag_system.query(test_query, k=2)
        
        if results:
            logger.info(f"Найдено {len(results)} результатов для запроса '{test_query}':")
            for i, doc in enumerate(results, 1):
                logger.info(f"Результат {i}: {doc.page_content[:200]}...")
        else:
            logger.warning(f"Не найдено результатов для запроса '{test_query}'")
            
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при переиндексировании: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)