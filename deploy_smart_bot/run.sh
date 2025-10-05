#!/bin/bash

echo "🤖 Запуск Support Bot v4 - Smart Bot..."
echo "========================================"

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📋 Скопируйте env_example.txt в .env и заполните настройки"
    exit 1
fi

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    exit 1
fi

# Проверяем pip
if ! command -v pip3 &> /dev/null; then
    echo "📦 Установка pip..."
    python3 -m ensurepip --upgrade
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

# Запускаем бота
echo "🚀 Запуск бота..."
python3 main.py
