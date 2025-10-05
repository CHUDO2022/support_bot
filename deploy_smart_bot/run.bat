@echo off
chcp 65001 >nul
echo 🤖 Запуск Support Bot v4 - Smart Bot...
echo ========================================

REM Проверяем наличие .env файла
if not exist .env (
    echo ❌ Файл .env не найден!
    echo 📋 Скопируйте env_example.txt в .env и заполните настройки
    pause
    exit /b 1
)

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

REM Устанавливаем зависимости
echo 📦 Установка зависимостей...
pip install -r requirements.txt

REM Запускаем бота
echo 🚀 Запуск бота...
python main.py

pause

