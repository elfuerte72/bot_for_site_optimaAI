"""
Модуль для интерфейса бота с RAG системой.
"""

import os
from typing import Any, Dict, List, Optional, Union

from langchain.schema import Document
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
"""

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

        return response.choices[0].message.content

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
