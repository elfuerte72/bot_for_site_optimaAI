"""
Модуль для получения релевантных документов из векторного хранилища.
"""

from typing import Any, Dict, List, Optional, Union

from langchain.schema import Document
from langchain.vectorstores.base import VectorStore


class Retriever:
    """Класс для получения релевантных документов из векторного хранилища."""

    def __init__(self, vector_store: VectorStore):
        """
        Инициализировать ретривер.

        Args:
            vector_store: Векторное хранилище
        """
        self.vector_store = vector_store

    def retrieve_documents(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Получить релевантные документы из векторного хранилища.

        Args:
            query: Запрос пользователя
            k: Количество документов для возврата
            fetch_k: Количество документов для предварительной выборки
            lambda_mult: Коэффициент для разнообразия результатов
            filter_metadata: Фильтр по метаданным

        Returns:
            List[Document]: Список релевантных документов
        """
        # Используем максимально маргинальную релевантность для улучшения разнообразия результатов
        retriever = self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult,
                "filter": filter_metadata,
            },
        )

        return retriever.get_relevant_documents(query)

    def similarity_search(
        self, query: str, k: int = 4, filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Выполнить поиск по сходству векторов.

        Args:
            query: Запрос пользователя
            k: Количество документов для возврата
            filter_metadata: Фильтр по метаданным

        Returns:
            List[Document]: Список релевантных документов
        """
        return self.vector_store.similarity_search(
            query=query, k=k, filter=filter_metadata
        )
