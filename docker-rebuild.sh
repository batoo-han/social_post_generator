#!/bin/bash
# Скрипт полной очистки и пересборки Docker образа

echo "🧹 Полная очистка Docker..."

# Останавливаем и удаляем контейнеры
echo "Остановка контейнеров..."
docker-compose down -v

# Удаляем образ приложения
echo "Удаление образов..."
docker rmi social_post_generator-app 2>/dev/null || true
docker rmi social-post-generator:latest 2>/dev/null || true

# Удаляем все dangling образы
echo "Очистка dangling образов..."
docker image prune -f

# Удаляем build cache
echo "Очистка build cache..."
docker builder prune -af

# Удаляем директорию logs на хосте (если есть проблемы с правами)
echo "Очистка директории logs..."
sudo rm -rf logs
mkdir -p logs
chmod 777 logs

# Пересборка БЕЗ кэша
echo ""
echo "🔨 Пересборка образа..."
docker-compose build --no-cache

# Запуск
echo ""
echo "🚀 Запуск контейнеров..."
docker-compose up -d

# Проверка
echo ""
echo "📊 Статус:"
docker-compose ps

echo ""
echo "📋 Логи (Ctrl+C для выхода):"
docker-compose logs -f

