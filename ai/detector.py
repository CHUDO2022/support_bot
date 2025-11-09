# -*- coding: utf-8 -*-
"""
Умный детектор запросов на файлы с использованием OpenAI API
"""

import json
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class SmartFileDetector:
    """Умный детектор запросов на файлы с использованием OpenAI"""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
        
        # Системный промпт для определения типа запроса
        self.system_prompt = """
Ты - помощник для определения типа запроса пользователя в службе поддержки фулфилмента.

Типы запросов:
1. TZ_FILE - запрос на файл технического задания (Excel)
2. WAREHOUSE_IMAGES - запрос на информацию о складе, адреса, как добраться
3. GENERAL_CHAT - все остальное

ПРАВИЛА ОПРЕДЕЛЕНИЯ:

TZ_FILE - ТОЛЬКО если есть явные слова:
- "файл ТЗ", "техническое задание", "эксель файл", "бланк", "форма"
- "заполнить", "скачать файл"

WAREHOUSE_IMAGES - если есть слова о складе:
- "склад", "адрес", "где", "как добраться", "схема", "проезд"
- "покажите склад", "фото склада", "изображения склада"
- "в казани", "в москве", "найти склад"

GENERAL_CHAT - все остальное:
- Приветствия, общие вопросы, расчеты, помощь

Отвечай ТОЛЬКО в формате JSON:
{
    "type": "TZ_FILE|WAREHOUSE_IMAGES|GENERAL_CHAT",
    "confidence": 0.95,
    "reasoning": "краткое объяснение"
}
"""
    
    async def detect_request_type(self, message_text: str) -> Dict[str, any]:
        """Определяет тип запроса пользователя"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message_text}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Парсим JSON ответ
            result_text = response.choices[0].message.content.strip()
            
            # Убираем возможные markdown блоки
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result = json.loads(result_text)
            
            logger.info(f"Detected request type: {result['type']} (confidence: {result['confidence']})")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._fallback_detection(message_text)
        except Exception as e:
            logger.error(f"Error in smart detection: {e}")
            return self._fallback_detection(message_text)
    
    def _fallback_detection(self, message_text: str) -> Dict[str, any]:
        """Резервный метод определения через ключевые слова"""
        text_lower = message_text.lower()
        
        # Простые и четкие ключевые слова
        tz_keywords = ["файл тз", "техническое задание", "эксель файл", "бланк", "форма"]
        warehouse_keywords = ["склад", "адрес", "где", "как добраться", "схема", "проезд"]
        
        # Проверяем на файл ТЗ
        if any(keyword in text_lower for keyword in tz_keywords):
            return {
                "type": "TZ_FILE",
                "confidence": 0.8,
                "reasoning": "запрос на файл ТЗ"
            }
        
        # Проверяем на информацию о складе
        if any(keyword in text_lower for keyword in warehouse_keywords):
            return {
                "type": "WAREHOUSE_IMAGES",
                "confidence": 0.8,
                "reasoning": "запрос на информацию о складе"
            }
        
        # Все остальное - обычное общение
        return {
            "type": "GENERAL_CHAT",
            "confidence": 0.9,
            "reasoning": "обычное общение"
        }

async def test_smart_detector():
    """Тестирование умного детектора"""
    from openai import AsyncOpenAI
    
    # Инициализируем клиент (нужен API ключ)
    client = AsyncOpenAI(api_key="your-api-key-here")
    detector = SmartFileDetector(client)
    
    test_messages = [
        "Мне нужен файл ТЗ для расчета",
        "носки 1000 штук, ozon, москва",
        "Покажите склад и как добраться",
        "Привет! Как дела?",
        "Сколько стоит доставка футболок?",
        "Пришлите эксель файл",
        "Где находится ваш склад?",
        "Расчет для кроссовок 100 штук"
    ]
    
    print("🧪 Тестирование умного детектора запросов\n")
    
    for message in test_messages:
        print(f"Сообщение: {message}")
        try:
            result = await detector.detect_request_type(message)
            print(f"Тип: {result['type']}")
            print(f"Уверенность: {result['confidence']}")
            print(f"Объяснение: {result['reasoning']}")
        except Exception as e:
            print(f"Ошибка: {e}")
        print("-" * 50)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_smart_detector())


