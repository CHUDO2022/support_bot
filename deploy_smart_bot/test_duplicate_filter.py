#!/usr/bin/env python3
"""
Тест фильтра дубликатов сообщений
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duplicate_filter import DuplicateMessageFilter, is_duplicate_message, get_duplicate_stats

def test_duplicate_filter():
    """Тестирует работу фильтра дубликатов"""
    print("🧪 Тестирование фильтра дубликатов...")
    print("=" * 50)
    
    # Создаем новый фильтр для тестов
    filter_instance = DuplicateMessageFilter(
        time_window=60,  # 1 минута для тестов
        max_messages_per_user=5,
        similarity_threshold=0.8
    )
    
    user_id = 12345
    
    # Тест 1: Обычные сообщения
    print("📝 Тест 1: Обычные сообщения")
    messages = [
        "Привет!",
        "Как дела?",
        "Покажи склад",
        "Расчет логистики",
        "Спасибо!"
    ]
    
    for i, msg in enumerate(messages, 1):
        is_dup = filter_instance.is_duplicate(user_id, msg)
        print(f"  {i}. '{msg}' -> {'🚫 ДУБЛИКАТ' if is_dup else '✅ Новое'}")
    
    print()
    
    # Тест 2: Точные дубликаты
    print("📝 Тест 2: Точные дубликаты")
    duplicate_messages = [
        "Привет!",
        "Привет!",
        "Как дела?",
        "Как дела?",
        "Как дела?"
    ]
    
    for i, msg in enumerate(duplicate_messages, 1):
        is_dup = filter_instance.is_duplicate(user_id, msg)
        print(f"  {i}. '{msg}' -> {'🚫 ДУБЛИКАТ' if is_dup else '✅ Новое'}")
    
    print()
    
    # Тест 3: Похожие сообщения
    print("📝 Тест 3: Похожие сообщения")
    similar_messages = [
        "Покажи склад",
        "Покажи склад!",
        "Покажи склад пожалуйста",
        "Покажи склад в Казани",
        "Покажи склад в Москве"
    ]
    
    for i, msg in enumerate(similar_messages, 1):
        is_dup = filter_instance.is_duplicate(user_id, msg)
        print(f"  {i}. '{msg}' -> {'🚫 ДУБЛИКАТ' if is_dup else '✅ Новое'}")
    
    print()
    
    # Тест 4: Разные пользователи
    print("📝 Тест 4: Разные пользователи")
    user2_id = 67890
    same_message = "Привет!"
    
    is_dup1 = filter_instance.is_duplicate(user_id, same_message)
    is_dup2 = filter_instance.is_duplicate(user2_id, same_message)
    
    print(f"  Пользователь {user_id}: '{same_message}' -> {'🚫 ДУБЛИКАТ' if is_dup1 else '✅ Новое'}")
    print(f"  Пользователь {user2_id}: '{same_message}' -> {'🚫 ДУБЛИКАТ' if is_dup2 else '✅ Новое'}")
    
    print()
    
    # Тест 5: Статистика
    print("📊 Статистика:")
    stats = filter_instance.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    
    # Тест 6: Очистка кэша
    print("🧹 Тест 6: Очистка кэша")
    print(f"  Кэш пользователя {user_id} до очистки: {len(filter_instance.user_messages[user_id])}")
    filter_instance.clear_user_cache(user_id)
    print(f"  Кэш пользователя {user_id} после очистки: {len(filter_instance.user_messages[user_id])}")
    
    print()
    print("✅ Тестирование завершено!")

def test_global_functions():
    """Тестирует глобальные функции"""
    print("\n🌐 Тестирование глобальных функций...")
    print("=" * 50)
    
    user_id = 11111
    
    # Тест глобальных функций
    messages = [
        "Тест 1",
        "Тест 1",  # дубликат
        "Тест 2",
        "Тест 1",  # дубликат
        "Тест 3"
    ]
    
    for i, msg in enumerate(messages, 1):
        is_dup = is_duplicate_message(user_id, msg)
        print(f"  {i}. '{msg}' -> {'🚫 ДУБЛИКАТ' if is_dup else '✅ Новое'}")
    
    # Статистика
    stats = get_duplicate_stats()
    print(f"\n📊 Глобальная статистика:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_duplicate_filter()
    test_global_functions()

