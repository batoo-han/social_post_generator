"""
Модуль конфигурации приложения.

Загружает настройки из переменных окружения (.env файл)
и предоставляет типобезопасный доступ к ним.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

# Загружаем переменные окружения из .env файла
load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения."""

    # ProxyAPI настройки
    # ProxyAPI.ru - сервис доступа к OpenAI в России без VPN
    openai_api_key: str = Field(..., description="API ключ ProxyAPI")
    openai_base_url: str = Field(
        default="https://api.proxyapi.ru/openai/v1",
        description="Базовый URL ProxyAPI для доступа к OpenAI"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="Модель OpenAI через ProxyAPI (gpt-4.1-mini, gpt-4o, gpt-5-mini)"
    )

    # Настройки приложения
    port: int = Field(default=8082, ge=1, le=65535, description="Порт приложения")
    host: str = Field(default="0.0.0.0", description="Хост приложения")
    debug: bool = Field(default=False, description="Режим отладки")
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования"
    )
    
    # CORS
    allowed_origins: str = Field(
        default="http://localhost:8082,http://127.0.0.1:8082",
        description="Разрешенные источники для CORS"
    )

    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=10,
        ge=1,
        description="Лимит запросов в минуту"
    )
    rate_limit_per_hour: int = Field(
        default=100,
        ge=1,
        description="Лимит запросов в час"
    )

    # Web scraping
    fetch_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Таймаут загрузки страницы в секундах"
    )
    max_page_size: int = Field(
        default=5242880,  # 5 MB
        ge=1024,
        description="Максимальный размер страницы в байтах"
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="User-Agent для запросов"
    )

    # Логирование
    log_dir: str = Field(default="logs", description="Директория для логов")
    log_max_size: int = Field(
        default=10485760,  # 10 MB
        description="Максимальный размер лог-файла"
    )
    log_backup_count: int = Field(
        default=5,
        description="Количество резервных копий логов"
    )
    log_date_format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="Формат даты в логах"
    )

    # Уведомления
    admin_email: str = Field(default="", description="Email администратора")
    smtp_host: str = Field(default="", description="SMTP хост")
    smtp_port: int = Field(default=587, description="SMTP порт")
    smtp_user: str = Field(default="", description="SMTP пользователь")
    smtp_password: str = Field(default="", description="SMTP пароль")
    smtp_use_tls: bool = Field(default=True, description="Использовать TLS")

    # Безопасность
    secret_key: str = Field(
        default="change_this_in_production",
        description="Секретный ключ"
    )

    # Ограничения контента
    max_post_length: int = Field(
        default=800,
        ge=100,
        description="Максимальная длина поста в символах"
    )
    min_text_length: int = Field(
        default=100,
        ge=50,
        description="Минимальное количество текста для генерации"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(
                f"Неверный уровень логирования: {v}. "
                f"Допустимые значения: {', '.join(valid_levels)}"
            )
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Валидация API ключа ProxyAPI."""
        if not v or v == "your_proxyapi_key_here" or v == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY не установлен! "
                "Пожалуйста, получите ключ ProxyAPI на https://proxyapi.ru/ "
                "и укажите его в .env файле."
            )
        return v

    def get_allowed_origins_list(self) -> List[str]:
        """Получить список разрешенных источников для CORS."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def ensure_log_directory(self) -> None:
        """Создать директорию для логов, если она не существует."""
        log_path = Path(self.log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

    class Config:
        """Конфигурация Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Глобальный экземпляр настроек
try:
    settings = Settings()
    # Создаем директорию для логов
    settings.ensure_log_directory()
except Exception as e:
    print(f"❌ Ошибка загрузки конфигурации: {e}")
    print("💡 Убедитесь, что файл .env существует и содержит все необходимые параметры.")
    print("📝 Скопируйте .env.example в .env и заполните значения.")
    raise


def get_settings() -> Settings:
    """
    Получить экземпляр настроек приложения.
    
    Returns:
        Settings: Настройки приложения
    """
    return settings


if __name__ == "__main__":
    # Тест конфигурации
    print("🔧 Проверка конфигурации...")
    print(f"✓ ProxyAPI Base URL: {settings.openai_base_url}")
    print(f"✓ Модель OpenAI: {settings.openai_model}")
    print(f"✓ Порт: {settings.port}")
    print(f"✓ Уровень логирования: {settings.log_level}")
    print(f"✓ Максимальная длина поста: {settings.max_post_length} символов")
    print(f"✓ CORS источники: {settings.get_allowed_origins_list()}")
    print("✅ Конфигурация загружена успешно!")
    print(f"📡 Используется ProxyAPI.ru для доступа к OpenAI")

