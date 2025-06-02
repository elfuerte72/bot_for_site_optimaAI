"""
Сервис для взаимодействия с OpenAI API и RAG системой.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import Settings
from src.models.message import Message, MessageResponse
from src.services.rag_service import RAGService


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

        # Инициализация RAG сервиса
        try:
            self.rag_service = RAGService(settings)
            self.use_rag = True
            self.logger.info("RAG сервис успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации RAG сервиса: {str(e)}")
            self.use_rag = False

    def _clean_markdown(self, text: str) -> str:
        """
        Очистить текст от markdown символов и правильно отформатировать.
        
        Args:
            text: Текст с markdown разметкой
            
        Returns:
            str: Очищенный и отформатированный текст
        """
        if not text:
            return text
            
        # Удаляем заголовки (# ## ### и т.д.)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Обрабатываем жирный текст (**text** или __text__) - убираем звездочки, но оставляем текст
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Обрабатываем курсив (*text* или _text_) - убираем символы, но оставляем текст
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'\1', text)
        
        # Удаляем зачеркнутый текст (~~text~~)
        text = re.sub(r'~~(.*?)~~', r'\1', text)
        
        # Удаляем код (`code` или ```code```)
        text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
        
        # Удаляем ссылки [text](url) - оставляем только текст
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Удаляем изображения ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        
        # Удаляем горизонтальные линии (--- или ***)
        text = re.sub(r'^[-*]{3,}$', '', text, flags=re.MULTILINE)
        
        # Обрабатываем маркированные списки (- * +) - заменяем на абзацы с отступами
        text = re.sub(r'^[\s]*[-*+]\s+(.+)$', r'\n• \1', text, flags=re.MULTILINE)
        
        # Обрабатываем нумерованные списки (1. 2. и т.д.) - заменяем на абзацы с номерами
        def replace_numbered_list(match):
            number = match.group(1)
            content = match.group(2)
            return f'\n{number}. {content}'
        
        text = re.sub(r'^[\s]*(\d+)\.[\s]+(.+)$', replace_numbered_list, text, flags=re.MULTILINE)
        
        # Удаляем цитаты (> text)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        # Удаляем таблицы (строки с |)
        text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*[-|:]+[\s]*$', '', text, flags=re.MULTILINE)
        
        # Нормализуем переносы строк - заменяем множественные переносы на двойные
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Убираем лишние пробелы в начале и конце строк
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)
        
        # Добавляем отступы после точек в списках для лучшей читаемости
        text = re.sub(r'(\d+\.)([^\s])', r'\1 \2', text)
        
        return text.strip()

    async def generate_response(
        self, messages: List[Message], stream: bool = False
    ) -> MessageResponse:
        """
        Генерация ответа с использованием OpenAI API и RAG системы.

        Args:
            messages: История сообщений
            stream: Использовать потоковую передачу ответа

        Returns:
            MessageResponse: Ответ от модели
        """
        # Проверяем, нужно ли использовать RAG систему
        if self.use_rag and messages:
            try:
                # Извлекаем запрос пользователя из сообщений
                query = self.rag_service.extract_query_from_messages(messages)

                if query:
                    # Получаем ответ из RAG системы
                    rag_response = await self.rag_service.get_rag_response(
                        query, self.system_prompt
                    )

                    # Создаем ответное сообщение
                    assistant_message = Message(role="assistant", content=rag_response)

                    self.logger.info(
                        f"Сгенерирован ответ с использованием RAG системы: {len(rag_response)} символов"
                    )

                    return MessageResponse(
                        message=assistant_message, finish_reason="stop", usage=None
                    )
            except Exception as e:
                self.logger.error(f"Ошибка при использовании RAG системы: {str(e)}")
                # Если произошла ошибка в RAG системе, продолжаем с обычным запросом к OpenAI

        # Если не используем RAG или произошла ошибка, используем стандартный подход
        # Добавляем системный промпт, если его нет в сообщениях
        has_system_prompt = any(msg.role == "system" for msg in messages)

        formatted_messages = []
        if not has_system_prompt and self.system_prompt:
            formatted_messages.append({"role": "system", "content": self.system_prompt})

        # Форматируем сообщения для API
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        try:
            self.logger.info(
                f"Sending request to OpenAI API with {len(formatted_messages)} messages"
            )

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
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def _handle_standard_response(
        self, formatted_messages: List[Dict[str, str]]
    ) -> MessageResponse:
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

            # Получаем ответ и очищаем от markdown
            raw_content = response.choices[0].message.content or ""
            cleaned_content = self._clean_markdown(raw_content)

            assistant_message = Message(
                role="assistant", content=cleaned_content
            )

            return MessageResponse(
                message=assistant_message,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(
                f"Error in OpenAI API call after {process_time:.2f}s: {str(e)}"
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def _handle_stream_response(
        self, formatted_messages: List[Dict[str, str]]
    ) -> MessageResponse:
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
            self.logger.info(
                f"OpenAI API stream completed in {process_time:.2f}s with {chunk_count} chunks"
            )

            # Очищаем собранный контент от markdown
            cleaned_content = self._clean_markdown(collected_content)

            assistant_message = Message(role="assistant", content=cleaned_content)

            return MessageResponse(
                message=assistant_message,
                finish_reason=finish_reason,
                # Для потоковых ответов информация об использовании токенов недоступна
                usage=None,
            )
        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(
                f"Error in OpenAI API stream after {process_time:.2f}s: {str(e)}"
            )
            raise