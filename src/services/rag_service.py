"""
Сервис для работы с RAG (Retrieval Augmented Generation) системой.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from src.config import Settings
from src.models.message import Message
from src.rag.bot_interface import BotInterface
from src.rag.rag_system import RAGSystem


class RAGService:
    """Сервис для работы с RAG системой."""

    def __init__(self, settings: Settings):
        """
        Инициализация сервиса.

        Args:
            settings: Настройки приложения
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        # Пути для RAG системы
        self.data_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "rag"
            )
        )
        self.persist_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "rag_index"
            )
        )

        # Создаем директорию для индекса, если она не существует
        os.makedirs(self.persist_dir, exist_ok=True)

        # Инициализация RAG системы
        self._initialize_rag_system()

    def _initialize_rag_system(self) -> None:
        """
        Инициализация RAG системы.
        """
        try:
            self.logger.info(
                f"Инициализация RAG системы. Данные: {self.data_dir}, Индекс: {self.persist_dir}"
            )

            # Создаем RAG систему
            self.rag_system = RAGSystem(
                data_dir=self.data_dir,
                persist_dir=self.persist_dir,
                chunk_size=1000,
                chunk_overlap=200,
            )

            # Загружаем и индексируем документы (если индекс не существует)
            self.rag_system.load_and_index_documents(force_reload=False)

            # Создаем интерфейс бота
            self.bot_interface = BotInterface(
                rag_system=self.rag_system,
                model_name=self.settings.gpt_model,
                temperature=0.7,
            )

            self.logger.info("RAG система успешно инициализирована")
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации RAG системы: {str(e)}")
            raise

    async def get_rag_response(
        self, query: str, system_prompt: Optional[str] = None
    ) -> str:
        """
        Получить ответ из RAG системы.

        Args:
            query: Запрос пользователя
            system_prompt: Системный промпт (опционально)

        Returns:
            str: Ответ от RAG системы
        """
        try:
            # Если системный промпт не предоставлен, используем промпт из настроек
            if not system_prompt and hasattr(self.settings, "system_prompt"):
                system_prompt = self.settings.system_prompt

            # Получаем ответ от RAG системы
            response = self.bot_interface.process_query(
                query=query,
                k=4,  # Количество релевантных документов
                system_prompt=system_prompt,
                use_mmr=True,
            )

            return response
        except Exception as e:
            self.logger.error(f"Ошибка при получении ответа из RAG системы: {str(e)}")
            return f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}"

    def extract_query_from_messages(self, messages: List[Message]) -> str:
        """
        Извлечь запрос пользователя из истории сообщений.

        Args:
            messages: История сообщений

        Returns:
            str: Запрос пользователя
        """
        # Извлекаем последнее сообщение пользователя
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            return ""

        return user_messages[-1].content
