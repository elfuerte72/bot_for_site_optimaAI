"""
Модуль для работы с эмбеддингами.
"""
from typing import List, Dict, Union, Optional

from langchain_openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings


class EmbeddingManager:
    """Класс для работы с эмбеддингами."""
    
    @staticmethod
    def get_embeddings(model_name: str = "text-embedding-3-small") -> Embeddings:
        """
        Получить модель для создания эмбеддингов.
        
        Args:
            model_name: Название модели для создания эмбеддингов
            
        Returns:
            Embeddings: Модель для создания эмбеддингов
        """
        return OpenAIEmbeddings(model=model_name, dimensions=1536)
