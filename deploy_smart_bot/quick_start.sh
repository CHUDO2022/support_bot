#!/bin/bash

echo "🚀 Быстрый запуск Support Bot v4 - Smart Bot"
echo "============================================="

# Проверяем Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    echo "📥 Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "📥 CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Проверяем pip3
if ! command -v pip3 &> /dev/null; then
    echo "📦 Установка pip3..."
    sudo apt update && sudo apt install python3-pip -y
fi

# Создаем .env если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp env_example.txt .env
    echo "⚠️  Заполните настройки в .env файле!"
    echo "📋 Отредактируйте: nano .env"
    read -p "Нажмите Enter после настройки .env файла..."
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

# Запускаем бота
echo "🚀 Запуск бота..."
python3 start.py

