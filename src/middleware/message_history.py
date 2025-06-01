"""
Middleware для управления историей сообщений.
"""

from typing import List
from src.models.message import Message


class MessageHistoryManager:
    """Менеджер для управления историей сообщений."""
    
    def __init__(self, max_messages: int = 10):
        """
        Инициализация менеджера истории.
        
        Args:
            max_messages: Максимальное количество сообщений для хранения (по умолчанию 10)
        """
        self.max_messages = max_messages
    
    def trim_messages(self, messages: List[Message]) -> List[Message]:
        """
        Обрезает историю сообщений до максимального размера.
        Сохраняет системный промпт (если есть) и последние N сообщений.
        
        Args:
            messages: Полная история сообщений
            
        Returns:
            List[Message]: Обрезанная история сообщений
        """
        if len(messages) <= self.max_messages:
            return messages
        
        # Проверяем наличие системного промпта
        system_messages = [msg for msg in messages if msg.role == "system"]
        other_messages = [msg for msg in messages if msg.role != "system"]
        
        # Берем последние N сообщений (не считая системный промпт)
        messages_to_keep = self.max_messages - len(system_messages)
        trimmed_messages = other_messages[-messages_to_keep:] if messages_to_keep > 0 else []
        
        # Возвращаем системный промпт + последние сообщения
        return system_messages + trimmed_messages
    
    def should_greet(self, messages: List[Message]) -> bool:
        """
        Определяет, нужно ли приветствовать пользователя.
        Приветствие нужно только если это первое сообщение пользователя.
        
        Args:
            messages: История сообщений
            
        Returns:
            bool: True, если нужно приветствовать
        """
        # Фильтруем только сообщения пользователя (исключая системные)
        user_messages = [msg for msg in messages if msg.role == "user"]
        
        # Приветствуем только если это первое сообщение пользователя
        return len(user_messages) <= 1