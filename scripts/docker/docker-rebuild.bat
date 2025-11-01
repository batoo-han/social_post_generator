@echo off
REM Скрипт полной очистки и пересборки Docker образа для Windows

echo.
echo ============================================
echo   Полная очистка и пересборка Docker
echo ============================================
echo.

echo [1/6] Остановка контейнеров...
docker-compose down -v

echo.
echo [2/6] Удаление образов...
docker rmi social_post_generator-app 2>nul
docker rmi social-post-generator:latest 2>nul

echo.
echo [3/6] Очистка dangling образов...
docker image prune -f

echo.
echo [4/6] Очистка build cache...
docker builder prune -af

echo.
echo [5/6] Очистка директории logs...
if exist logs rmdir /s /q logs
mkdir logs

echo.
echo [6/6] Пересборка БЕЗ кэша...
docker-compose build --no-cache

echo.
echo ============================================
echo   Запуск контейнеров
echo ============================================
docker-compose up -d

echo.
echo Статус:
docker-compose ps

echo.
echo Нажмите любую клавишу для просмотра логов...
pause >nul

docker-compose logs -f

