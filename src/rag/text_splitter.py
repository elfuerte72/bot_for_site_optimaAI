"""
Модуль для разделения документов на чанки.
"""

from typing import Dict, List, Optional, Union

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextSplitter:
    """Класс для разделения документов на чанки."""

    @staticmethod
    def split_documents(
        documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Разделить документы на чанки.

        Args:
            documents: Список документов
            chunk_size: Размер чанка
            chunk_overlap: Размер перекрытия между чанками

        Returns:
            List[Document]: Список чанков
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

        return splitter.split_documents(documents)
