# Многоступенчатая сборка для оптимизации размера образа

# ============================================
# Стадия 1: Базовый образ с зависимостями
# ============================================
FROM python:3.10-slim as base

# Метаданные образа
LABEL maintainer="Social Post Generator"
LABEL description="AI-powered social media post generator"
LABEL version="1.1.0"

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    gcc \
#    g++ \
#    libxml2-dev \
#    libxslt-dev \
#    && rm -rf /var/lib/apt/lists/*

# ============================================
# Стадия 2: Установка Python зависимостей
# ============================================
FROM base as dependencies

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Стадия 3: Финальный образ
# ============================================
FROM python:3.10-slim as final

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8082

# Устанавливаем минимальные системные зависимости
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    libxml2 \
#    libxslt1.1 \
#    && rm -rf /var/lib/apt/lists/*

# Создаем непривилегированного пользователя и необходимые директории
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/static && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем установленные зависимости из стадии dependencies
COPY --from=dependencies /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Копируем файлы приложения
COPY --chown=appuser:appuser . .

# Переключаемся на непривилегированного пользователя
USER appuser

# Создаем директорию для логов от имени appuser
RUN mkdir -p /app/logs && chmod 755 /app/logs

# (healthcheck removed to avoid periodic ProxyAPI calls)

# Экспонируем порт
EXPOSE 8082

# Запускаем приложение
CMD ["python", "-u", "src/app.py"]

