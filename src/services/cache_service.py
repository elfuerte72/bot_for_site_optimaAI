"""
Сервис для кэширования ответов от OpenAI API.
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
import time
from datetime import datetime, timedelta

from src.models.message import Message


class CacheService:
    """
    Сервис для кэширования ответов от OpenAI API.
    Использует in-memory кэш с ограничением по времени жизни записей.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Инициализация сервиса кэширования.
        
        Args:
            ttl_seconds: Время жизни кэша в секундах (по умолчанию 1 час)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, messages: List[Message]) -> str:
        """
        Генерация уникального ключа для кэширования на основе сообщений.
        
        Args:
            messages: Список сообщений
            
        Returns:
            str: Уникальный хэш-ключ
        """
        # Преобразуем сообщения в строку для хэширования
        messages_str = json.dumps([msg.model_dump() for msg in messages], sort_keys=True)
        return hashlib.md5(messages_str.encode()).hexdigest()
    
    def get(self, messages: List[Message]) -> Optional[Dict[str, Any]]:
        """
        Получение кэшированного ответа.
        
        Args:
            messages: Список сообщений
            
        Returns:
            Optional[Dict[str, Any]]: Кэшированный ответ или None, если кэш отсутствует
        """
        key = self._generate_key(messages)
        
        if key in self._cache:
            cache_entry = self._cache[key]
            # Проверяем, не истек ли срок действия кэша
            if time.time() - cache_entry["timestamp"] < self.ttl_seconds:
                return cache_entry["data"]
            else:
                # Удаляем устаревший кэш
                del self._cache[key]
        
        return None
    
    def set(self, messages: List[Message], data: Dict[str, Any]) -> None:
        """
        Сохранение ответа в кэш.
        
        Args:
            messages: Список сообщений
            data: Данные для кэширования
        """
        key = self._generate_key(messages)
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def clear_expired(self) -> int:
        """
        Очистка устаревших записей кэша.
        
        Returns:
            int: Количество удаленных записей
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry["timestamp"] >= self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def clear_all(self) -> int:
        """
        Полная очистка кэша.
        
        Returns:
            int: Количество удаленных записей
        """
        count = len(self._cache)
        self._cache.clear()
        return count
