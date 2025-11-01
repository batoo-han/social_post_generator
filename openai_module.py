"""
Модуль для работы с OpenAI API через ProxyAPI.ru.

Предоставляет класс для взаимодействия с моделями GPT
через ProxyAPI.ru - сервис доступа к OpenAI в России без VPN.

Документация: https://proxyapi.ru/docs/openai-text-generation
"""

import time
from typing import Optional, Dict, Any
from openai import OpenAI, APIError, RateLimitError as OpenAIRateLimitError, APIConnectionError, APITimeoutError

from config import settings
from logger import get_logger, log_execution_time, LogContext
from exceptions import OpenAIError, RateLimitError, ConfigurationError

logger = get_logger(__name__)


class OpenAIClient:
    """Клиент для работы с OpenAI API через ProxyAPI.ru."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Инициализация клиента OpenAI через ProxyAPI.ru.
        
        Args:
            api_key: API ключ ProxyAPI (из настроек по умолчанию)
            base_url: Базовый URL API ProxyAPI (из настроек по умолчанию)
            model: Модель для использования (из настроек по умолчанию)
            
        Note:
            ProxyAPI полностью совместим со стандартным OpenAI Chat Completions API.
            Используется стандартный client.chat.completions.create() с messages.
        """
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.model = model or settings.openai_model
        
        # Валидация параметров
        self._validate_config()
        
        # Создаем клиент OpenAI для ProxyAPI
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=30.0,  # 30 секунд таймаут
            )
            logger.info(
                f"✅ ProxyAPI клиент инициализирован: "
                f"модель={self.model}, base_url={self.base_url}"
            )
            logger.info(
                f"📡 Используется ProxyAPI.ru для доступа к OpenAI в России"
            )
        except Exception as e:
            logger.critical(f"🔥 Ошибка инициализации ProxyAPI клиента: {e}")
            raise ConfigurationError(
                parameter="ProxyAPI",
                reason=f"Не удалось создать клиент: {str(e)}"
            )
        
        # Счетчики для статистики
        self.total_requests = 0
        self.total_tokens = 0
        self.failed_requests = 0

    def _validate_config(self) -> None:
        """Валидация конфигурации."""
        if not self.api_key or self.api_key == "your_proxyapi_key_here":
            raise ConfigurationError(
                parameter="OPENAI_API_KEY",
                reason="ProxyAPI ключ не установлен"
            )
        
        # Проверка что используется правильный base_url для ProxyAPI
        if "proxyapi.ru" not in self.base_url:
            logger.warning(
                f"⚠️ Base URL не содержит 'proxyapi.ru': {self.base_url}. "
                f"Убедитесь что используете правильный эндпоинт ProxyAPI."
            )
        
        # Валидация модели для ProxyAPI
        supported_models = ["gpt-4.1-mini", "gpt-4o", "gpt-5-mini", "gpt-4o-mini", "gpt-4-turbo"]
        if self.model not in supported_models:
            logger.warning(
                f"⚠️ Модель '{self.model}' может не поддерживаться ProxyAPI. "
                f"Рекомендуемые: {', '.join(supported_models)}"
            )

    @log_execution_time()
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Сгенерировать текст с помощью GPT модели через ProxyAPI.
        
        Args:
            prompt: Основной промпт
            system_prompt: Системный промпт (опционально)
            max_retries: Максимальное количество попыток при ошибках
            
        Returns:
            str: Сгенерированный текст
            
        Raises:
            OpenAIError: При ошибке генерации
            RateLimitError: При превышении лимитов
            
        Note:
            ProxyAPI полностью совместим со стандартным OpenAI Chat Completions API.
            Используется client.chat.completions.create() с messages.
            Параметры temperature и max_tokens можно не указывать (ProxyAPI использует умолчания).
        """
        logger.debug(
            f"📝 Генерация текста через ProxyAPI: "
            f"модель={self.model}, "
            f"prompt_length={len(prompt)}"
        )
        
        # Формируем сообщения для Chat Completions API
        # ProxyAPI совместим со стандартным OpenAI API
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        logger.debug(f"📝 Сообщений в запросе: {len(messages)}")
        
        # Пытаемся сгенерировать с retry механизмом
        last_error = None
        for attempt in range(max_retries):
            try:
                with LogContext(
                    f"ProxyAPI запрос (попытка {attempt + 1}/{max_retries})",
                    logger=logger
                ):
                    # Используем стандартный Chat Completions API (ProxyAPI совместим)
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                    )
                
                # Извлекаем текст из ответа
                # ProxyAPI возвращает структуру совместимую с OpenAI
                generated_text = response.choices[0].message.content.strip()
                
                # Обновляем статистику
                self.total_requests += 1
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens
                    self.total_tokens += tokens_used
                    logger.debug(f"📊 Использовано токенов: {tokens_used}")
                else:
                    logger.debug(f"📊 Информация о токенах недоступна")
                
                logger.info(
                    f"✅ Текст успешно сгенерирован через ProxyAPI: "
                    f"длина={len(generated_text)} символов"
                )
                
                return generated_text
            
            except OpenAIRateLimitError as e:
                # Rate limit - не retry, сразу возвращаем ошибку
                logger.warning(f"⚠️ ProxyAPI rate limit превышен: {e}")
                self.failed_requests += 1
                
                # Пытаемся извлечь retry_after из ошибки
                retry_after = None
                if hasattr(e, 'retry_after'):
                    retry_after = e.retry_after
                
                raise RateLimitError(retry_after=retry_after)
            
            except APITimeoutError as e:
                logger.warning(
                    f"⚠️ Таймаут при запросе к ProxyAPI "
                    f"(попытка {attempt + 1}/{max_retries}): {e}"
                )
                last_error = e
                
                if attempt < max_retries - 1:
                    # Экспоненциальная задержка перед повтором
                    delay = 2 ** attempt
                    logger.info(f"⏳ Ожидание {delay} сек перед повтором...")
                    time.sleep(delay)
                else:
                    self.failed_requests += 1
                    raise OpenAIError(
                        reason="Таймаут запроса",
                        api_error=e,
                        retry_count=attempt + 1
                    )
            
            except APIConnectionError as e:
                logger.warning(
                    f"⚠️ Ошибка соединения с ProxyAPI "
                    f"(попытка {attempt + 1}/{max_retries}): {e}"
                )
                last_error = e
                
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.info(f"⏳ Ожидание {delay} сек перед повтором...")
                    time.sleep(delay)
                else:
                    self.failed_requests += 1
                    raise OpenAIError(
                        reason="Ошибка соединения",
                        api_error=e,
                        retry_count=attempt + 1
                    )
            
            except APIError as e:
                logger.error(f"❌ Ошибка ProxyAPI: {e}")
                self.failed_requests += 1
                
                # Не retry для ошибок аутентификации и т.п.
                raise OpenAIError(
                    reason=str(e),
                    api_error=e,
                    retry_count=attempt + 1
                )
            
            except Exception as e:
                logger.error(
                    f"❌ Неожиданная ошибка при генерации "
                    f"(попытка {attempt + 1}/{max_retries}): {e}",
                    exc_info=True
                )
                last_error = e
                
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)
                else:
                    self.failed_requests += 1
                    raise OpenAIError(
                        reason="Неожиданная ошибка",
                        api_error=e,
                        retry_count=attempt + 1
                    )
        
        # Если дошли сюда - все попытки провалились
        self.failed_requests += 1
        raise OpenAIError(
            reason="Все попытки исчерпаны",
            api_error=last_error,
            retry_count=max_retries
        )

    def validate_response(self, text: str, min_length: int = 10) -> bool:
        """
        Валидировать ответ от модели.
        
        Args:
            text: Текст для валидации
            min_length: Минимальная длина текста
            
        Returns:
            bool: True если текст валидный
        """
        if not text or not text.strip():
            logger.warning("⚠️ Пустой ответ от модели")
            return False
        
        if len(text.strip()) < min_length:
            logger.warning(
                f"⚠️ Ответ слишком короткий: "
                f"{len(text.strip())} < {min_length}"
            )
            return False
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику использования API.
        
        Returns:
            dict: Словарь со статистикой
        """
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = (
                (self.total_requests - self.failed_requests) / 
                self.total_requests * 100
            )
        
        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 2),
            "total_tokens": self.total_tokens,
            "model": self.model
        }

    def check_health(self) -> bool:
        """
        Проверить доступность ProxyAPI.
        
        Returns:
            bool: True если API доступен
        """
        try:
            logger.debug("🏥 Проверка здоровья ProxyAPI...")
            
            # Простой тестовый запрос через стандартный API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
            )
            
            logger.info("✅ ProxyAPI доступен")
            return True
        
        except Exception as e:
            logger.error(f"❌ ProxyAPI недоступен: {e}")
            return False


