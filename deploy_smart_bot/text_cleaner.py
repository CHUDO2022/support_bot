# -*- coding: utf-8 -*-
"""
Модуль для очистки текста от меток source и других служебных символов
"""

import re
import logging

logger = logging.getLogger(__name__)

def clean_source_marks(text: str) -> str:
    """
    Очищает текст от меток вида [цифры:цифрыsource], [цифры:цифрыtsource], 【цифры:цифры†source】 и подобных.
    Сохраняет форматирование текста, включая отступы и табуляцию.
    
    Args:
        text (str): Исходный текст для очистки
        
    Returns:
        str: Очищенный текст
    """
    if not text or not isinstance(text, str):
        return text
    
    try:
        # Расширенное регулярное выражение для поиска различных меток
        # Паттерны включают разные типы скобок и символы
        patterns = [
            # Обычные квадратные скобки
            r'\[\d+:\d+source\]',      # [8:14source]
            r'\[\d+:\d+tsource\]',     # [8:0tsource]
            r'\[\d+:\d+ssource\]',     # [цифры:цифрыssource]
            r'\[\d+:\d+[a-z]*source\]', # любые другие варианты с буквами перед source
            
            # Специальные скобки 【】 с символом † и любым содержимым
            r'【\d+:\d+†[^】]*】',      # 【4:11†source】, 【4:5†Intensivny_kurs_bashkirskogo_yazyka.pdf】
            
            # Другие возможные варианты скобок
            r'「\d+:\d+[a-z]*source」',   # японские скобки
            r'〈\d+:\d+[a-z]*source〉',   # угловые скобки
            r'《\d+:\d+[a-z]*source》',   # двойные угловые скобки
            
            # Специальные случаи для addresses.txt
            r'\[\d+:\d+taddresses\.txt\]',  # [6:0taddresses.txt]
            r'【\d+:\d+†addresses\.txt】',   # 【6:0†addresses.txt】
        ]
        
        cleaned_text = text
        
        # Применяем все паттерны
        for pattern in patterns:
            # Удаляем все найденные метки
            cleaned_text = re.sub(pattern, '', cleaned_text)
            
            # Логируем найденные метки
            matches = re.findall(pattern, text)
            if matches:
                logger.info(f"Очищено {len(matches)} меток по паттерну {pattern}: {matches}")
        
        # Обрабатываем пробелы более аккуратно, сохраняя структуру
        # Удаляем только множественные пробелы в середине строк, но сохраняем отступы
        lines = cleaned_text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Удаляем множественные пробелы
            content = re.sub(r' +', ' ', line)
            
            # Удаляем пробелы в начале и конце строки
            content = content.strip()
            
            processed_lines.append(content)
        
        # Собираем текст обратно
        cleaned_text = '\n'.join(processed_lines)
        
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Ошибка при очистке текста от меток source: {e}")
        return text

def clean_all_text_marks(text: str) -> str:
    """
    Очищает текст от различных типов меток и форматирования.
    Сохраняет структуру текста и отступы.
    
    Args:
        text (str): Исходный текст для очистки
        
    Returns:
        str: Очищенный текст
    """
    if not text or not isinstance(text, str):
        return text
    
    try:
        # Очищаем от меток source
        cleaned_text = clean_source_marks(text)
        
        # Дополнительные паттерны для очистки (можно расширить)
        
        # Удаляем пустые квадратные скобки []
        cleaned_text = re.sub(r'\[\s*\]', '', cleaned_text)
        
        # Удаляем скобки с пробелами [ ]
        cleaned_text = re.sub(r'\[\s+\]', '', cleaned_text)
        
        # Обрабатываем пробелы аккуратно, сохраняя структуру
        lines = cleaned_text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Сохраняем отступы в начале строки
            leading_spaces = len(line) - len(line.lstrip())
            content = line.lstrip()
            
            # Удаляем множественные пробелы только в содержимом
            content = re.sub(r' +', ' ', content)
            
            # Восстанавливаем отступы
            processed_line = ' ' * leading_spaces + content
            processed_lines.append(processed_line)
        
        # Собираем текст обратно
        cleaned_text = '\n'.join(processed_lines)
        
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Ошибка при общей очистке текста: {e}")
        return text

def test_cleaner():
    """Тестирует работу очистки текста"""
    test_cases = [
        # Простые случаи
        ("Привет [8:14source] как дела?", "Привет как дела?"),
        ("[12:1source] Начало текста", "Начало текста"),
        ("Конец текста [5:10source]", "Конец текста"),
        
        # Специальные случаи для addresses.txt
        ("В моей базе есть информация о складе в Москве: ул. Поляны, д. 5А, стр. 1[6:0taddresses.txt].", 
         "В моей базе есть информация о складе в Москве: ул. Поляны, д. 5А, стр. 1."),
        
        # Специальные скобки
        ("【6:0†addresses.txt】 Адрес склада", "Адрес склада"),
        
        # Множественные метки
        ("[1:5source] Первая [2:8source] Вторая [3:12source] Третья", "Первая Вторая Третья"),
        
        # Без меток
        ("Обычный текст без меток", "Обычный текст без меток"),
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ ОЧИСТКИ ТЕКСТА")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected_output) in enumerate(test_cases, 1):
        try:
            result = clean_source_marks(input_text)
            
            if result == expected_output:
                print(f"✅ Тест {i}: ПРОЙДЕН")
                print(f"   Вход: '{input_text}'")
                print(f"   Выход: '{result}'")
                passed += 1
            else:
                print(f"❌ Тест {i}: ПРОВАЛЕН")
                print(f"   Вход: '{input_text}'")
                print(f"   Ожидалось: '{expected_output}'")
                print(f"   Получено: '{result}'")
                failed += 1
                
        except Exception as e:
            print(f"❌ Тест {i}: ОШИБКА - {e}")
            print(f"   Вход: '{input_text}'")
            failed += 1
            
        print("-" * 30)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"✅ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    print(f"📈 Успешность: {passed/(passed+failed)*100:.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    test_cleaner()
