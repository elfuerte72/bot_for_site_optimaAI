#!/usr/bin/env python3
"""
Тест для проверки API ключа OpenAI.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные окружения
load_dotenv()

def test_openai_api():
    """Тестирует API ключ OpenAI."""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY не найден в переменных окружения")
        return False
    
    print(f"✅ API ключ найден (длина: {len(api_key)})")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Простой тест - получение списка моделей
        models = client.models.list()
        print(f"✅ API ключ действителен. Доступно моделей: {len(models.data)}")
        
        # Тест простого запроса
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Привет! Это тест."}],
            max_tokens=10
        )
        
        print(f"✅ Тестовый запрос успешен: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании API: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai_api()