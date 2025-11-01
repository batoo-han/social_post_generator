#!/bin/bash
# Скрипт автоматического обновления Social Post Generator на сервере
# Автоматически определяет тип обновления: полное (rebuild) или частичное (restart)

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для красивого вывода
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Баннер
echo ""
echo "=========================================="
echo "  🚀 Social Post Generator Updater"
echo "=========================================="
echo ""

# Проверка что мы в правильной директории
if [ ! -f "docker-compose.yml" ]; then
    error "Файл docker-compose.yml не найден!"
    error "Запустите скрипт из директории проекта"
    exit 1
fi

# Проверка что Docker запущен
if ! docker info > /dev/null 2>&1; then
    error "Docker не запущен или недоступен!"
    exit 1
fi

# 1. Создание backup
info "Создание backup текущей версии..."
BACKUP_DIR="backups"
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

# Backup конфигурации
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/${BACKUP_NAME}.env"
    success "Backup .env создан"
fi

# Backup логов
if [ -d "logs" ]; then
    tar -czf "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" logs/ 2>/dev/null || true
    success "Backup логов создан"
fi

# 2. Получение изменений из Git
info "Проверка обновлений из Git..."

# Сохраняем текущий коммит
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Fetch изменений
if git fetch origin 2>/dev/null; then
    success "Обновления получены из Git"
    
    # Проверяем есть ли изменения
    BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
    
    if [ "$BEHIND" -eq 0 ]; then
        info "Уже используется последняя версия"
        warning "Пропускаем git pull"
    else
        info "Доступно $BEHIND новых коммитов"
        
        # Показываем что изменилось
        info "Изменения:"
        git log HEAD..origin/main --oneline --no-decorate | head -5
        
        # Pull изменений
        if git pull origin main; then
            success "Изменения применены"
        else
            error "Ошибка при git pull"
            warning "Продолжаем с текущей версией"
        fi
    fi
else
    warning "Git remote недоступен, используем локальную версию"
fi

# 3. Определение типа обновления
info "Анализ изменений для определения типа обновления..."

NEED_REBUILD=false
CHANGED_FILES=$(git diff --name-only $CURRENT_COMMIT HEAD 2>/dev/null || echo "")

# Проверяем какие файлы изменились
if echo "$CHANGED_FILES" | grep -qE "Dockerfile|docker-compose.yml|requirements.txt"; then
    warning "Обнаружены изменения в Docker/зависимостях"
    NEED_REBUILD=true
fi

if echo "$CHANGED_FILES" | grep -qE "\.py$"; then
    warning "Обнаружены изменения в Python коде"
    NEED_REBUILD=true
fi

if echo "$CHANGED_FILES" | grep -qE "static/"; then
    warning "Обнаружены изменения в статических файлах"
    # Для статики можно не пересобирать, но лучше пересобрать
    NEED_REBUILD=true
fi

# Если нет git или изменений не определить - делаем rebuild на всякий случай
if [ -z "$CHANGED_FILES" ] && [ "$CURRENT_COMMIT" != "unknown" ]; then
    info "Изменений не обнаружено, только перезапуск"
    NEED_REBUILD=false
elif [ "$CURRENT_COMMIT" == "unknown" ]; then
    warning "Git история недоступна, выполняется полная пересборка"
    NEED_REBUILD=true
fi

# 4. Остановка текущей версии
info "Остановка текущей версии..."
docker-compose down
success "Контейнеры остановлены"

# 5. Выполнение обновления
if [ "$NEED_REBUILD" = true ]; then
    echo ""
    warning "=========================================="
    warning "  ПОЛНОЕ ОБНОВЛЕНИЕ (Rebuild)"
    warning "=========================================="
    echo ""
    
    # Удаление старых образов
    info "Удаление старых образов..."
    docker-compose down --rmi local 2>/dev/null || true
    
    # Очистка
    info "Очистка build cache..."
    docker builder prune -f
    
    # Пересборка
    info "Пересборка образа (это может занять несколько минут)..."
    if docker-compose build --no-cache --pull; then
        success "Образ успешно пересобран"
    else
        error "Ошибка при сборке образа!"
        
        # Пытаемся восстановить из backup
        if [ -f "$BACKUP_DIR/${BACKUP_NAME}.env" ]; then
            warning "Попытка восстановления из backup..."
            cp "$BACKUP_DIR/${BACKUP_NAME}.env" .env
        fi
        
        exit 1
    fi
else
    echo ""
    info "=========================================="
    info "  ЧАСТИЧНОЕ ОБНОВЛЕНИЕ (Restart)"
    info "=========================================="
    echo ""
    
    info "Пересборка не требуется, только перезапуск"
fi

# 6. Запуск обновленной версии
info "Запуск обновленной версии..."
if docker-compose up -d; then
    success "Контейнеры запущены"
else
    error "Ошибка при запуске контейнеров!"
    exit 1
fi

# 7. Проверка здоровья
info "Проверка работоспособности..."
sleep 5  # Даем время на запуск

# Проверяем что контейнер работает
if docker-compose ps | grep -q "Up"; then
    success "Контейнер запущен"
else
    error "Контейнер не запустился!"
    docker-compose logs --tail=50
    exit 1
fi

# Проверяем health endpoint
info "Проверка health endpoint..."
sleep 10  # Даем время приложению полностью запуститься

for i in {1..5}; do
    if curl -s http://localhost:8082/api/health > /dev/null 2>&1; then
        success "Приложение работает корректно!"
        break
    else
        warning "Попытка $i/5: приложение еще запускается..."
        sleep 5
    fi
    
    if [ $i -eq 5 ]; then
        error "Приложение не отвечает после запуска!"
        warning "Проверьте логи: docker-compose logs"
        exit 1
    fi
done

# 8. Итоговая информация
echo ""
echo "=========================================="
success "Обновление завершено успешно!"
echo "=========================================="
echo ""

# Показываем версию
info "Текущий коммит: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

# Статус контейнеров
info "Статус контейнеров:"
docker-compose ps

echo ""
info "Приложение доступно на: http://localhost:8082"
info "Health check: http://localhost:8082/api/health"
info "API документация: http://localhost:8082/docs"

echo ""
info "Backup сохранен в: $BACKUP_DIR/${BACKUP_NAME}*"

echo ""
info "Для просмотра логов: docker-compose logs -f"
echo ""

# Очистка старых backup (старше 7 дней)
find "$BACKUP_DIR" -name "backup_*" -mtime +7 -delete 2>/dev/null || true

success "Готово! 🎉"