# Глобальный экземпляр клиента
_global_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """
    Получить глобальный экземпляр ProxyAPI клиента (singleton).
    
    Returns:
        OpenAIClient: Клиент ProxyAPI для доступа к OpenAI
    """
    global _global_client
    
    if _global_client is None:
        logger.info("🔧 Создание глобального экземпляра ProxyAPI клиента...")
        _global_client = OpenAIClient()
    
    return _global_client


if __name__ == "__main__":
    # Тест модуля
    print("🧪 Тестирование ProxyAPI модуля...\n")
    
    try:
        # Создаем клиент
        client = get_openai_client()
        print(f"✅ ProxyAPI клиент создан: модель={client.model}\n")
        print(f"📡 Base URL: {client.base_url}\n")
        
        # Проверяем здоровье
        if client.check_health():
            print("✅ ProxyAPI доступен\n")
        
        # Тестовая генерация
        print("📝 Генерация тестового текста через ProxyAPI...")
        result = client.generate_text(
            prompt="Напиши короткий ироничный пост о Python в одно предложение.",
            system_prompt="Ты автор ироничных постов для соцсетей."
        )
        print(f"Результат: {result}\n")
        
        # Статистика
        stats = client.get_statistics()
        print("📊 Статистика:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Тесты ProxyAPI успешно пройдены!")
    
    except ConfigurationError as e:
        print(f"❌ Ошибка конфигурации: {e.message}")
        print("💡 Проверьте файл .env и настройте OPENAI_API_KEY (ProxyAPI ключ)")
        print("💡 Убедитесь что OPENAI_BASE_URL = https://api.proxyapi.ru/openai/v1")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

