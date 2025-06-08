"""
Основной модуль RAG системы, объединяющий все компоненты.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.documents import Document

from .document_loader import DocumentLoader
from .embeddings import EmbeddingManager
from .retriever import Retriever
from .text_splitter import TextSplitter
from .vector_store import VectorStore


class RAGSystem:
    """Класс, объединяющий все компоненты RAG системы."""

    def __init__(
        self,
        data_dir: str,
        persist_dir: str,
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_chroma: bool = False,
    ):
        """
        Инициализировать RAG систему.

        Args:
            data_dir: Директория с исходными данными
            persist_dir: Директория для сохранения векторного хранилища
            embedding_model: Модель для создания эмбеддингов
            chunk_size: Размер чанка при разделении документов
            chunk_overlap: Размер перекрытия между чанками
            use_chroma: Использовать Chroma вместо FAISS
        """
        self.data_dir = data_dir
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_chroma = use_chroma

        self.embeddings = EmbeddingManager.get_embeddings(model_name=embedding_model)
        self.retriever = None

    def load_and_index_documents(self, force_reload: bool = False) -> None:
        """
        Загрузить и индексировать документы.

        Args:
            force_reload: Принудительно перезагрузить и переиндексировать документы
        """
        # Проверяем, существует ли индекс
        index_exists = (
            os.path.exists(self.persist_dir) and len(os.listdir(self.persist_dir)) > 0
        )

        # Если индекс существует и не требуется перезагрузка, загружаем существующий индекс
        if index_exists and not force_reload:
            self._load_existing_index()
            return

        # Загружаем документы
        documents = DocumentLoader.load_documents_from_dir(self.data_dir)
        if not documents:
            raise ValueError(f"Не удалось загрузить документы из {self.data_dir}")

        print(f"Загружено {len(documents)} документов")

        # Разбиваем документы на чанки
        chunks = TextSplitter.split_documents(
            documents=documents,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        print(f"Создано {len(chunks)} чанков")

        # Создаем векторное хранилище
        if self.use_chroma:
            vector_store = VectorStore.create_chroma_db(
                documents=chunks,
                embeddings=self.embeddings,
                persist_directory=self.persist_dir,
            )
        else:
            vector_store = VectorStore.create_faiss_index(
                documents=chunks,
                embeddings=self.embeddings,
                persist_directory=self.persist_dir,
            )

        self.retriever = Retriever(vector_store)
        print(f"Индексы созданы и сохранены в {self.persist_dir}")

    def _load_existing_index(self) -> None:
        """Загрузить существующий индекс."""
        try:
            if self.use_chroma:
                vector_store = VectorStore.load_chroma_db(
                    persist_directory=self.persist_dir,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True,  # Разрешаем десериализацию для локального использования
                )
            else:
                vector_store = VectorStore.load_faiss_index(
                    persist_directory=self.persist_dir,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True,  # Разрешаем десериализацию для локального использования
                )

            self.retriever = Retriever(vector_store)
            print(f"Индекс загружен из {self.persist_dir}")
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке индекса: {str(e)}")

    def query(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_mmr: bool = True,
    ) -> List[Document]:
        """
        Выполнить запрос к RAG системе.

        Args:
            query: Запрос пользователя
            k: Количество документов для возврата
            fetch_k: Количество документов для предварительной выборки (для MMR)
            lambda_mult: Коэффициент для разнообразия результатов (для MMR)
            filter_metadata: Фильтр по метаданным
            use_mmr: Использовать максимально маргинальную релевантность

        Returns:
            List[Document]: Список релевантных документов
        """
        if not self.retriever:
            raise ValueError("Необходимо сначала загрузить и индексировать документы")

        if use_mmr:
            return self.retriever.retrieve_documents(
                query=query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult,
                filter_metadata=filter_metadata,
            )
        else:
            return self.retriever.similarity_search(
                query=query, k=k, filter_metadata=filter_metadata
            )

    def format_results(self, documents: List[Document]) -> str:
        """
        Форматировать результаты запроса.

        Args:
            documents: Список релевантных документов

        Returns:
            str: Отформатированные результаты
        """
        if not documents:
            return "Не найдено релевантных документов."

        results = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Неизвестный источник")
            file_name = Path(source).name

            results.append(f"Результат #{i} (из {file_name}):\n{doc.page_content}\n")

        return "\n".join(results)
