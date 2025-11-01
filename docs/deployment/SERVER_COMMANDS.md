# ⚡ Команды для сервера - Шпаргалка

## 🔥 Полная очистка и пересборка (при ошибках)

### Одной командой (копипаста):

```bash
docker-compose down -v && \
docker rmi $(docker images -q social_post_generator*) -f 2>/dev/null; \
docker image prune -af && \
docker builder prune -af && \
rm -rf logs && \
mkdir -p logs && \
chmod 777 logs && \
docker-compose build --no-cache --pull && \
docker-compose up -d && \
sleep 10 && \
docker-compose logs --tail=100
```

### Или используйте готовый скрипт:

```bash
chmod +x docker-rebuild.sh
./docker-rebuild.sh
```

---

## 🔄 Обновление приложения

### Автоматическое (рекомендуется):

```bash
./update.sh
```

### Ручное:

```bash
git pull && \
docker-compose down && \
docker-compose up -d --build && \
docker-compose ps
```

---

## 🐛 Решение проблемы "Permission denied" с логами

### Вариант 1: Очистка директории logs

```bash
# Остановить контейнеры
docker-compose down

# Удалить директорию logs
sudo rm -rf logs

# Создать заново с правильными правами
mkdir -p logs
chmod 777 logs

# Пересобрать и запустить
docker-compose build --no-cache
docker-compose up -d
```

### Вариант 2: Использовать скрипт

```bash
./docker-rebuild.sh
```

### Вариант 3: Изменить владельца

```bash
# Узнать UID пользователя в контейнере (обычно 1000)
docker-compose run --rm app id

# Изменить владельца директории logs
sudo chown -R 1000:1000 logs
chmod -R 755 logs

# Перезапустить
docker-compose up -d
```

---

## 📊 Проверка и мониторинг

### Статус контейнеров

```bash
docker-compose ps
```

### Логи

```bash
# Все логи
docker-compose logs -f

# Только приложение
docker-compose logs -f app

# Последние 100 строк
docker-compose logs --tail=100 app

# С временными метками
docker-compose logs -f --timestamps app
```

### Использование ресурсов

```bash
docker stats
```

### Health check

```bash
curl http://localhost:8082/api/health
```

### Тестовая генерация

```bash
curl -X POST http://localhost:8082/api/generate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","style":"ироничный","max_length":800}'
```

---

## 🛠️ Управление контейнерами

### Запуск

```bash
docker-compose up -d
```

### Остановка

```bash
docker-compose down
```

### Перезапуск

```bash
docker-compose restart
```

### Пересборка

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 🧹 Очистка Docker

### Очистка всего (осторожно!)

```bash
# Остановка всех контейнеров
docker stop $(docker ps -aq)

# Удаление всех контейнеров
docker rm $(docker ps -aq)

# Удаление всех образов
docker rmi $(docker images -q) -f

# Очистка volumes и сетей
docker system prune -a --volumes
```

### Очистка только этого проекта

```bash
# Остановка и удаление
docker-compose down -v --rmi all

# Очистка build cache
docker builder prune -af
```

---

## 📦 Backup и восстановление

### Создание backup

```bash
# Создание backup (вручную)
tar -czf backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml logs/

# Или используйте скрипт обновления (делает автоматически)
./update.sh
```

### Восстановление из backup

```bash
# Распаковка
tar -xzf backups/backup_YYYYMMDD_HHMMSS.tar.gz

# Перезапуск
docker-compose up -d
```

---

## 🔧 Troubleshooting команды

### Контейнер не запускается

```bash
# Проверка логов
docker-compose logs app

# Проверка образа
docker images | grep social_post

# Пересборка
./docker-rebuild.sh
```

### Порт занят

```bash
# Найти что использует порт 8082
sudo lsof -i :8082
# или
sudo netstat -tlnp | grep 8082

# Убить процесс
sudo kill -9 <PID>
```

### Недостаточно места

```bash
# Проверка места
df -h

# Очистка Docker
docker system prune -a --volumes

# Очистка старых логов
find logs/ -name "*.log" -mtime +7 -delete
```

---

## 🚀 Быстрые команды

### Полный перезапуск за 10 секунд

```bash
docker-compose restart && docker-compose logs -f
```

### Применить изменения в коде

```bash
docker-compose up -d --build
```

### Проверка что всё работает

```bash
docker-compose ps && \
curl -s http://localhost:8082/api/health | jq && \
docker-compose logs --tail=20
```

### Обновление с GitHub

```bash
git pull && ./update.sh
```

---

## 📝 Полезные алиасы

Добавьте в `~/.bashrc` или `~/.zshrc`:

```bash
# Алиасы для Social Post Generator
alias spg-start='cd /opt/social_post_generator && docker-compose up -d'
alias spg-stop='cd /opt/social_post_generator && docker-compose down'
alias spg-restart='cd /opt/social_post_generator && docker-compose restart'
alias spg-logs='cd /opt/social_post_generator && docker-compose logs -f'
alias spg-update='cd /opt/social_post_generator && ./update.sh'
alias spg-rebuild='cd /opt/social_post_generator && ./docker-rebuild.sh'
alias spg-health='curl http://localhost:8082/api/health'
```

Применить:
```bash
source ~/.bashrc
```

Использование:
```bash
spg-update   # Обновление
spg-logs     # Просмотр логов
spg-health   # Проверка здоровья
```

---

## 🎯 Итоговая рекомендация

### Для продакшн сервера:

**Обычный день:**
```bash
./update.sh  # Умное обновление
```

**Серьезное обновление:**
```bash
./update-smart.sh  # С автооткатом
```

**Проблемы:**
```bash
./docker-rebuild.sh  # Полная очистка
```

---

**Копируйте команды прямо из этого файла! 📋**

