@echo off
chcp 65001 >nul
echo 📦 Установка Support Bot v4 - Smart Bot...
echo ==========================================

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    echo 📥 Скачайте с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
python --version

REM Обновляем pip
echo 📦 Обновление pip...
python -m pip install --upgrade pip

REM Устанавливаем зависимости
echo 📦 Установка зависимостей...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей!
    pause
    exit /b 1
)

echo ✅ Зависимости установлены успешно!

REM Проверяем наличие .env
if not exist .env (
    echo ⚠️  Файл .env не найден!
    echo 📋 Скопируйте env_example.txt в .env и заполните настройки
    copy env_example.txt .env
    echo ✅ Создан файл .env из шаблона
)

echo 🎉 Установка завершена!
echo 📋 Не забудьте настроить .env файл перед запуском
echo 🚀 Для запуска используйте run.bat

pause

