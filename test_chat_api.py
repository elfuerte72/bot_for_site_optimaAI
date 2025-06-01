#!/usr/bin/env python3
"""
Тест Chat API с RAG системой.
"""

import json
import requests

def test_chat_api():
    """Тестирует Chat API."""
    base_url = "http://localhost:8000"
    
    # Тестовые запросы
    test_queries = [
        "Расскажи о компании Optima AI",
        "Какие услуги предлагает Академия?",
        "Сколько стоит обучение AI-Full Stack?",
        "Кто основатели компании?",
        "Что дает прокачка навыка промптинга?"
    ]
    
    print("🚀 Тестирование Chat API с RAG системой")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Тест #{i}: {query}")
        print("-" * 40)
        
        # Подготавливаем запрос
        payload = {
            "messages": [
                {"role": "user", "content": query}
            ],
            "use_cache": False,
            "stream": False
        }
        
        try:
            # Отправляем запрос с API ключом
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": "your_optional_api_key_for_authentication"
            }
            response = requests.post(
                f"{base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get("message", {}).get("content", "")
                processing_time = data.get("processing_time", 0)
                from_cache = data.get("from_cache", False)
                
                print(f"✅ Статус: {response.status_code}")
                print(f"⏱️ Время обработки: {processing_time:.2f}с")
                print(f"💾 Из кэша: {from_cache}")
                print(f"📄 Длина ответа: {len(bot_response)} символов")
                
                # Проверяем на markdown символы
                markdown_symbols = ['**', '*', '#', '`', '[', ']', '>', '|', '~~']
                found_markdown = []
                for symbol in markdown_symbols:
                    if symbol in bot_response:
                        found_markdown.append(symbol)
                
                if found_markdown:
                    print(f"⚠️ Найдены markdown символы: {found_markdown}")
                else:
                    print("✅ Markdown символы успешно удалены")
                
                print(f"\n💬 Ответ бота:")
                print(bot_response[:300] + "..." if len(bot_response) > 300 else bot_response)
                
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(f"📄 Ответ: {response.text}")
                
        except Exception as e:
            print(f"❌ Исключение: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено!")

if __name__ == "__main__":
    test_chat_api()