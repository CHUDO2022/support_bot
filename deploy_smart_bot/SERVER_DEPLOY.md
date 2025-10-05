# 🚀 Деплой на Linux сервер

## Быстрый старт на сервере

### 1. Подготовка сервера

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python3 и pip
sudo apt install python3 python3-pip python3-venv -y

# Устанавливаем дополнительные зависимости
sudo apt install git curl wget unzip -y
```

### 2. Загрузка и настройка бота

```bash
# Переходим в домашнюю директорию
cd ~

# Создаем директорию для бота
mkdir -p ~/bots/support_bot
cd ~/bots/support_bot

# Загружаем файлы (замените на ваш способ загрузки)
# Вариант 1: Если есть архив
# wget https://your-server.com/support_bot_v4_smart_deploy.zip
# unzip support_bot_v4_smart_deploy.zip

# Вариант 2: Если клонируете из git
# git clone https://github.com/your-repo/support_bot.git .

# Вариант 3: Если загружаете через SCP/SFTP
# scp -r user@local-machine:/path/to/deploy_smart_bot/* ./
```

### 3. Настройка окружения

```bash
# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Создаем .env файл
cp env_example.txt .env
nano .env  # заполните настройки
```

### 4. Заполните .env файл

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
ASSISTANT_ID=asst_your-assistant-id-here

# Telegram Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
PHONE_NUMBER=+79123456789

# Bot Configuration
BOT_NAME=support_bot_v4
LOG_LEVEL=INFO
```

### 5. Установка и запуск

```bash
# Устанавливаем зависимости
pip install -r requirements.txt

# Делаем скрипты исполняемыми
chmod +x *.sh

# Запускаем бота
./quick_start.sh
```

## 🔧 Настройка автозапуска (systemd)

### 1. Создаем systemd сервис

```bash
sudo nano /etc/systemd/system/support-bot.service
```

### 2. Содержимое файла сервиса

```ini
[Unit]
Description=Support Bot v4 - Smart Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bots/support_bot
Environment=PATH=/home/ubuntu/bots/support_bot/venv/bin
ExecStart=/home/ubuntu/bots/support_bot/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Активируем сервис

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable support-bot

# Запускаем сервис
sudo systemctl start support-bot

# Проверяем статус
sudo systemctl status support-bot

# Просмотр логов
sudo journalctl -u support-bot -f
```

## 🐳 Docker деплой (альтернатива)

### 1. Установка Docker

```bash
# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER

# Перезагружаемся или выполняем
newgrp docker
```

### 2. Запуск через Docker Compose

```bash
# Создаем .env файл
cp env_example.txt .env
nano .env  # заполните настройки

# Запускаем контейнер
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Логи systemd сервиса
sudo journalctl -u support-bot -f

# Логи приложения
tail -f bot.log

# Логи Docker
docker-compose logs -f
```

### Мониторинг ресурсов

```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Сетевые соединения
netstat -tulpn | grep python
```

## 🔄 Обновление бота

```bash
# Останавливаем сервис
sudo systemctl stop support-bot

# Создаем бэкап
cp -r ~/bots/support_bot ~/bots/support_bot_backup_$(date +%Y%m%d)

# Загружаем новую версию
# (замените на ваш способ обновления)

# Перезапускаем сервис
sudo systemctl start support-bot

# Проверяем статус
sudo systemctl status support-bot
```

## 🛠️ Устранение проблем

### Проблема: "Command 'python' not found"

```bash
# Создаем симлинк
sudo ln -s /usr/bin/python3 /usr/bin/python
```

### Проблема: "Permission denied"

```bash
# Даем права на выполнение
chmod +x *.sh
chmod +x *.py
```

### Проблема: "Module not found"

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Переустанавливаем зависимости
pip install -r requirements.txt
```

### Проблема: "Port already in use"

```bash
# Находим процесс
sudo lsof -i :8000

# Убиваем процесс
sudo kill -9 PID
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u support-bot -f`
2. Проверьте статус: `sudo systemctl status support-bot`
3. Проверьте .env файл: `cat .env`
4. Проверьте права доступа: `ls -la`

## 🔐 Безопасность

### Рекомендации:

1. Используйте виртуальное окружение
2. Не храните .env файл в git
3. Ограничьте права доступа к файлам
4. Используйте firewall для ограничения доступа
5. Регулярно обновляйте зависимости

```bash
# Ограничиваем права на .env
chmod 600 .env

# Создаем отдельного пользователя для бота
sudo useradd -m -s /bin/bash botuser
sudo chown -R botuser:botuser ~/bots/support_bot
```

