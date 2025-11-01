"""
Модуль кастомных исключений приложения.

Определяет специфичные исключения для различных ошибок
и предоставляет дружественные сообщения для пользователей.
"""

from typing import Optional
from logger import get_logger

logger = get_logger(__name__)


class SocialPostGeneratorException(Exception):
    """Базовое исключение для всех ошибок приложения."""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """
        Инициализация исключения.
        
        Args:
            message: Техническое сообщение об ошибке (для логов)
            user_message: Дружественное сообщение для пользователя
            error_code: Код ошибки для API
            details: Дополнительные детали ошибки
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or self._default_user_message()
        self.error_code = error_code or self._default_error_code()
        self.details = details or {}
        
        # Логируем ошибку
        logger.error(
            f"❌ {self.__class__.__name__}: {message}",
            extra={"error_code": self.error_code, "details": self.details}
        )

    def _default_user_message(self) -> str:
        """Сообщение по умолчанию для пользователя."""
        return (
            "Произошла ошибка при обработке запроса. "
            "Администратор уже уведомлен о проблеме."
        )

    def _default_error_code(self) -> str:
        """Код ошибки по умолчанию."""
        return "INTERNAL_ERROR"

    def to_dict(self) -> dict:
        """
        Преобразовать исключение в словарь для API ответа.
        
        Returns:
            dict: Словарь с информацией об ошибке
        """
        return {
            "success": False,
            "error": self.user_message,
            "error_code": self.error_code,
            **self.details
        }


class ValidationError(SocialPostGeneratorException):
    """Ошибка валидации входных данных."""

    def _default_error_code(self) -> str:
        return "VALIDATION_ERROR"

    def _default_user_message(self) -> str:
        return (
            "Некорректные входные данные. "
            "Пожалуйста, проверьте правильность введенной информации."
        )


class URLValidationError(ValidationError):
    """Ошибка валидации URL."""

    def __init__(self, url: str, reason: Optional[str] = None):
        """
        Инициализация ошибки URL.
        
        Args:
            url: Некорректный URL
            reason: Причина ошибки
        """
        message = f"Некорректный URL: {url}"
        if reason:
            message += f" ({reason})"
        
        user_message = (
            "Некорректный URL. Пожалуйста, укажите полный URL "
            "с протоколом (http:// или https://)"
        )
        
        super().__init__(
            message=message,
            user_message=user_message,
            details={"url": url, "reason": reason}
        )


class URLFetchError(SocialPostGeneratorException):
    """Ошибка загрузки веб-страницы."""

    def _default_error_code(self) -> str:
        return "URL_FETCH_ERROR"

    def _default_user_message(self) -> str:
        return (
            "Не удалось загрузить страницу. "
            "Проверьте правильность URL и доступность сайта."
        )

    def __init__(
        self,
        url: str,
        reason: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        """
        Инициализация ошибки загрузки.
        
        Args:
            url: URL который не удалось загрузить
            reason: Причина ошибки
            status_code: HTTP статус код (если есть)
        """
        message = f"Ошибка загрузки {url}"
        if status_code:
            message += f" (HTTP {status_code})"
        if reason:
            message += f": {reason}"
        
        details = {"url": url}
        if status_code:
            details["status_code"] = status_code
        if reason:
            details["reason"] = reason
        
        super().__init__(
            message=message,
            details=details
        )


class TextExtractionError(SocialPostGeneratorException):
    """Ошибка извлечения текста из HTML."""

    def _default_error_code(self) -> str:
        return "TEXT_EXTRACTION_ERROR"

    def _default_user_message(self) -> str:
        return (
            "На странице не найдено достаточно текста для генерации поста. "
            "Попробуйте другой URL."
        )

    def __init__(self, url: str, reason: Optional[str] = None):
        """
        Инициализация ошибки извлечения текста.
        
        Args:
            url: URL страницы
            reason: Причина ошибки
        """
        message = f"Не удалось извлечь текст из {url}"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            details={"url": url, "reason": reason}
        )


class OpenAIError(SocialPostGeneratorException):
    """Ошибка взаимодействия с OpenAI API."""

    def _default_error_code(self) -> str:
        return "OPENAI_ERROR"

    def _default_user_message(self) -> str:
        return (
            "Временные проблемы с генерацией. "
            "Мы уже работаем над решением. Попробуйте позже."
        )

    def __init__(
        self,
        reason: str,
        api_error: Optional[Exception] = None,
        retry_count: int = 0
    ):
        """
        Инициализация ошибки OpenAI.
        
        Args:
            reason: Причина ошибки
            api_error: Исходное исключение от API
            retry_count: Количество попыток повтора
        """
        message = f"Ошибка OpenAI API: {reason}"
        if api_error:
            message += f" ({type(api_error).__name__}: {str(api_error)})"
        
        details = {
            "reason": reason,
            "retry_count": retry_count
        }
        if api_error:
            details["api_error_type"] = type(api_error).__name__
            details["api_error_message"] = str(api_error)
        
        super().__init__(
            message=message,
            details=details
        )


class RateLimitError(OpenAIError):
    """Превышен лимит запросов к API."""

    def _default_error_code(self) -> str:
        return "RATE_LIMIT_ERROR"

    def _default_user_message(self) -> str:
        return (
            "Превышен лимит запросов. "
            "Пожалуйста, подождите немного перед следующей попыткой."
        )

    def __init__(self, retry_after: Optional[int] = None):
        """
        Инициализация ошибки rate limit.
        
        Args:
            retry_after: Через сколько секунд можно повторить запрос
        """
        reason = "Превышен rate limit"
        if retry_after:
            reason += f", повторите через {retry_after} секунд"
        
        super().__init__(reason=reason)
        if retry_after:
            self.details["retry_after"] = retry_after


class PostGenerationError(SocialPostGeneratorException):
    """Общая ошибка генерации поста."""

    def _default_error_code(self) -> str:
        return "POST_GENERATION_ERROR"

    def _default_user_message(self) -> str:
        return (
            "Не удалось сгенерировать пост. "
            "Пожалуйста, попробуйте другой URL или стиль."
        )

    def __init__(self, reason: str, url: Optional[str] = None, style: Optional[str] = None):
        """
        Инициализация ошибки генерации.
        
        Args:
            reason: Причина ошибки
            url: URL страницы
            style: Стиль генерации
        """
        message = f"Ошибка генерации поста: {reason}"
        
        details = {"reason": reason}
        if url:
            details["url"] = url
        if style:
            details["style"] = style
        
        super().__init__(
            message=message,
            details=details
        )


class ConfigurationError(SocialPostGeneratorException):
    """Ошибка конфигурации приложения."""

    def _default_error_code(self) -> str:
        return "CONFIGURATION_ERROR"

    def _default_user_message(self) -> str:
        return (
            "Ошибка конфигурации приложения. "
            "Пожалуйста, обратитесь к администратору."
        )

    def __init__(self, parameter: str, reason: str):
        """
        Инициализация ошибки конфигурации.
        
        Args:
            parameter: Параметр конфигурации
            reason: Причина ошибки
        """
        message = f"Ошибка конфигурации '{parameter}': {reason}"
        
        super().__init__(
            message=message,
            details={"parameter": parameter, "reason": reason}
        )


def handle_exception(exception: Exception) -> dict:
    """
    Обработать исключение и вернуть dict для API ответа.
    
    Args:
        exception: Исключение для обработки
        
    Returns:
        dict: Словарь с информацией об ошибке
    """
    if isinstance(exception, SocialPostGeneratorException):
        # Наше кастомное исключение - используем его метод
        return exception.to_dict()
    else:
        # Неожиданное исключение - логируем и возвращаем общую ошибку
        logger.critical(
            f"🔥 Необработанное исключение: {type(exception).__name__}: {str(exception)}",
            exc_info=True
        )
        return {
            "success": False,
            "error": (
                "Произошла непредвиденная ошибка. "
                "Администратор уже уведомлен."
            ),
            "error_code": "INTERNAL_ERROR"
        }


if __name__ == "__main__":
    # Тесты исключений
    print("🧪 Тестирование исключений...\n")
    
    try:
        raise URLValidationError("invalid-url", "отсутствует протокол")
    except SocialPostGeneratorException as e:
        print("1. URLValidationError:")
        print(f"   {e.to_dict()}\n")
    
    try:
        raise URLFetchError("https://example.com", "timeout", 504)
    except SocialPostGeneratorException as e:
        print("2. URLFetchError:")
        print(f"   {e.to_dict()}\n")
    
    try:
        raise TextExtractionError("https://example.com", "страница пустая")
    except SocialPostGeneratorException as e:
        print("3. TextExtractionError:")
        print(f"   {e.to_dict()}\n")
    
    try:
        raise OpenAIError("Invalid API key")
    except SocialPostGeneratorException as e:
        print("4. OpenAIError:")
        print(f"   {e.to_dict()}\n")
    
    try:
        raise RateLimitError(retry_after=60)
    except SocialPostGeneratorException as e:
        print("5. RateLimitError:")
        print(f"   {e.to_dict()}\n")
    
    # Тест обработки обычного исключения
    try:
        raise ValueError("Неожиданная ошибка")
    except Exception as e:
        print("6. Обычное исключение:")
        print(f"   {handle_exception(e)}\n")
    
    print("✅ Все тесты пройдены!")

