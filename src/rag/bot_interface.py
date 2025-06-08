"""
Модуль для интерфейса бота с RAG системой.
"""

import os
import re
from typing import Any, Dict, List, Optional, Union

from langchain_core.documents import Document
from openai import OpenAI

from .rag_system import RAGSystem


class BotInterface:
    """Класс для взаимодействия бота с RAG системой."""

    def __init__(
        self,
        rag_system: RAGSystem,
        model_name: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """
        Инициализировать интерфейс бота.

        Args:
            rag_system: RAG система
            model_name: Название модели
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
        """
        self.rag_system = rag_system
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _clean_markdown(self, text: str) -> str:
        """
        Очистить текст от markdown символов и правильно отформатировать.
        
        Args:
            text: Текст с markdown разметкой
            
        Returns:
            str: Очищенный и отформатированный текст
        """
        if not text:
            return text
            
        # Удаляем заголовки (# ## ### и т.д.)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Обрабатываем жирный текст (**text** или __text__) - убираем звездочки, но оставляем текст
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Обрабатываем курсив (*text* или _text_) - убираем символы, но оставляем текст
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'\1', text)
        
        # Удаляем зачеркнутый текст (~~text~~)
        text = re.sub(r'~~(.*?)~~', r'\1', text)
        
        # Удаляем код (`code` или ```code```)
        text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
        
        # Удаляем ссылки [text](url) - оставляем только текст
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Удаляем изображения ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        
        # Удаляем горизонтальные линии (--- или ***)
        text = re.sub(r'^[-*]{3,}$', '', text, flags=re.MULTILINE)
        
        # Обрабатываем маркированные списки (- * +) - заменяем на абзацы с отступами
        text = re.sub(r'^[\s]*[-*+]\s+(.+)$', r'\n• \1', text, flags=re.MULTILINE)
        
        # Обрабатываем нумерованные списки (1. 2. и т.д.) - заменяем на абзацы с номерами
        def replace_numbered_list(match):
            number = match.group(1)
            content = match.group(2)
            return f'\n{number}. {content}'
        
        text = re.sub(r'^[\s]*(\d+)\.[\s]+(.+)$', replace_numbered_list, text, flags=re.MULTILINE)
        
        # Удаляем цитаты (> text)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        # Удаляем таблицы (строки с |)
        text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*[-|:]+[\s]*$', '', text, flags=re.MULTILINE)
        
        # Нормализуем переносы строк - заменяем множественные переносы на двойные
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Убираем лишние пробелы в начале и конце строк
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)
        
        # Добавляем отступы после точек в списках для лучшей читаемости
        text = re.sub(r'(\d+\.)([^\s])', r'\1 \2', text)
        
        return text.strip()

    def process_query(
        self,
        query: str,
        k: int = 4,
        system_prompt: Optional[str] = None,
        use_mmr: bool = True,
    ) -> str:
        """
        Обработать запрос пользователя.

        Args:
            query: Запрос пользователя
            k: Количество релевантных документов
            system_prompt: Системный промпт
            use_mmr: Использовать максимально маргинальную релевантность

        Returns:
            str: Ответ бота
        """
        # Получаем релевантные документы
        relevant_docs = self.rag_system.query(query=query, k=k, use_mmr=use_mmr)

        # Если нет релевантных документов, отвечаем заглушкой
        if not relevant_docs:
            return "Извините, я не нашел релевантной информации по вашему запросу."

        # Формируем контекст из релевантных документов
        context = self._format_context(relevant_docs)

        # Определяем системный промпт
        if not system_prompt:
            system_prompt = """Ты - умный ассистент компании Optima AI.
Отвечай на запросы пользователя, основываясь на предоставленном контексте.
Если в контексте нет релевантной информации, признайся в этом и предложи задать другой вопрос.
Твои ответы должны быть вежливыми, информативными и полезными.
Не выдумывай информацию.
Всегда отвечай на русском языке.

ВАЖНО: Отвечай простым текстом БЕЗ использования markdown разметки.
НЕ используй символы: **, *, __, _, ~~, `, #, -, +, >, |
Если нужно перечислить пункты, используй обычные абзацы с номерами или символом •
Каждый пункт списка должен начинаться с новой строки."""

        # Формируем запрос к модели
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Контекст:\n{context}\n\nЗапрос пользователя: {query}",
            },
        ]

        # Отправляем запрос к модели
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Получаем ответ и очищаем от markdown
        raw_response = response.choices[0].message.content
        cleaned_response = self._clean_markdown(raw_response)
        
        return cleaned_response

    def _format_context(self, documents: List[Document]) -> str:
        """
        Форматировать контекст из релевантных документов.

        Args:
            documents: Список релевантных документов

        Returns:
            str: Отформатированный контекст
        """
        context_parts = []

        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Неизвестный источник")
            context_parts.append(
                f"Документ {i} (источник: {source}):\n{doc.page_content}\n"
            )

        return "\n".join(context_parts)