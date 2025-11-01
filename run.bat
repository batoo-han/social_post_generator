@echo off
REM Скрипт быстрого запуска для Windows
echo.
echo ========================================
echo   Social Post Generator
echo   Quick Start Script
echo ========================================
echo.

REM Проверка наличия .env
if not exist .env (
    echo [ОШИБКА] Файл .env не найден!
    echo.
    echo Пожалуйста, создайте .env файл:
    echo   copy .env.example .env
    echo.
    echo И укажите ваш OPENAI_API_KEY
    echo.
    pause
    exit /b 1
)

REM Проверка наличия виртуального окружения
if not exist .venv (
    echo [ИНФО] Создание виртуального окружения...
    python -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать venv
        pause
        exit /b 1
    )
)

REM Активация venv и установка зависимостей
echo [ИНФО] Активация окружения и установка зависимостей...
call .venv\Scripts\activate.bat
pip install -r requirements.txt > nul 2>&1

REM Запуск приложения
echo.
echo ========================================
echo   Запуск приложения...
echo ========================================
echo.
echo Приложение будет доступно на:
echo   http://localhost:8082
echo.
echo Для остановки нажмите Ctrl+C
echo.

python app.py

pause

