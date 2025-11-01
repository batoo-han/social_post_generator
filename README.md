# 🎯 Social Post Generator

**Мощный AI-генератор постов для социальных сетей**

Автоматически создавайте захватывающие посты на основе контента любых веб-страниц с использованием искусственного интеллекта GPT.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![ProxyAPI](https://img.shields.io/badge/ProxyAPI-supported-success.svg)

---

## ✨ Возможности

- 🤖 **6 стилей генерации** - от ироничного до профессионального
- 📏 **Настраиваемая длина** - от 400 до 4000 символов
- 🇷🇺 **Работает из России** - через ProxyAPI.ru без VPN
- 🎨 **Современный UI** - темная тема с анимациями
- 📡 **REST API** - для интеграций
- 🐳 **Docker ready** - легкое развертывание

---

## ⚡ Быстрый старт

### Локально (за 2 минуты):

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/YOUR_REPO/social_post_generator.git
cd social_post_generator

# 2. Настройте .env
cp .env.example .env
# Укажите ваш ProxyAPI ключ в .env

# 3. Запустите
./scripts/start/run.sh     # Linux/Mac
scripts\start\run.bat       # Windows
```

Откройте: http://localhost:8082

### На сервере (Docker):

```bash
# 1. Клонируйте и настройте
git clone https://github.com/batoo-han/social_post_generator.git
cd social_post_generator
cp .env.example .env
nano .env  # Укажите OPENAI_API_KEY

# 2. Запустите
chmod +x scripts/docker/docker-rebuild.sh
./scripts/docker/docker-rebuild.sh
```

---

## 📚 Документация

### 👤 Для пользователей

- **[docs/user/START_HERE.md](docs/user/START_HERE.md)** ⭐ Начните здесь!
- [docs/user/QUICKSTART.md](docs/user/QUICKSTART.md) - Быстрый старт
- [docs/user/USER_GUIDE.md](docs/user/USER_GUIDE.md) - Руководство пользователя
- [docs/user/PROXYAPI.md](docs/user/PROXYAPI.md) - Про ProxyAPI.ru
- [docs/user/FEATURES.md](docs/user/FEATURES.md) - Возможности

### 🛠️ Для DevOps

- **[docs/deployment/INSTALL_SERVER.md](docs/deployment/INSTALL_SERVER.md)** - Установка на VPS
- [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) - Полное руководство
- [docs/deployment/NGINX_SETUP.md](docs/deployment/NGINX_SETUP.md) - Настройка Nginx  
- [docs/deployment/UPDATE_GUIDE.md](docs/deployment/UPDATE_GUIDE.md) - Обновление
- [docs/deployment/SCRIPTS.md](docs/deployment/SCRIPTS.md) - Справка по скриптам
- [docs/deployment/SERVER_COMMANDS.md](docs/deployment/SERVER_COMMANDS.md) - Команды

### 💻 Для разработчиков

- [docs/developer/ARCHITECTURE.md](docs/developer/ARCHITECTURE.md) - Архитектура
- [docs/developer/API.md](docs/developer/API.md) - API документация
- [docs/developer/CONTRIBUTING.md](docs/developer/CONTRIBUTING.md) - Как внести вклад
- [docs/developer/CHANGELOG.md](docs/developer/CHANGELOG.md) - История изменений

---

## 📁 Структура проекта

```
social_post_generator/
├── src/                     # Исходный код приложения
│   ├── agent.py            # Агент генерации постов
│   ├── openai_module.py    # Интеграция с ProxyAPI
│   ├── app.py              # FastAPI сервер
│   ├── config.py           # Конфигурация
│   ├── logger.py           # Логирование
│   ├── exceptions.py       # Обработка ошибок
│   └── static/             # Frontend (HTML/CSS/JS)
├── scripts/                # Скрипты управления
│   ├── start/              # Запуск приложения
│   ├── update/             # Обновление
│   └── docker/             # Docker операции
├── docs/                   # Документация
│   ├── user/               # Для пользователей
│   ├── developer/          # Для разработчиков
│   └── deployment/         # Для DevOps
├── docker-compose.yml      # Docker Compose
├── Dockerfile              # Docker образ
├── requirements.txt        # Зависимости
├── .env.example            # Шаблон настроек
└── README.md               # Этот файл
```

---

## 🚀 Использование

### Запуск для разработки:

```bash
./scripts/start/run.sh          # Linux/Mac
scripts\start\run.bat            # Windows
```

### Обновление на сервере:

```bash
./scripts/update/update.sh       # Умное обновление
```

### Полная пересборка Docker:

```bash
./scripts/docker/docker-rebuild.sh
```

📖 Подробнее: [docs/deployment/SCRIPTS.md](docs/deployment/SCRIPTS.md)

---

## 🐳 Docker

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Логи
docker-compose logs -f

# Обновление
./scripts/update/update.sh
```

---

## 📡 API

- `POST /api/generate` - Генерация поста
- `GET /api/styles` - Список стилей
- `GET /api/health` - Health check
- `GET /docs` - Swagger UI

Подробнее: [docs/developer/API.md](docs/developer/API.md)

---

## ⚙️ Конфигурация

```ini
# .env файл
OPENAI_API_KEY=your_proxyapi_key    # Получить на https://proxyapi.ru/
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o
PORT=8082
```

---

## 🤝 Вклад в проект

Мы приветствуем вклад в проект!

- 📖 [docs/developer/CONTRIBUTING.md](docs/developer/CONTRIBUTING.md) - Руководство
- 🐛 [Создайте Issue](https://github.com/batoo-han/issues) - Баг или идея
- 🔧 Pull Request - С улучшениями

---

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

## 🙏 Благодарности

- [ProxyAPI.ru](https://proxyapi.ru/) - за доступ к OpenAI в России
- [OpenAI](https://openai.com) - за GPT модели
- [FastAPI](https://fastapi.tiangolo.com) - за отличный фреймворк

---

**Сделано с ❤️ и AI**

⭐ Поставьте звезду если проект понравился!
