"""
Модуль для загрузки документов разных форматов в RAG систему.
"""
import os
from typing import List, Dict, Union, Optional
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document


class DocumentLoader:
    """Класс для загрузки документов разных форматов."""
    
    @staticmethod
    def load_document(file_path: str) -> List[Document]:
        """
        Загрузить документ в зависимости от его типа.
        
        Args:
            file_path: Путь к документу
            
        Returns:
            List[Document]: Список документов
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return DocumentLoader._load_pdf(file_path)
        elif ext in ['.md', '.txt']:
            return DocumentLoader._load_text(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {ext}")
    
    @staticmethod
    def load_documents_from_dir(dir_path: str, recursive: bool = True) -> List[Document]:
        """
        Загрузить все документы из директории.
        
        Args:
            dir_path: Путь к директории
            recursive: Загружать ли документы из поддиректорий
            
        Returns:
            List[Document]: Список документов
        """
        documents = []
        path = Path(dir_path)
        
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Путь {dir_path} не существует или не является директорией")
        
        for file_path in path.glob("**/*" if recursive else "*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in ['.pdf', '.md', '.txt']:
                    try:
                        docs = DocumentLoader.load_document(str(file_path))
                        # Добавляем имя файла как метаданные
                        for doc in docs:
                            doc.metadata["source"] = str(file_path)
                            doc.metadata["file_name"] = file_path.name
                        documents.extend(docs)
                    except Exception as e:
                        print(f"Ошибка при загрузке файла {file_path}: {str(e)}")
        
        return documents
    
    @staticmethod
    def _load_pdf(file_path: str) -> List[Document]:
        """Загрузить PDF документ."""
        loader = PyPDFLoader(file_path)
        return loader.load()
    
    @staticmethod
    def _load_text(file_path: str) -> List[Document]:
        """Загрузить текстовый документ."""
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()
