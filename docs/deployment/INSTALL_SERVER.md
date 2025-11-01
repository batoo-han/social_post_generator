# 🚀 Установка на сервер за 5 минут

## Быстрая установка на VPS/Dedicated сервер

### Предварительные требования

- Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- Docker и Docker Compose
- Git
- Доступ к ProxyAPI.ru

---

## ⚡ Установка

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Установка Git
sudo apt install git -y

# Перелогиньтесь для применения прав docker
exit
# ssh обратно на сервер
```

### Шаг 2: Клонирование проекта

```bash
# Создание директории
sudo mkdir -p /opt/social_post_generator
sudo chown $USER:$USER /opt/social_post_generator
cd /opt/social_post_generator

# Клонирование (замените YOUR_REPO)
git clone https://github.com/YOUR_REPO/social_post_generator.git .
```

### Шаг 3: Настройка

```bash
# Создание .env
cp .env.example .env

# Редактирование .env
nano .env
```

**Обязательно установите:**
```ini
OPENAI_API_KEY=ваш_ключ_с_proxyapi_ru
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o
HOST=0.0.0.0
DEBUG=false
LOG_LEVEL=INFO
```

**Сохраните:** Ctrl+O, Enter, Ctrl+X

### Шаг 4: Создание директории для логов

```bash
# Создание с правильными правами
mkdir -p logs
chmod 777 logs
```

### Шаг 5: Запуск

```bash
# Сборка и запуск
docker-compose build
docker-compose up -d

# Проверка
docker-compose ps
```

### Шаг 6: Проверка работоспособности

```bash
# Ждем 30 секунд
sleep 30

# Health check
curl http://localhost:8082/api/health

# Логи
docker-compose logs --tail=50 app
```

---

## 🌐 Настройка Nginx (опционально, но рекомендуется)

```bash
# Установка Nginx
sudo apt install nginx -y

# Создание конфигурации
sudo nano /etc/nginx/sites-available/social-post-generator
```

**Вставьте конфигурацию из:** [docs/NGINX_SETUP.md](docs/NGINX_SETUP.md)

```bash
# Активация
sudo ln -s /etc/nginx/sites-available/social-post-generator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 SSL сертификат (опционально)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификата (замените your-domain.com)
sudo certbot --nginx -d your-domain.com

# Автообновление
sudo certbot renew --dry-run
```

---

## ✅ Финальная проверка

Откройте в браузере:

- **Без Nginx:** http://ваш-сервер-ip:8082
- **С Nginx:** http://ваш-домен.com
- **С SSL:** https://ваш-домен.com

Должен открыться интерфейс генератора постов!

---

## 🔄 Обновление в будущем

```bash
cd /opt/social_post_generator
./update.sh
```

Всё! Скрипт сделает всё автоматически.

---

## 🐛 Если что-то пошло не так

### Проблема: Permission denied с logs

```bash
./docker-rebuild.sh
```

### Проблема: Порт 8082 занят

```bash
# Измените порт в .env
PORT=8083

# И в docker-compose.yml
ports:
  - "8083:8083"
```

### Проблема: Docker не найден

```bash
# Проверка
docker --version
docker-compose --version

# Если не установлены - повторите Шаг 1
```

### Полные логи

```bash
docker-compose logs app > full_logs.txt
cat full_logs.txt
```

---

## 📞 Поддержка

- 📖 [Полная документация](README.md)
- 🔧 [Развертывание](docs/DEPLOYMENT.md)
- 🐛 [Troubleshooting](README.md#-troubleshooting)
- ⚡ [Команды для сервера](SERVER_COMMANDS.md)

---

**Установка завершена! Приятного использования! 🎉**

