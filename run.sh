#!/bin/bash
# Скрипт быстрого запуска для Linux/Mac

echo ""
echo "========================================"
echo "  Social Post Generator"
echo "  Quick Start Script"
echo "========================================"
echo ""

# Проверка наличия .env
if [ ! -f .env ]; then
    echo "[ОШИБКА] Файл .env не найден!"
    echo ""
    echo "Пожалуйста, создайте .env файл:"
    echo "  cp .env.example .env"
    echo ""
    echo "И укажите ваш OPENAI_API_KEY"
    echo ""
    exit 1
fi

# Проверка наличия виртуального окружения
if [ ! -d .venv ]; then
    echo "[ИНФО] Создание виртуального окружения..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ОШИБКА] Не удалось создать venv"
        exit 1
    fi
fi

# Активация venv и установка зависимостей
echo "[ИНФО] Активация окружения и установка зависимостей..."
source .venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Запуск приложения
echo ""
echo "========================================"
echo "  Запуск приложения..."
echo "========================================"
echo ""
echo "Приложение будет доступно на:"
echo "  http://localhost:8082"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

python app.py

