# 🚀 Руководство по развертыванию

Подробная инструкция по развертыванию Social Post Generator на различных платформах.

---

## Содержание

1. [VPS Deployment](#vps-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Systemd Service](#systemd-service)
4. [Nginx Reverse Proxy](#nginx-reverse-proxy)
5. [SSL Certificate](#ssl-certificate)
6. [Мониторинг](#мониторинг)
7. [Backup](#backup)
8. [Обновления](#обновления)

---

## VPS Deployment

### Требования

**Минимальные:**
- OS: Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- RAM: 1 GB
- CPU: 1 core
- Disk: 10 GB
- Python: 3.10+
- Docker: 20.10+ (опционально)

**Рекомендуемые:**
- RAM: 2 GB
- CPU: 2 cores
- Disk: 20 GB
- SSD накопитель

### Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y \
    git \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nginx \
    certbot \
    python3-certbot-nginx

# Установка Docker (опционально)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Создание пользователя для приложения

```bash
# Создаем пользователя
sudo adduser --system --group --home /opt/social_post_generator appuser

# Переключаемся на пользователя
sudo su - appuser
```

### Клонирование проекта

```bash
# Клонируем репозиторий
cd /opt/social_post_generator
git clone <repository-url> .

# Проверяем структуру
ls -la
```

### Настройка окружения

```bash
# Создаем .env файл
cp .env.example .env

# Редактируем конфигурацию
nano .env

# Обязательно установить:
# - OPENAI_API_KEY
# - HOST=0.0.0.0
# - DEBUG=false
# - LOG_LEVEL=INFO
```

---

## Docker Deployment

### Метод 1: Docker Compose (Рекомендуется)

```bash
# Переход в директорию проекта
cd /opt/social_post_generator

# Создание .env
cp .env.example .env
nano .env

# Сборка и запуск
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f app

# Остановка
docker-compose down
```

### Метод 2: Docker напрямую

```bash
# Сборка образа
docker build -t social-post-generator:latest .

# Запуск контейнера
docker run -d \
  --name social_post_gen \
  --restart unless-stopped \
  -p 8082:8082 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  social-post-generator:latest

# Проверка
docker ps
docker logs -f social_post_gen
```

### Docker полезные команды

```bash
# Перезапуск
docker-compose restart app

# Пересборка после изменений
docker-compose up -d --build

# Просмотр использования ресурсов
docker stats

# Очистка неиспользуемых образов
docker system prune -a

# Backup volumes
docker run --rm -v social_post_generator_logs:/data -v $(pwd):/backup ubuntu tar czf /backup/logs-backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v social_post_generator_logs:/data -v $(pwd):/backup ubuntu tar xzf /backup/logs-backup.tar.gz -C /data
```

---

## Systemd Service

Для запуска приложения как системного сервиса без Docker:

### Создание service файла

```bash
sudo nano /etc/systemd/system/social-post-generator.service
```

**Содержимое:**

```ini
[Unit]
Description=Social Post Generator
After=network.target

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/social_post_generator
Environment="PATH=/opt/social_post_generator/.venv/bin"
ExecStart=/opt/social_post_generator/.venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=social-post-gen

# Ограничения безопасности
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/social_post_generator/logs

[Install]
WantedBy=multi-user.target
```

### Управление сервисом

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable social-post-generator

# Запуск
sudo systemctl start social-post-generator

# Статус
sudo systemctl status social-post-generator

# Логи
sudo journalctl -u social-post-generator -f

# Остановка
sudo systemctl stop social-post-generator

# Перезапуск
sudo systemctl restart social-post-generator
```

---

## Nginx Reverse Proxy

Nginx используется как reverse proxy для Docker контейнера, обеспечивая:
- SSL/TLS терминацию
- Rate limiting и защиту от DDoS
- Кэширование статических файлов
- Сжатие трафика (gzip)
- Load balancing (при масштабировании)
- Security headers

### Установка Nginx

```bash
# Обновление системы
sudo apt update

# Установка Nginx
sudo apt install nginx -y

# Включение автозапуска
sudo systemctl enable nginx

# Запуск Nginx
sudo systemctl start nginx

# Проверка статуса
sudo systemctl status nginx
```

### Базовая конфигурация (HTTP)

Создаем конфигурационный файл для приложения:

```bash
sudo nano /etc/nginx/sites-available/social-post-generator
```

**Содержимое файла:**

```nginx
# Upstream для Docker контейнера
upstream social_post_backend {
    server 127.0.0.1:8082 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    # Логирование
    access_log /var/log/nginx/social-post-generator-access.log;
    error_log /var/log/nginx/social-post-generator-error.log warn;

    # Максимальный размер тела запроса
    client_max_body_size 10M;
    client_body_timeout 60s;

    # Таймауты
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Proxy к Docker контейнеру
    location / {
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        # Заголовки для проксирования
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support (если будет нужен)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Отключаем буферизацию для streaming
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # API endpoints с особыми настройками
    location /api/ {
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличиваем таймаут для генерации (может занять время)
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
        
        # Не кэшируем API запросы
        proxy_cache_bypass 1;
        proxy_no_cache 1;
    }

    # Статические файлы (прямая отдача из контейнера)
    location /static/ {
        proxy_pass http://social_post_backend;
        
        # Кэширование статики
        proxy_cache_valid 200 30d;
        proxy_cache_valid 404 1h;
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # Gzip сжатие
        gzip on;
        gzip_vary on;
        gzip_types text/css text/javascript application/javascript;
    }

    # Health check endpoint
    location /api/health {
        proxy_pass http://social_post_backend;
        access_log off;  # Не логируем health checks
    }

    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    # Robots.txt
    location = /robots.txt {
        access_log off;
        log_not_found off;
    }
}
```

**Активация конфигурации:**

```bash
# Проверка синтаксиса конфигурации
sudo nginx -t

# Если все ОК - создаем символическую ссылку
sudo ln -s /etc/nginx/sites-available/social-post-generator /etc/nginx/sites-enabled/

# Удаляем дефолтную конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Перезагрузка Nginx
sudo systemctl reload nginx

# Или полный рестарт
sudo systemctl restart nginx
```

### Продвинутая конфигурация с оптимизациями

```bash
sudo nano /etc/nginx/sites-available/social-post-generator
```

```nginx
# Кэш для статических файлов
proxy_cache_path /var/cache/nginx/social-post levels=1:2 keys_zone=static_cache:10m max_size=100m inactive=60m use_temp_path=off;

# Rate limiting зоны
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=50r/m;

# Upstream с балансировкой (для масштабирования)
upstream social_post_backend {
    least_conn;  # Алгоритм балансировки
    server 127.0.0.1:8082 max_fails=3 fail_timeout=30s;
    # При масштабировании можно добавить еще контейнеры:
    # server 127.0.0.1:8083 max_fails=3 fail_timeout=30s;
    keepalive 64;
}

server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    # Логирование с расширенным форматом
    log_format detailed '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'rt=$request_time uct="$upstream_connect_time" '
                       'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/social-post-generator-access.log detailed;
    error_log /var/log/nginx/social-post-generator-error.log warn;

    # Защита от медленных клиентов
    client_body_timeout 10s;
    client_header_timeout 10s;
    client_max_body_size 10M;

    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Rate limiting для общих запросов
    limit_req zone=general_limit burst=100 nodelay;

    # Главная страница и статика
    location / {
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # Таймауты
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # API с усиленным rate limiting
    location /api/generate {
        limit_req zone=api_limit burst=5 nodelay;
        limit_req_status 429;
        
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличенные таймауты для генерации
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Не кэшируем
        proxy_cache_bypass 1;
        proxy_no_cache 1;
    }

    # Другие API endpoints
    location ~ ^/api/(styles|health) {
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Health check можно кэшировать на короткое время
        proxy_cache static_cache;
        proxy_cache_valid 200 10s;
    }

    # Статические файлы с агрессивным кэшированием
    location /static/ {
        proxy_pass http://social_post_backend;
        
        proxy_cache static_cache;
        proxy_cache_valid 200 30d;
        proxy_cache_valid 404 1h;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_lock on;
        
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Cache-Status $upstream_cache_status;
    }

    # Swagger документация
    location /docs {
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Кэшируем на час
        proxy_cache static_cache;
        proxy_cache_valid 200 1h;
    }

    # Health check без логирования
    location = /api/health {
        proxy_pass http://social_post_backend;
        access_log off;
        
        # Быстрый таймаут
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }

    # Служебные файлы
    location = /favicon.ico {
        access_log off;
        log_not_found off;
        expires 7d;
    }

    location = /robots.txt {
        access_log off;
        log_not_found off;
    }
}
```

### Конфигурация для Docker Compose с несколькими контейнерами

Если вы масштабируете приложение и запускаете несколько контейнеров:

```nginx
upstream social_post_backend {
    least_conn;
    
    # Несколько экземпляров контейнера на разных портах
    server 127.0.0.1:8082 max_fails=3 fail_timeout=30s weight=1;
    server 127.0.0.1:8083 max_fails=3 fail_timeout=30s weight=1;
    server 127.0.0.1:8084 max_fails=3 fail_timeout=30s weight=1;
    
    keepalive 64;
}
```

**docker-compose.yml для масштабирования:**

```yaml
version: '3.8'

services:
  app1:
    build: .
    ports:
      - "8082:8082"
    env_file: .env
    
  app2:
    build: .
    ports:
      - "8083:8082"
    env_file: .env
    
  app3:
    build: .
    ports:
      - "8084:8082"
    env_file: .env
```

### Тестирование конфигурации

```bash
# Проверка синтаксиса
sudo nginx -t

# Проверка что порты слушаются
sudo netstat -tlnp | grep nginx

# Проверка upstream
curl -I http://localhost

# Проверка через доменное имя
curl -I http://your-domain.com

# Проверка API
curl http://your-domain.com/api/health

# Проверка rate limiting
for i in {1..15}; do curl http://your-domain.com/api/generate; done
```

### Мониторинг Nginx

**Включение статуса Nginx:**

```nginx
# Добавить в /etc/nginx/sites-available/social-post-generator
server {
    listen 127.0.0.1:8080;
    
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

**Проверка:**
```bash
curl http://127.0.0.1:8080/nginx_status
```

### Логи и отладка

```bash
# Просмотр access логов в реальном времени
sudo tail -f /var/log/nginx/social-post-generator-access.log

# Просмотр error логов
sudo tail -f /var/log/nginx/social-post-generator-error.log

# Фильтрация ошибок
sudo grep "error" /var/log/nginx/social-post-generator-error.log

# Просмотр последних запросов к API
sudo grep "/api/generate" /var/log/nginx/social-post-generator-access.log | tail -20

# Статистика по кодам ответа
sudo awk '{print $9}' /var/log/nginx/social-post-generator-access.log | sort | uniq -c | sort -rn

# Топ IP адресов по количеству запросов
sudo awk '{print $1}' /var/log/nginx/social-post-generator-access.log | sort | uniq -c | sort -rn | head -10
```

### Ротация логов

Создаем конфигурацию logrotate:

```bash
sudo nano /etc/logrotate.d/social-post-generator
```

```
/var/log/nginx/social-post-generator-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
```

### Troubleshooting Nginx

**Проблема: 502 Bad Gateway**

```bash
# Проверьте что контейнер запущен
docker ps

# Проверьте что порт 8082 слушается
sudo netstat -tlnp | grep 8082

# Проверьте логи контейнера
docker logs social_post_generator

# Проверьте логи nginx
sudo tail -f /var/log/nginx/social-post-generator-error.log
```

**Проблема: 504 Gateway Timeout**

```bash
# Увеличьте таймауты в nginx конфигурации
proxy_read_timeout 180s;
proxy_send_timeout 180s;
proxy_connect_timeout 180s;

# Перезагрузите nginx
sudo systemctl reload nginx
```

**Проблема: Rate limiting слишком строгий**

```bash
# Увеличьте лимиты
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/m;  # Было 10r/m

# Или увеличьте burst
limit_req zone=api_limit burst=20 nodelay;  # Было 5
```

### Оптимизация производительности

**Настройки nginx.conf:**

```bash
sudo nano /etc/nginx/nginx.conf
```

```nginx
user www-data;
worker_processes auto;
worker_rlimit_nofile 65535;
pid /run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Базовые настройки
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    types_hash_max_size 2048;
    server_tokens off;
    
    # Буферы
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
    
    # Таймауты
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;
    
    # Остальные настройки...
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Логирование
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # Включаем конфигурации сайтов
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### Проверка производительности

```bash
# Benchmarking с Apache Bench
apt install apache2-utils
ab -n 1000 -c 10 http://your-domain.com/

# Или с wrk
apt install wrk
wrk -t4 -c100 -d30s http://your-domain.com/
```

---

## SSL Certificate

### Получение сертификата Let's Encrypt

```bash
# Автоматическая настройка SSL
sudo certbot --nginx -d your-domain.com

# Или только получение сертификата
sudo certbot certonly --nginx -d your-domain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

### Обновленная конфигурация Nginx с SSL

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/your-domain.com/chain.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Остальная конфигурация...
    location / {
        proxy_pass http://127.0.0.1:8082;
        # ... proxy настройки ...
    }
}
```

---

## Мониторинг

### Health Check скрипт

```bash
#!/bin/bash
# /opt/social_post_generator/health_check.sh

HEALTH_URL="http://localhost:8082/api/health"
MAX_RETRIES=3

for i in $(seq 1 $MAX_RETRIES); do
    response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
    
    if [ $response -eq 200 ]; then
        echo "OK: Service is healthy"
        exit 0
    fi
    
    sleep 5
done

echo "ERROR: Service is down"
exit 1
```

**Добавление в crontab:**

```bash
# Проверка каждые 5 минут
*/5 * * * * /opt/social_post_generator/health_check.sh || /usr/bin/systemctl restart social-post-generator
```

### Prometheus мониторинг (опционально)

Можно добавить экспорт метрик для Prometheus:

```python
# В app.py добавить
from prometheus_client import Counter, Histogram, generate_latest

# Метрики
request_count = Counter('requests_total', 'Total requests')
generation_duration = Histogram('generation_duration_seconds', 'Generation duration')

# Endpoint
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Backup

### Скрипт автоматического бэкапа

```bash
#!/bin/bash
# /opt/social_post_generator/backup.sh

BACKUP_DIR="/backup/social-post-generator"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/social_post_generator"

# Создаем директорию бэкапов
mkdir -p $BACKUP_DIR

# Бэкап конфигурации
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    $APP_DIR/.env \
    $APP_DIR/docker-compose.yml

# Бэкап логов
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz \
    $APP_DIR/logs/

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Автоматизация через cron:**

```bash
# Ежедневный бэкап в 3:00
0 3 * * * /opt/social_post_generator/backup.sh
```

---

## Обновления

### Автоматическое обновление (рекомендуется)

**Умный скрипт обновления:**

```bash
cd /opt/social_post_generator

# Автоматическое обновление
./update.sh

# Или продвинутая версия с откатом
./update-smart.sh
```

Скрипт автоматически:
- ✅ Создает backup
- ✅ Определяет тип обновления (rebuild/restart)
- ✅ Выполняет минимально необходимые действия
- ✅ Проверяет работоспособность
- ✅ Откатывается при ошибках (smart версия)

📖 **Подробная документация:** [docs/UPDATE_GUIDE.md](UPDATE_GUIDE.md)

### Ручное обновление

**С Docker:**

```bash
cd /opt/social_post_generator

# Получение изменений
git pull

# Остановка контейнера
docker-compose down

# Пересборка и запуск
docker-compose up -d --build

# Проверка
docker-compose logs -f app
```

**Без Docker (systemd):**

```bash
cd /opt/social_post_generator

# Остановка сервиса
sudo systemctl stop social-post-generator

# Получение изменений
git pull

# Обновление зависимостей
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Запуск сервиса
sudo systemctl start social-post-generator

# Проверка
sudo systemctl status social-post-generator
```

### Откат к предыдущей версии

```bash
# Просмотр коммитов
git log --oneline -10

# Откат к конкретному коммиту
git checkout <commit-hash>

# Перезапуск
docker-compose restart  # или systemctl restart
```

---

## Безопасность

### Firewall настройки

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Проверка
sudo ufw status
```

### Ограничение доступа к логам

```bash
# Только владелец может читать
chmod 600 /opt/social_post_generator/.env
chmod 755 /opt/social_post_generator/logs
chmod 644 /opt/social_post_generator/logs/*.log
```

### Fail2ban для защиты от брутфорса

```bash
# Установка
sudo apt install fail2ban -y

# Создание правила
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/social-post-generator-error.log
maxretry = 5
findtime = 60
bantime = 600
```

---

## Troubleshooting в продакшне

### Проверка портов

```bash
# Проверка что порт 8082 слушается
sudo netstat -tlnp | grep 8082
# или
sudo lsof -i :8082
```

### Проверка Docker

```bash
# Статус контейнера
docker ps -a

# Логи
docker logs social_post_generator

# Перезапуск
docker restart social_post_generator

# Проверка ресурсов
docker stats
```

### Проверка Nginx

```bash
# Тест конфигурации
sudo nginx -t

# Перезагрузка
sudo systemctl reload nginx

# Логи
sudo tail -f /var/log/nginx/social-post-generator-error.log
```

### Проверка приложения

```bash
# Health check
curl http://localhost:8082/api/health

# API test
curl -X POST http://localhost:8082/api/generate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","style":"ироничный"}'
```

---

**Успешного развертывания! 🚀**

