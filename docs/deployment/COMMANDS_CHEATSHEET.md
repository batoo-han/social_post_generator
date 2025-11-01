# ⚡ Шпаргалка команд - Копируй и используй!

## 🔥 Решение проблемы "Permission denied" на сервере

### Полная очистка и пересборка (РЕКОМЕНДУЕТСЯ):

```bash
cd /opt/social_post_generator
chmod +x docker-rebuild.sh
./docker-rebuild.sh
```

### Или одной командой:

```bash
docker-compose down -v && \
docker rmi $(docker images -q social_post*) -f 2>/dev/null; \
docker image prune -af && \
docker builder prune -af && \
sudo rm -rf logs && \
mkdir -p logs && \
chmod 777 logs && \
docker-compose build --no-cache --pull && \
docker-compose up -d && \
sleep 10 && \
docker-compose logs --tail=100
```

---

## 🚀 Быстрая установка на новом сервере

```bash
# 1. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Клонирование проекта
sudo mkdir -p /opt/social_post_generator
sudo chown $USER:$USER /opt/social_post_generator
cd /opt/social_post_generator
git clone https://github.com/YOUR_REPO/social_post_generator.git .

# 4. Настройка
cp .env.example .env
nano .env  # Указать OPENAI_API_KEY

# 5. Запуск
chmod +x docker-rebuild.sh
./docker-rebuild.sh
```

---

## 🔄 Обновление приложения

### Автоматическое (умное):

```bash
cd /opt/social_post_generator
chmod +x update.sh
./update.sh
```

### С автооткатом (для продакшна):

```bash
chmod +x update-smart.sh
./update-smart.sh
```

### Ручное:

```bash
git pull
docker-compose down
docker-compose up -d --build
docker-compose logs -f
```

---

## 📊 Проверка и мониторинг

### Статус:

```bash
docker-compose ps
```

### Логи:

```bash
# В реальном времени
docker-compose logs -f

# Последние 100 строк
docker-compose logs --tail=100

# Только ошибки
docker-compose logs | grep ERROR
```

### Health check:

```bash
curl http://localhost:8082/api/health
```

### Тест API:

```bash
curl -X POST http://localhost:8082/api/generate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","style":"ироничный","max_length":800}'
```

---

## 🛠️ Управление контейнерами

### Запуск:

```bash
docker-compose up -d
```

### Остановка:

```bash
docker-compose down
```

### Перезапуск:

```bash
docker-compose restart
```

### Пересборка:

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 🧹 Очистка

### Очистка проекта:

```bash
docker-compose down -v --rmi all
docker builder prune -af
```

### Очистка всего Docker:

```bash
docker system prune -a --volumes
```

---

## 🌐 Nginx

### Быстрая настройка:

```bash
# Установка
sudo apt install nginx -y

# Создание конфига
sudo nano /etc/nginx/sites-available/social-post-generator
# Вставьте конфиг из docs/NGINX_SETUP.md

# Активация
sudo ln -s /etc/nginx/sites-available/social-post-generator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL (Let's Encrypt):

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 🐛 Troubleshooting

### Docker не запускается:

```bash
sudo systemctl start docker
sudo systemctl status docker
```

### Порт занят:

```bash
sudo lsof -i :8082
sudo kill -9 <PID>
```

### Недостаточно места:

```bash
df -h
docker system prune -a --volumes
```

---

## 💾 Backup

### Создание:

```bash
tar -czf backup_$(date +%Y%m%d).tar.gz .env logs/
```

### Восстановление:

```bash
tar -xzf backup_YYYYMMDD.tar.gz
docker-compose restart
```

---

## 🔧 Полезные алиасы

Добавьте в `~/.bashrc`:

```bash
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
spg-update   # Обновить
spg-logs     # Логи
spg-health   # Проверка
```

---

**Копируйте команды прямо отсюда! 📋**

**Полная документация:** [SERVER_COMMANDS.md](SERVER_COMMANDS.md)

