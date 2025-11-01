"""
Модуль настройки логирования приложения.

Предоставляет централизованное многоуровневое логирование
с поддержкой ротации файлов и детальных форматов.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from functools import wraps
import time
import traceback

from config import settings


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветным выводом для консоли."""

    # ANSI коды цветов
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def format(self, record):
        """Форматирование с добавлением цвета."""
        # Добавляем цвет к уровню логирования
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        
        # Форматируем как обычно
        return super().format(record)


class AppLogger:
    """Класс для управления логированием приложения."""

    def __init__(self):
        """Инициализация логгера."""
        self.log_dir = Path(settings.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Основной логгер приложения
        self.logger = logging.getLogger("social_post_generator")
        self.logger.setLevel(getattr(logging, settings.log_level))
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Настраиваем обработчики
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_error_handler()
        
        # Отключаем propagation чтобы избежать дублирования
        self.logger.propagate = False

    def _setup_console_handler(self):
        """Настройка вывода в консоль."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
        
        # Формат с цветами
        console_format = ColoredFormatter(
            fmt='%(levelname)s | %(asctime)s | %(name)s | %(message)s',
            datefmt=settings.log_date_format
        )
        console_handler.setFormatter(console_format)
        
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self):
        """Настройка записи в основной лог-файл."""
        log_file = self.log_dir / "app.log"
        
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Детальный формат для файла
        file_format = logging.Formatter(
            fmt='%(levelname)-8s | %(asctime)s | %(name)s | '
                '%(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt=settings.log_date_format
        )
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(file_handler)

    def _setup_error_handler(self):
        """Настройка отдельного файла для ошибок."""
        error_file = self.log_dir / "error.log"
        
        error_handler = RotatingFileHandler(
            filename=error_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Максимально детальный формат для ошибок
        error_format = logging.Formatter(
            fmt='%(levelname)-8s | %(asctime)s | %(name)s\n'
                'File: %(pathname)s:%(lineno)d\n'
                'Function: %(funcName)s()\n'
                'Message: %(message)s\n'
                '---',
            datefmt=settings.log_date_format
        )
        error_handler.setFormatter(error_format)
        
        self.logger.addHandler(error_handler)

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Получить логгер.
        
        Args:
            name: Имя логгера (опционально)
            
        Returns:
            logging.Logger: Настроенный логгер
        """
        if name:
            return self.logger.getChild(name)
        return self.logger


# Глобальный экземпляр логгера
app_logger = AppLogger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Получить логгер для модуля.
    
    Args:
        name: Имя модуля
        
    Returns:
        logging.Logger: Настроенный логгер
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Сообщение")
    """
    return app_logger.get_logger(name)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Декоратор для логирования времени выполнения функции.
    
    Args:
        logger: Логгер для использования (опционально)
        
    Example:
        >>> @log_execution_time()
        ... def slow_function():
        ...     time.sleep(1)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            start_time = time.time()
            
            _logger.debug(
                f"🚀 Начало выполнения {func.__name__}() "
                f"с args={args}, kwargs={kwargs}"
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                _logger.debug(
                    f"✅ Завершено {func.__name__}() "
                    f"за {execution_time:.3f} сек"
                )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                _logger.error(
                    f"❌ Ошибка в {func.__name__}() "
                    f"после {execution_time:.3f} сек: {e}"
                )
                raise
        
        return wrapper
    return decorator


def log_exception(logger: Optional[logging.Logger] = None):
    """
    Декоратор для логирования исключений с traceback.
    
    Args:
        logger: Логгер для использования (опционально)
        
    Example:
        >>> @log_exception()
        ... def risky_function():
        ...     raise ValueError("Ошибка!")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _logger.error(
                    f"❌ Исключение в {func.__name__}():\n"
                    f"Тип: {type(e).__name__}\n"
                    f"Сообщение: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                raise
        
        return wrapper
    return decorator


class LogContext:
    """Контекстный менеджер для логирования блока кода."""

    def __init__(
        self,
        description: str,
        logger: Optional[logging.Logger] = None,
        level: int = logging.INFO
    ):
        """
        Инициализация контекста.
        
        Args:
            description: Описание блока кода
            logger: Логгер (опционально)
            level: Уровень логирования
        """
        self.description = description
        self.logger = logger or get_logger()
        self.level = level
        self.start_time = None

    def __enter__(self):
        """Вход в контекст."""
        self.start_time = time.time()
        self.logger.log(self.level, f"▶️ Начало: {self.description}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста."""
        execution_time = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.log(
                self.level,
                f"✅ Завершено: {self.description} "
                f"за {execution_time:.3f} сек"
            )
        else:
            self.logger.error(
                f"❌ Ошибка: {self.description} "
                f"после {execution_time:.3f} сек: {exc_val}"
            )
        
        # Не подавляем исключение
        return False


# Инициализируем логирование при импорте
logger = get_logger(__name__)
logger.info("🎯 Система логирования инициализирована")
logger.debug(f"📝 Уровень логирования: {settings.log_level}")
logger.debug(f"📁 Директория логов: {settings.log_dir}")


if __name__ == "__main__":
    # Тест логирования
    test_logger = get_logger("test")
    
    test_logger.debug("🔍 Отладочное сообщение")
    test_logger.info("ℹ️ Информационное сообщение")
    test_logger.warning("⚠️ Предупреждение")
    test_logger.error("❌ Ошибка")
    test_logger.critical("🔥 Критическая ошибка")
    
    # Тест декоратора времени выполнения
    @log_execution_time()
    def test_function():
        time.sleep(0.1)
        return "результат"
    
    result = test_function()
    
    # Тест контекстного менеджера
    with LogContext("тестовая операция"):
        time.sleep(0.1)
        test_logger.info("Выполнение операции...")
    
    print("\n✅ Проверьте файлы логов в директории:", settings.log_dir)

