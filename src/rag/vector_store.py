"""
Модуль для работы с векторным хранилищем.
"""

import os
from typing import Dict, List, Optional, Union

from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_community.vectorstores import FAISS, Chroma


class VectorStore:
    """Класс для работы с векторным хранилищем."""

    @staticmethod
    def create_faiss_index(
        documents: List[Document],
        embeddings: Embeddings,
        persist_directory: Optional[str] = None,
        index_name: str = "documents",
    ) -> FAISS:
        """
        Создать индекс FAISS из документов.

        Args:
            documents: Список документов
            embeddings: Модель для создания эмбеддингов
            persist_directory: Директория для сохранения индекса
            index_name: Название индекса

        Returns:
            FAISS: Векторное хранилище
        """
        db = FAISS.from_documents(documents, embeddings)

        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)
            db.save_local(folder_path=persist_directory, index_name=index_name)

        return db

    @staticmethod
    def load_faiss_index(
        persist_directory: str,
        embeddings: Embeddings,
        index_name: str = "documents",
        allow_dangerous_deserialization: bool = False,
    ) -> FAISS:
        """
        Загрузить индекс FAISS.

        Args:
            persist_directory: Директория с сохраненным индексом
            embeddings: Модель для создания эмбеддингов
            index_name: Название индекса
            allow_dangerous_deserialization: Разрешить десериализацию pickle файлов

        Returns:
            FAISS: Векторное хранилище
        """
        return FAISS.load_local(
            folder_path=persist_directory,
            embeddings=embeddings,
            index_name=index_name,
            allow_dangerous_deserialization=allow_dangerous_deserialization,
        )

    @staticmethod
    def create_chroma_db(
        documents: List[Document],
        embeddings: Embeddings,
        persist_directory: str,
        collection_name: str = "documents",
    ) -> Chroma:
        """
        Создать базу данных Chroma из документов.

        Args:
            documents: Список документов
            embeddings: Модель для создания эмбеддингов
            persist_directory: Директория для сохранения базы данных
            collection_name: Название коллекции

        Returns:
            Chroma: Векторное хранилище
        """
        return Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name,
        )

    @staticmethod
    def load_chroma_db(
        persist_directory: str,
        embeddings: Embeddings,
        collection_name: str = "documents",
        allow_dangerous_deserialization: bool = False,
    ) -> Chroma:
        """
        Загрузить базу данных Chroma.

        Args:
            persist_directory: Директория с сохраненной базой данных
            embeddings: Модель для создания эмбеддингов
            collection_name: Название коллекции
            allow_dangerous_deserialization: Разрешить десериализацию pickle файлов

        Returns:
            Chroma: Векторное хранилище
        """
        return Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=collection_name,
            allow_dangerous_deserialization=allow_dangerous_deserialization,
        )
