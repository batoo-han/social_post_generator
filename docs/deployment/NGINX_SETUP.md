# 🚀 Быстрая настройка Nginx для Social Post Generator

## Краткая инструкция (5 минут)

### Шаг 1: Установка Nginx

```bash
sudo apt update
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Шаг 2: Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/social-post-generator
```

**Вставьте эту базовую конфигурацию:**

```nginx
upstream social_post_backend {
    server 127.0.0.1:8082 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;  # ИЗМЕНИТЕ НА ВАШ ДОМЕН

    access_log /var/log/nginx/social-post-generator-access.log;
    error_log /var/log/nginx/social-post-generator-error.log;

    client_max_body_size 10M;

    location / {
        proxy_pass http://social_post_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /api/generate {
        proxy_pass http://social_post_backend;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        proxy_read_timeout 120s;
    }
}
```

### Шаг 3: Активация

```bash
# Проверка конфигурации
sudo nginx -t

# Создание симлинка
sudo ln -s /etc/nginx/sites-available/social-post-generator /etc/nginx/sites-enabled/

# Удаление дефолтной конфигурации
sudo rm /etc/nginx/sites-enabled/default

# Перезагрузка
sudo systemctl reload nginx
```

### Шаг 4: Проверка

```bash
# Проверка что nginx работает
sudo systemctl status nginx

# Проверка что приложение доступно
curl http://your-domain.com/api/health
```

## 🔒 Добавление SSL (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx -y

# Автоматическая настройка SSL
sudo certbot --nginx -d your-domain.com

# Тест автообновления
sudo certbot renew --dry-run
```

Готово! Ваше приложение доступно на `https://your-domain.com`

---

## 📊 Полезные команды

```bash
# Проверка конфигурации
sudo nginx -t

# Перезагрузка nginx
sudo systemctl reload nginx

# Просмотр логов
sudo tail -f /var/log/nginx/social-post-generator-access.log
sudo tail -f /var/log/nginx/social-post-generator-error.log

# Статус nginx
sudo systemctl status nginx

# Перезапуск nginx
sudo systemctl restart nginx
```

---

## 🐛 Решение проблем

### Ошибка 502 Bad Gateway
```bash
# Проверьте что контейнер работает
docker ps
docker logs social_post_generator

# Проверьте что порт 8082 открыт
sudo netstat -tlnp | grep 8082
```

### Ошибка 504 Gateway Timeout
Увеличьте таймауты в nginx конфигурации:
```nginx
proxy_read_timeout 180s;
proxy_connect_timeout 180s;
```

---

## 📚 Дополнительная документация

Полная документация по настройке Nginx: [DEPLOYMENT.md](DEPLOYMENT.md#nginx-reverse-proxy)

Включает:
- ✅ Продвинутую конфигурацию с кэшированием
- ✅ Rate limiting
- ✅ Load balancing
- ✅ Security headers
- ✅ Мониторинг и логи
- ✅ Оптимизацию производительности

---

**Быстрая настройка завершена! 🎉**

