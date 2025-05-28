"""
Сервис для взаимодействия с OpenAI API.
"""

from typing import List, Optional, Dict, Any
import logging
import time
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import Settings
from src.models.message import Message, MessageResponse


class OpenAIService:
    """Сервис для работы с OpenAI API."""
    
    def __init__(self, settings: Settings):
        """
        Инициализация сервиса.
        
        Args:
            settings: Настройки приложения
        """
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.gpt_model
        self.system_prompt = settings.system_prompt
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
    
    async def generate_response(
        self, 
        messages: List[Message], 
        stream: bool = False
    ) -> MessageResponse:
        """
        Генерация ответа с использованием OpenAI API.
        
        Args:
            messages: История сообщений
            stream: Использовать потоковую передачу ответа
            
        Returns:
            MessageResponse: Ответ от модели
        """
        # Добавляем системный промпт, если его нет в сообщениях
        has_system_prompt = any(msg.role == "system" for msg in messages)
        
        formatted_messages = []
        if not has_system_prompt and self.system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # Форматируем сообщения для API
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        try:
            self.logger.info(f"Sending request to OpenAI API with {len(formatted_messages)} messages")
            
            if stream:
                return await self._handle_stream_response(formatted_messages)
            else:
                return await self._handle_standard_response(formatted_messages)
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def _handle_standard_response(self, formatted_messages: List[Dict[str, str]]) -> MessageResponse:
        """
        Обработка стандартного (не потокового) ответа от API.
        С автоматическими повторными попытками при сбоях.
        
        Args:
            formatted_messages: Форматированные сообщения для API
            
        Returns:
            MessageResponse: Ответ от модели
        """
        start_time = time.time()
        try:
            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            
            process_time = time.time() - start_time
            self.logger.info(f"OpenAI API response received in {process_time:.2f}s")
            
            assistant_message = Message(
                role="assistant",
                content=response.choices[0].message.content or ""
            )
            
            return MessageResponse(
                message=assistant_message,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(f"Error in OpenAI API call after {process_time:.2f}s: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def _handle_stream_response(self, formatted_messages: List[Dict[str, str]]) -> MessageResponse:
        """
        Обработка потокового ответа от API.
        С автоматическими повторными попытками при сбоях.
        
        Args:
            formatted_messages: Форматированные сообщения для API
            
        Returns:
            MessageResponse: Собранный ответ от модели
        """
        start_time = time.time()
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True,
            )
            
            collected_content = ""
            finish_reason = None
            chunk_count = 0
            
            async for chunk in stream:
                chunk_count += 1
                if chunk.choices and chunk.choices[0].delta.content:
                    collected_content += chunk.choices[0].delta.content
                
                if chunk.choices and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason
            
            process_time = time.time() - start_time
            self.logger.info(f"OpenAI API stream completed in {process_time:.2f}s with {chunk_count} chunks")
            
            assistant_message = Message(
                role="assistant",
                content=collected_content
            )
            
            return MessageResponse(
                message=assistant_message,
                finish_reason=finish_reason,
                # Для потоковых ответов информация об использовании токенов недоступна
                usage=None
            )
        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(f"Error in OpenAI API stream after {process_time:.2f}s: {str(e)}")
            raise
