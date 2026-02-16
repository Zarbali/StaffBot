@echo off
chcp 65001 >nul
color 0a
title Бот для управления штатной структурой

echo ============================================
echo        БОТ УПРАВЛЕНИЯ ШТАТНОЙ СТРУКТУРОЙ
echo ============================================
echo.

echo [1] Проверка Python...
python --version
if errorlevel 1 (
    echo ❌ Python не установлен!
    echo.
    echo Установите Python 3.12:
    echo 1. Скачайте с python.org
    echo 2. При установке отметьте "Add Python to PATH"
    pause
    exit
)

echo.
echo [2] Установка discord.py...
python -m pip install discord.py --quiet
echo ✅ Библиотеки установлены

echo.
echo [3] Проверка файлов...
if not exist "staff_bot.py" (
    echo ❌ Файл staff_bot.py не найден!
    pause
    exit
)

echo.
echo [4] Создание файлов данных...
if not exist "staff_data.json" (
    echo {} > staff_data.json
    echo ✅ staff_data.json создан
)

if not exist "control_panel_message.json" (
    echo {} > control_panel_message.json
    echo ✅ control_panel_message.json создан
)

echo.
echo [5] Запуск бота...
echo ============================================
echo.
echo Бот выполнит следующие действия при запуске:
echo 1. Отправит сообщение с кнопками в канал управления
echo 2. Создаст сообщения со штатной структурой
echo 3. Будет ждать нажатий на кнопки
echo.
echo ============================================
timeout /t 3 /nobreak >nul

python staff_bot.py

if errorlevel 1 (
    echo.
    echo ❌ Бот завершился с ошибкой!
    echo.
    echo Проверьте:
    echo 1. Файл .env с DISCORD_BOT_TOKEN (скопируйте .env.example в .env)
    echo 2. ID каналов в настройках
    echo 3. Права бота на сервере
)

pause9:56 11.01.2026