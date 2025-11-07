#!/usr/bin/env python3
"""
Универсальный скрипт запуска Support Bot v4 - Smart Bot
Работает на Windows, Linux и macOS
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Выводит баннер запуска"""
    print("🤖 Support Bot v4 - Smart Bot")
    print("=" * 40)
    print(f"🖥️  Платформа: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 40)

def check_python_version():
    """Проверяет версию Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше!")
        print(f"📊 Текущая версия: {sys.version}")
        return False
    return True

def check_env_file():
    """Проверяет наличие .env файла"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("📋 Скопируйте env_example.txt в .env и заполните настройки")
        
        # Создаем .env из шаблона
        example_path = Path("env_example.txt")
        if example_path.exists():
            print("📝 Создаем .env из шаблона...")
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Файл .env создан из шаблона")
            print("⚠️  Не забудьте заполнить настройки в .env!")
        return False
    return True

def install_requirements():
    """Устанавливает зависимости"""
    print("📦 Проверка зависимостей...")
    
    try:
        # Проверяем, установлены ли основные пакеты
        import pyrogram
        import openai
        print("✅ Основные зависимости уже установлены")
        return True
    except ImportError:
        print("📦 Установка зависимостей...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Зависимости установлены успешно")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки зависимостей: {e}")
            return False

def start_bot():
    """Запускает бота"""
    print("🚀 Запуск бота...")
    print("=" * 40)
    
    try:
        # Импортируем и запускаем main.py
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        print("👋 До свидания!")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        print("📋 Проверьте логи и настройки в .env")
        return False
    
    return True

def main():
    """Основная функция"""
    print_banner()
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    # Проверяем .env файл
    if not check_env_file():
        print("\n⚠️  Настройте .env файл и запустите снова")
        sys.exit(1)
    
    # Устанавливаем зависимости
    if not install_requirements():
        sys.exit(1)
    
    # Запускаем бота
    start_bot()

if __name__ == "__main__":
    main()

