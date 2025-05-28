"""
Скрипт для тестирования RAG системы.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from src.rag.rag_system import RAGSystem
from src.rag.bot_interface import BotInterface


def main():
    """Основная функция для тестирования RAG системы."""
    # Определяем пути
    data_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag"))
    persist_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag_index"))
    
    # Создаем директорию для индекса, если она не существует
    os.makedirs(persist_dir, exist_ok=True)
    
    print(f"Директория с данными: {data_dir}")
    print(f"Директория для индекса: {persist_dir}")
    
    # Создаем RAG систему
    rag_system = RAGSystem(
        data_dir=data_dir,
        persist_dir=persist_dir,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Загружаем и индексируем документы
    try:
        print("Загрузка и индексация документов...")
        rag_system.load_and_index_documents(force_reload=True)
        print("Документы успешно загружены и проиндексированы!")
    except Exception as e:
        print(f"Ошибка при загрузке и индексации документов: {str(e)}")
        return
    
    # Создаем интерфейс бота
    bot = BotInterface(rag_system=rag_system)
    
    # Тестовые запросы
    test_queries = [
        "Расскажи о компании Optima AI",
        "Какие услуги предлагает Академия Optima AI?",
        "Что дает прокачка навыка промптинга?",
        "Кто основатели компании?",
        "Какие пакеты обучения предлагает Академия?"
    ]
    
    # Тестируем запросы
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Тестовый запрос #{i}: {query}")
        print(f"{'=' * 80}")
        
        # Получаем релевантные документы
        relevant_docs = rag_system.query(query=query, k=3)
        
        print("\nРелевантные документы:")
        print(rag_system.format_results(relevant_docs))
        
        # Получаем ответ от бота
        response = bot.process_query(query=query, k=3)
        
        print("\nОтвет бота:")
        print(response)
    
    # Интерактивный режим
    print("\n\nИнтерактивный режим (введите 'exit' для выхода):")
    while True:
        query = input("\nВаш вопрос: ")
        if query.lower() == 'exit':
            break
        
        response = bot.process_query(query=query)
        print("\nОтвет бота:")
        print(response)


if __name__ == "__main__":
    main()
