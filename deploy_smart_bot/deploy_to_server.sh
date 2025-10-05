#!/bin/bash

echo "🚀 Деплой Support Bot v4 на Linux сервер"
echo "========================================"

# Проверяем, что мы на Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Этот скрипт предназначен для Linux серверов"
    exit 1
fi

# Проверяем права root
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Не рекомендуется запускать от root. Создайте обычного пользователя."
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Обновляем систему
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
echo "📦 Установка зависимостей..."
sudo apt install -y python3 python3-pip python3-venv git curl wget unzip htop

# Создаем директорию для бота
BOT_DIR="$HOME/bots/support_bot"
echo "📁 Создание директории: $BOT_DIR"
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

# Создаем виртуальное окружение
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Копируем файлы (если они уже есть в текущей директории)
if [ -f "main.py" ]; then
    echo "✅ Файлы бота уже присутствуют"
else
    echo "❌ Файлы бота не найдены!"
    echo "📋 Скопируйте файлы бота в директорию $BOT_DIR"
    echo "📁 Необходимые файлы:"
    echo "   - main.py"
    echo "   - file_manager.py"
    echo "   - text_cleaner.py"
    echo "   - human_behavior.py"
    echo "   - smart_file_detector.py"
    echo "   - requirements.txt"
    echo "   - env_example.txt"
    echo "   - Картинки/ (папка)"
    echo "   - ТЗ.xlsx"
    exit 1
fi

# Устанавливаем зависимости
echo "📦 Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp env_example.txt .env
    echo "⚠️  ВАЖНО! Отредактируйте .env файл:"
    echo "   nano .env"
    echo "   Заполните все необходимые настройки"
    read -p "Нажмите Enter после настройки .env файла..."
fi

# Создаем systemd сервис
echo "🔧 Создание systemd сервиса..."
SERVICE_FILE="/etc/systemd/system/support-bot.service"
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Support Bot v4 - Smart Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
echo "🔄 Перезагрузка systemd..."
sudo systemctl daemon-reload

# Включаем автозапуск
echo "🚀 Настройка автозапуска..."
sudo systemctl enable support-bot

# Запускаем сервис
echo "▶️  Запуск бота..."
sudo systemctl start support-bot

# Проверяем статус
echo "📊 Статус сервиса:"
sudo systemctl status support-bot --no-pager

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "📋 Полезные команды:"
echo "   Статус:     sudo systemctl status support-bot"
echo "   Логи:       sudo journalctl -u support-bot -f"
echo "   Остановка:  sudo systemctl stop support-bot"
echo "   Запуск:     sudo systemctl start support-bot"
echo "   Перезапуск: sudo systemctl restart support-bot"
echo ""
echo "📁 Файлы бота: $BOT_DIR"
echo "📝 Конфигурация: $BOT_DIR/.env"
echo "📊 Логи: sudo journalctl -u support-bot -f"

