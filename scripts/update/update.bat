@echo off
REM Скрипт автоматического обновления для Windows
REM Автоматически определяет нужна ли пересборка

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo   Social Post Generator Updater
echo ==========================================
echo.

REM Проверка наличия docker-compose.yml
if not exist "docker-compose.yml" (
    echo [ERROR] Файл docker-compose.yml не найден!
    echo Запустите скрипт из директории проекта
    pause
    exit /b 1
)

REM 1. Создание backup
echo [1/7] Создание backup...
set BACKUP_DIR=backups
set BACKUP_NAME=backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_NAME=%BACKUP_NAME: =0%

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

if exist .env (
    copy .env "%BACKUP_DIR%\%BACKUP_NAME%.env" >nul
    echo    - Backup .env создан
)

if exist logs (
    tar -czf "%BACKUP_DIR%\%BACKUP_NAME%_logs.tar.gz" logs 2>nul
    echo    - Backup логов создан
)

REM 2. Получение обновлений из Git
echo.
echo [2/7] Проверка обновлений...

git fetch origin >nul 2>&1
if errorlevel 0 (
    echo    - Обновления получены
    git pull origin main
    if errorlevel 0 (
        echo    - Изменения применены
    )
) else (
    echo    - Git remote недоступен, используем локальную версию
)

REM 3. Определение нужна ли пересборка
echo.
echo [3/7] Анализ изменений...

set NEED_REBUILD=0

REM Проверяем изменились ли критичные файлы за последний час
for %%f in (Dockerfile docker-compose.yml requirements.txt *.py) do (
    if exist "%%f" (
        forfiles /p . /m "%%f" /d -0 >nul 2>&1
        if not errorlevel 1 (
            echo    - Обнаружены свежие изменения в %%f
            set NEED_REBUILD=1
        )
    )
)

REM 4. Остановка контейнеров
echo.
echo [4/7] Остановка контейнеров...
docker-compose down
echo    - Контейнеры остановлены

REM 5. Выполнение обновления
echo.
if !NEED_REBUILD! equ 1 (
    echo ==========================================
    echo   ПОЛНОЕ ОБНОВЛЕНИЕ (Rebuild)
    echo ==========================================
    echo.
    
    echo [5/7] Удаление старых образов...
    docker rmi social_post_generator-app --force 2>nul
    docker image prune -f >nul
    
    echo [6/7] Пересборка образа...
    docker-compose build --no-cache
    if errorlevel 1 (
        echo.
        echo [ERROR] Ошибка при сборке!
        pause
        exit /b 1
    )
) else (
    echo ==========================================
    echo   ЧАСТИЧНОЕ ОБНОВЛЕНИЕ (Restart)
    echo ==========================================
    echo.
    echo [5/7] Пересборка не требуется
    echo [6/7] Используем существующий образ
)

REM 6. Запуск обновленной версии
echo.
echo [7/7] Запуск обновленной версии...
docker-compose up -d
if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при запуске!
    pause
    exit /b 1
)

REM 7. Проверка здоровья
echo.
echo Проверка работоспособности...
timeout /t 10 /nobreak >nul

docker-compose ps

REM Проверка health endpoint
echo.
echo Проверка health endpoint...
timeout /t 5 /nobreak >nul

curl -s http://localhost:8082/api/health >nul 2>&1
if errorlevel 0 (
    echo.
    echo ==========================================
    echo   Обновление завершено успешно!
    echo ==========================================
    echo.
    echo Приложение доступно на: http://localhost:8082
    echo Health check: http://localhost:8082/api/health
    echo.
    echo Backup сохранен в: %BACKUP_DIR%\%BACKUP_NAME%*
    echo.
    echo Для просмотра логов: docker-compose logs -f
    echo.
) else (
    echo.
    echo [WARNING] Приложение может быть еще не готово
    echo Проверьте логи: docker-compose logs
    echo.
)

REM Очистка старых backup (старше 7 дней)
forfiles /p "%BACKUP_DIR%" /s /m backup_* /d -7 /c "cmd /c del @path" 2>nul

echo Готово!
echo.
pause

