#!/bin/bash
# Умный скрипт обновления с детектированием изменений через Git
# Автоматически определяет минимально необходимые действия

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
step() { echo -e "${CYAN}▶️  $1${NC}"; }

echo ""
echo "================================================"
echo "  🚀 Smart Update для Social Post Generator"
echo "================================================"
echo ""

# Проверки
if [ ! -f "docker-compose.yml" ]; then
    error "Не в директории проекта!"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    error "Docker не запущен!"
    exit 1
fi

# Функция создания backup
create_backup() {
    step "Создание backup..."
    BACKUP_DIR="backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup конфигурации и логов
    tar -czf "${BACKUP_PATH}.tar.gz" .env logs/ 2>/dev/null || true
    
    success "Backup: ${BACKUP_PATH}.tar.gz"
    echo "$BACKUP_PATH"
}

# Функция проверки здоровья
check_health() {
    step "Проверка работоспособности..."
    
    # Ждем запуска (приложение может загружаться до 60 секунд)
    info "Ожидание запуска приложения (60 сек)..."
    sleep 30
    
    for i in {1..10}; do
        if curl -sf http://localhost:8082/api/health >/dev/null 2>&1; then
            success "Приложение работает!"
            return 0
        fi
        warning "Попытка $i/10..."
        sleep 7
    done
    
    error "Приложение не отвечает!"
    return 1
}

# Функция отката
rollback() {
    error "Выполняется откат к предыдущей версии..."
    
    if [ -n "$BACKUP_PATH" ] && [ -f "${BACKUP_PATH}.tar.gz" ]; then
        tar -xzf "${BACKUP_PATH}.tar.gz" 2>/dev/null || true
        docker-compose up -d
        warning "Откат выполнен, восстановлена предыдущая версия"
    fi
}

# Создаем backup
BACKUP_PATH=$(create_backup)

# Сохраняем текущий коммит
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "none")
info "Текущий коммит: ${CURRENT_COMMIT:0:7}"

# Получаем обновления
step "Получение обновлений из Git..."
if git fetch origin 2>/dev/null; then
    NEW_COMMITS=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
    
    if [ "$NEW_COMMITS" -eq 0 ]; then
        info "Нет новых коммитов"
    else
        info "Доступно коммитов: $NEW_COMMITS"
        echo ""
        git log HEAD..origin/main --oneline --no-decorate | head -10
        echo ""
        
        git pull origin main
        success "Обновления применены"
    fi
else
    warning "Git remote недоступен"
fi

# Определяем что изменилось
step "Анализ изменений..."

CHANGED_FILES=$(git diff --name-only $CURRENT_COMMIT HEAD 2>/dev/null || echo "all")

# Детальный анализ
REBUILD_NEEDED=false
RESTART_NEEDED=false

if [ "$CHANGED_FILES" = "all" ]; then
    warning "Невозможно определить изменения → полная пересборка"
    REBUILD_NEEDED=true
else
    # Docker/зависимости
    if echo "$CHANGED_FILES" | grep -qE "Dockerfile|docker-compose|requirements\.txt"; then
        warning "Изменения в Docker/зависимостях → пересборка"
        REBUILD_NEEDED=true
    fi
    
    # Python код
    if echo "$CHANGED_FILES" | grep -qE "\.py$"; then
        warning "Изменения в Python коде → пересборка"
        REBUILD_NEEDED=true
    fi
    
    # Статика
    if echo "$CHANGED_FILES" | grep -qE "static/"; then
        warning "Изменения в статике → пересборка"
        REBUILD_NEEDED=true
    fi
    
    # Только конфигурация
    if echo "$CHANGED_FILES" | grep -qE "\.env"; then
        warning "Изменения в .env → перезапуск"
        RESTART_NEEDED=true
    fi
    
    # Только документация
    if echo "$CHANGED_FILES" | grep -qE "\.md$|docs/" && [ "$REBUILD_NEEDED" = false ]; then
        info "Только документация → обновление не требуется"
    fi
fi

# Выполняем обновление
echo ""
step "Остановка контейнеров..."
docker-compose down

if [ "$REBUILD_NEEDED" = true ]; then
    echo ""
    warning "================================================"
    warning "  РЕЖИМ: Полная пересборка"
    warning "================================================"
    echo ""
    
    step "Очистка старых образов..."
    docker-compose down --rmi local 2>/dev/null || true
    docker builder prune -f >/dev/null
    
    step "Пересборка образа..."
    if ! docker-compose build --no-cache; then
        error "Ошибка при сборке!"
        rollback
        exit 1
    fi
    success "Образ пересобран"
    
elif [ "$RESTART_NEEDED" = true ]; then
    echo ""
    info "================================================"
    info "  РЕЖИМ: Перезапуск (конфигурация изменена)"
    info "================================================"
    echo ""
    
else
    echo ""
    info "================================================"
    info "  РЕЖИМ: Быстрый перезапуск"
    info "================================================"
    echo ""
fi

# Запуск
step "Запуск контейнеров..."
if ! docker-compose up -d; then
    error "Ошибка при запуске!"
    rollback
    exit 1
fi

# Проверка
if check_health; then
    echo ""
    echo "================================================"
    success "🎉 Обновление успешно завершено!"
    echo "================================================"
    echo ""
    
    NEW_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    info "Версия: $CURRENT_COMMIT → $NEW_COMMIT"
    info "Backup: $BACKUP_PATH"
    echo ""
    
    docker-compose ps
    
    echo ""
    success "Приложение: http://localhost:8082"
    info "Логи: docker-compose logs -f"
    echo ""
else
    warning "Приложение запущено, но health check не прошел"
    warning "Проверьте логи: docker-compose logs"
fi

# Очистка старых backup
find backups/ -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "Готово!"

