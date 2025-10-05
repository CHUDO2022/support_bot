#!/bin/bash

echo "📊 Статус Support Bot v4 - Smart Bot"
echo "===================================="

# Проверяем статус systemd сервиса
echo "🔧 Systemd сервис:"
if systemctl is-active --quiet support-bot; then
    echo "✅ Сервис запущен"
    echo "📊 Статус:"
    systemctl status support-bot --no-pager -l
else
    echo "❌ Сервис не запущен"
    echo "📊 Статус:"
    systemctl status support-bot --no-pager -l
fi

echo ""
echo "📝 Последние логи (10 строк):"
echo "=============================="
journalctl -u support-bot --no-pager -n 10

echo ""
echo "💾 Использование ресурсов:"
echo "=========================="
echo "💽 Память:"
free -h

echo ""
echo "🖥️  CPU:"
top -bn1 | grep "Cpu(s)"

echo ""
echo "💿 Диск:"
df -h | grep -E "(Filesystem|/dev/)"

echo ""
echo "🌐 Сетевые соединения:"
echo "======================"
netstat -tulpn | grep python3 || echo "Нет активных соединений Python"

echo ""
echo "📁 Файлы бота:"
echo "=============="
BOT_DIR="$HOME/bots/support_bot"
if [ -d "$BOT_DIR" ]; then
    echo "📂 Директория: $BOT_DIR"
    echo "📊 Размер: $(du -sh "$BOT_DIR" 2>/dev/null | cut -f1)"
    echo "📝 Файлы:"
    ls -la "$BOT_DIR" | head -10
else
    echo "❌ Директория бота не найдена: $BOT_DIR"
fi

echo ""
echo "🔧 Полезные команды:"
echo "==================="
echo "   Логи:       journalctl -u support-bot -f"
echo "   Перезапуск: sudo systemctl restart support-bot"
echo "   Остановка:  sudo systemctl stop support-bot"
echo "   Запуск:     sudo systemctl start support-bot"

