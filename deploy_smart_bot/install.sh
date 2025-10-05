#!/bin/bash

echo "📦 Установка Support Bot v4 - Smart Bot..."
echo "=========================================="

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    echo "📥 Установите через пакетный менеджер вашей системы"
    exit 1
fi

echo "✅ Python найден"
python3 --version

# Обновляем pip
echo "📦 Обновление pip..."
python3 -m pip install --upgrade pip

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Ошибка установки зависимостей!"
    exit 1
fi

echo "✅ Зависимости установлены успешно!"

# Проверяем наличие .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "📋 Скопируйте env_example.txt в .env и заполните настройки"
    cp env_example.txt .env
    echo "✅ Создан файл .env из шаблона"
fi

echo "🎉 Установка завершена!"
echo "📋 Не забудьте настроить .env файл перед запуском"
echo "🚀 Для запуска используйте ./run.sh"

