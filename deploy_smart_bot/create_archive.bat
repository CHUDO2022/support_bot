@echo off
chcp 65001 >nul
echo 📦 Создание архива для деплоя...
echo =================================

REM Создаем архив с текущей датой
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

echo 📅 Создаем архив: support_bot_v4_smart_%timestamp%.zip

REM Создаем архив (требуется 7-Zip или WinRAR)
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "support_bot_v4_smart_%timestamp%.zip" * -x!*.pyc -x!__pycache__ -x!*.log -x!*.session*
) else if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
    "C:\Program Files (x86)\7-Zip\7z.exe" a -tzip "support_bot_v4_smart_%timestamp%.zip" * -x!*.pyc -x!__pycache__ -x!*.log -x!*.session*
) else (
    echo ❌ 7-Zip не найден! Создайте архив вручную
    echo 📁 Включите все файлы кроме:
    echo    - *.pyc
    echo    - __pycache__
    echo    - *.log
    echo    - *.session*
    pause
    exit /b 1
)

if exist "support_bot_v4_smart_%timestamp%.zip" (
    echo ✅ Архив создан: support_bot_v4_smart_%timestamp%.zip
    echo 📁 Размер архива:
    dir "support_bot_v4_smart_%timestamp%.zip" | find "support_bot_v4_smart_%timestamp%.zip"
) else (
    echo ❌ Ошибка создания архива!
)

pause

