"""
Модуль агента для генерации постов в социальные сети.

Основная бизнес-логика приложения: загрузка контента,
парсинг текста и генерация постов в разных стилях.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from urllib.parse import urlparse
import validators

from config import settings
from logger import get_logger, log_execution_time, LogContext
from openai_module import OpenAIClient, get_openai_client
from exceptions import (
    URLValidationError,
    URLFetchError,
    TextExtractionError,
    PostGenerationError
)

logger = get_logger(__name__)


class SocialPostAgent:
    """Агент для генерации постов в социальные сети."""

    # Определение доступных стилей и их промптов
    STYLES = {
        "ироничный": {
            "id": "ironic",
            "name": "Ироничный",
            "description": "Легкая ирония и самоирония, умный юмор",
            "emoji": "😏",
            "system_prompt": (
                "Ты креативный автор постов для социальных сетей. "
                "Твой стиль - легкая ирония, самоирония и умный юмор. "
                "Ты пишешь увлекательно, но не переходишь грань в сарказм. "
                "Используешь эмодзи умеренно и к месту."
            ),
            "user_prompt_template": (
                "На основе этого текста напиши короткий ироничный пост "
                "для социальных сетей (максимум 800 символов). "
                "Пост должен быть остроумным, интересным и цепляющим внимание.\n\n"
                "Текст: {text}"
            )
        },
        "профессиональный": {
            "id": "professional",
            "name": "Профессиональный",
            "description": "Деловой и информативный стиль",
            "emoji": "💼",
            "system_prompt": (
                "Ты профессиональный контент-менеджер. "
                "Твой стиль - деловой, информативный и структурированный. "
                "Ты пишешь четко, по существу, подчеркиваешь ключевые моменты. "
                "Избегаешь лишних эмоций, но остаешься интересным."
            ),
            "user_prompt_template": (
                "На основе этого текста напиши короткий профессиональный пост "
                "для социальных сетей (максимум 800 символов). "
                "Пост должен быть информативным, структурированным и полезным.\n\n"
                "Текст: {text}"
            )
        },
        "мотивационный": {
            "id": "motivational",
            "name": "Мотивационный",
            "description": "Вдохновляющий и побуждающий к действию",
            "emoji": "🚀",
            "system_prompt": (
                "Ты вдохновляющий коуч и мотиватор. "
                "Твой стиль - энергичный, позитивный и побуждающий к действию. "
                "Ты видишь возможности везде и умеешь заряжать людей энтузиазмом. "
                "Используешь мощные метафоры и призывы к действию."
            ),
            "user_prompt_template": (
                "На основе этого текста напиши короткий мотивационный пост "
                "для социальных сетей (максимум 800 символов). "
                "Пост должен вдохновлять, мотивировать и побуждать к действию.\n\n"
                "Текст: {text}"
            )
        },
        "юмористический": {
            "id": "humorous",
            "name": "Юмористический",
            "description": "Веселый и развлекательный контент",
            "emoji": "😄",
            "system_prompt": (
                "Ты талантливый комедийный автор. "
                "Твой стиль - легкий юмор, неожиданные повороты и игра слов. "
                "Ты умеешь рассмешить, не оскорбляя, и развлечь, оставаясь умным. "
                "Твои шутки всегда уместны и добродушны."
            ),
            "user_prompt_template": (
                "На основе этого текста напиши короткий юмористический пост "
                "для социальных сетей (максимум 800 символов). "
                "Пост должен быть смешным, легким и поднимающим настроение.\n\n"
                "Текст: {text}"
            )
        },
        "образовательный": {
            "id": "educational",
            "name": "Образовательный",
            "description": "Обучающий контент с полезными фактами",
            "emoji": "📚",
            "system_prompt": (
                "Ты опытный преподаватель и популяризатор знаний. "
                "Твой стиль - понятный, структурированный и познавательный. "
                "Ты умеешь объяснять сложное простыми словами. "
                "Всегда даешь практическую ценность и конкретные знания."
            ),
            "user_prompt_template": (
                "На основе этого текста напиши короткий образовательный пост "
                "для социальных сетей (максимум 800 символов). "
                "Пост должен учить, объяснять и давать полезную информацию.\n\n"
                "Текст: {text}"
            )
        },
        "эмоциональный": {
            "id": "emotional",
            "name": "Эмоциональный",
            "description": "Трогательный, чувственный и поэтичный стиль",
            "emoji": "❤️",
            "system_prompt": (
                "Ты чувствительный автор, умеющий затрагивать душу. "
                "Твой стиль - эмоциональный, искренний, глубокий и поэтичный. "
                "Ты пишешь о том, что важно, что трогает сердца и вызывает отклик. "
                "Используешь образные сравнения, метафоры и эмоциональные триггеры. "
                "Твои слова вдохновляют и создают эмоциональную связь с читателем."
            ),
            "user_prompt_template": (
                "На основе этого текста напиши короткий эмоциональный пост "
                "для социальных сетей (максимум 800 символов). "
                "Пост должен трогать, вызывать чувства и резонировать с читателем.\n\n"
                "Текст: {text}"
            )
        }
    }

    # Стиль по умолчанию
    DEFAULT_STYLE = "ироничный"

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """
        Инициализация агента.
        
        Args:
            openai_client: Клиент OpenAI (опционально)
        """
        self.openai_client = openai_client or get_openai_client()
        logger.info("✅ SocialPostAgent инициализирован")

    def validate_url(self, url: str) -> str:
        """
        Валидировать и нормализовать URL.
        
        Args:
            url: URL для валидации
            
        Returns:
            str: Нормализованный URL
            
        Raises:
            URLValidationError: Если URL невалидный
        """
        logger.debug(f"🔍 Валидация URL: {url}")
        
        # Проверка на пустоту
        if not url or not url.strip():
            raise URLValidationError(url, "URL пустой")
        
        url = url.strip()
        
        # Проверка базовой валидности
        if not validators.url(url):
            raise URLValidationError(url, "Невалидный формат URL")
        
        # Парсим URL
        parsed = urlparse(url)
        
        # Проверка протокола
        if parsed.scheme not in ['http', 'https']:
            raise URLValidationError(
                url,
                f"Неподдерживаемый протокол: {parsed.scheme}"
            )
        
        # Проверка наличия домена
        if not parsed.netloc:
            raise URLValidationError(url, "Отсутствует доменное имя")
        
        logger.debug(f"✅ URL валиден: {url}")
        return url

    @log_execution_time()
    def fetch_html(self, url: str) -> str:
        """
        Загрузить HTML контент по URL.
        
        Args:
            url: URL для загрузки
            
        Returns:
            str: HTML контент
            
        Raises:
            URLFetchError: Если не удалось загрузить страницу
        """
        logger.info(f"🌐 Загрузка страницы: {url}")
        
        headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=settings.fetch_timeout,
                allow_redirects=True,
                stream=True  # Для проверки размера
            )
            
            # Проверяем размер контента
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > settings.max_page_size:
                raise URLFetchError(
                    url,
                    reason=f"Страница слишком большая: {content_length} байт",
                    status_code=response.status_code
                )
            
            # Проверяем статус код
            response.raise_for_status()
            
            # Получаем контент
            html = response.text
            
            logger.info(
                f"✅ Страница загружена: {len(html)} символов, "
                f"статус: {response.status_code}"
            )
            
            return html
        
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Таймаут при загрузке {url}")
            raise URLFetchError(url, reason="Превышено время ожидания")
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"🔌 Ошибка соединения с {url}: {e}")
            raise URLFetchError(url, reason="Не удалось установить соединение")
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            logger.warning(f"❌ HTTP ошибка {status_code} для {url}")
            
            if status_code == 404:
                reason = "Страница не найдена (404)"
            elif status_code == 403:
                reason = "Доступ запрещен (403)"
            elif status_code == 500:
                reason = "Ошибка сервера (500)"
            else:
                reason = f"HTTP ошибка {status_code}"
            
            raise URLFetchError(url, reason=reason, status_code=status_code)
        
        except requests.exceptions.TooManyRedirects:
            logger.warning(f"🔄 Слишком много редиректов для {url}")
            raise URLFetchError(url, reason="Слишком много редиректов")
        
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при загрузке {url}: {e}")
            raise URLFetchError(url, reason=str(e))

    @log_execution_time()
    def extract_text(self, html: str) -> str:
        """
        Извлечь текстовый контент из HTML.
        
        Args:
            html: HTML контент
            
        Returns:
            str: Извлеченный текст
            
        Raises:
            TextExtractionError: Если не удалось извлечь текст
        """
        logger.debug("📄 Извлечение текста из HTML...")
        
        try:
            # Парсим HTML с помощью BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Удаляем скрипты и стили
            for script in soup(['script', 'style', 'meta', 'link', 'noscript']):
                script.decompose()
            
            # Пытаемся найти основной контент
            # Ищем в распространенных контейнерах контента
            main_content = None
            content_selectors = [
                'article',
                'main',
                '[role="main"]',
                '.content',
                '#content',
                '.post-content',
                '.entry-content',
                '.article-content',
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    logger.debug(f"✅ Найден контент в селекторе: {selector}")
                    break
            
            # Если не нашли - берем весь body
            if not main_content:
                main_content = soup.body if soup.body else soup
                logger.debug("ℹ️ Используется весь body")
            
            # Извлекаем текст
            text = main_content.get_text(separator=' ', strip=True)
            
            # Очищаем текст
            text = self.clean_text(text)
            
            logger.info(f"✅ Текст извлечен: {len(text)} символов")
            
            return text
        
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения текста: {e}", exc_info=True)
            raise TextExtractionError("unknown", reason=str(e))

    def clean_text(self, text: str) -> str:
        """
        Очистить текст от лишних символов и пробелов.
        
        Args:
            text: Текст для очистки
            
        Returns:
            str: Очищенный текст
        """
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем множественные переносы строк
        text = re.sub(r'\n+', '\n', text)
        
        # Убираем пробелы в начале и конце
        text = text.strip()
        
        return text

    def validate_text_length(self, text: str, url: str) -> None:
        """
        Проверить что текста достаточно для генерации.
        
        Args:
            text: Текст для проверки
            url: URL источника (для ошибки)
            
        Raises:
            TextExtractionError: Если текста недостаточно
        """
        if len(text) < settings.min_text_length:
            logger.warning(
                f"⚠️ Недостаточно текста: {len(text)} < {settings.min_text_length}"
            )
            raise TextExtractionError(
                url,
                reason=f"Текста недостаточно: {len(text)} символов"
            )

    def get_available_styles(self) -> List[Dict]:
        """
        Получить список доступных стилей.
        
        Returns:
            list: Список стилей с метаданными
        """
        return [
            {
                "id": style_data["id"],
                "name": style_data["name"],
                "description": style_data["description"],
                "emoji": style_data["emoji"]
            }
            for style_name, style_data in self.STYLES.items()
        ]

    def validate_style(self, style: str) -> str:
        """
        Валидировать и нормализовать стиль.
        
        Args:
            style: Стиль для валидации
            
        Returns:
            str: Нормализованный стиль
        """
        if not style:
            return self.DEFAULT_STYLE
        
        style = style.lower().strip()
        
        # Проверяем по русскому названию
        if style in self.STYLES:
            return style
        
        # Проверяем по ID
        for style_name, style_data in self.STYLES.items():
            if style_data["id"] == style:
                return style_name
        
        # Если не найден - возвращаем по умолчанию
        logger.warning(
            f"⚠️ Неизвестный стиль '{style}', "
            f"используется '{self.DEFAULT_STYLE}'"
        )
        return self.DEFAULT_STYLE

    @log_execution_time()
    def generate_post(
        self, 
        url: str, 
        style: Optional[str] = None,
        max_length: Optional[int] = None
    ) -> str:
        """
        Сгенерировать пост на основе контента URL.
        
        Args:
            url: URL страницы
            style: Стиль генерации (опционально)
            max_length: Максимальная длина поста в символах (опционально, по умолчанию из settings)
            
        Returns:
            str: Сгенерированный пост
            
        Raises:
            URLValidationError: Если URL невалидный
            URLFetchError: Если не удалось загрузить страницу
            TextExtractionError: Если не удалось извлечь текст
            PostGenerationError: Если не удалось сгенерировать пост
        """
        with LogContext(f"Генерация поста для {url}", logger=logger):
            # 1. Валидируем URL
            url = self.validate_url(url)
            
            # 2. Валидируем стиль
            style = self.validate_style(style)
            style_config = self.STYLES[style]
            
            # 3. Определяем максимальную длину
            post_max_length = max_length or settings.max_post_length
            if post_max_length < 400:
                post_max_length = 400
            elif post_max_length > 4000:
                post_max_length = 4000
            
            logger.info(f"🎨 Стиль: {style} ({style_config['emoji']})")
            logger.info(f"📏 Максимальная длина поста: {post_max_length} символов")
            
            # 3. Загружаем HTML
            html = self.fetch_html(url)
            
            # 4. Извлекаем текст
            text = self.extract_text(html)
            
            # 5. Проверяем длину текста
            self.validate_text_length(text, url)
            
            # 6. Ограничиваем текст для промпта (чтобы не превысить токены)
            max_text_length = 3000  # Примерно 750 токенов
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
                logger.debug(f"✂️ Текст обрезан до {max_text_length} символов")
            
            # 7. Формируем промпты с указанием длины
            system_prompt = style_config["system_prompt"]
            user_prompt = style_config["user_prompt_template"].format(text=text)
            # Добавляем явное указание максимальной длины в промпт
            user_prompt = user_prompt.replace(
                "максимум 800 символов",
                f"максимум {post_max_length} символов"
            )
            
            logger.debug(f"📝 Длина промпта: {len(user_prompt)} символов")
            
            # 8. Генерируем пост
            try:
                post = self.openai_client.generate_text(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
            except Exception as e:
                logger.error(f"❌ Ошибка генерации поста: {e}")
                raise PostGenerationError(
                    reason=str(e),
                    url=url,
                    style=style
                )
            
            # 9. Валидируем и обрезаем пост
            post = post.strip()
            
            if len(post) > post_max_length:
                logger.warning(
                    f"✂️ Пост обрезан с {len(post)} "
                    f"до {post_max_length} символов"
                )
                post = post[:post_max_length].rsplit(' ', 1)[0] + "..."
            
            logger.info(
                f"✅ Пост сгенерирован: {len(post)} символов, "
                f"стиль: {style}, "
                f"макс. длина: {post_max_length}"
            )
            
            return post


# Глобальный экземпляр агента
_global_agent: Optional[SocialPostAgent] = None


def get_agent() -> SocialPostAgent:
    """
    Получить глобальный экземпляр агента (singleton).
    
    Returns:
        SocialPostAgent: Агент генерации постов
    """
    global _global_agent
    
    if _global_agent is None:
        logger.info("🔧 Создание глобального экземпляра агента...")
        _global_agent = SocialPostAgent()
    
    return _global_agent


if __name__ == "__main__":
    # Тест агента
    print("🧪 Тестирование агента генерации постов...\n")
    
    agent = get_agent()
    
    # Показываем доступные стили
    print("📋 Доступные стили:")
    for style in agent.get_available_styles():
        print(f"   {style['emoji']} {style['name']}: {style['description']}")
    print()
    
    # Тестовый URL (используем example.com для теста)
    test_url = "https://example.com"
    
    try:
        print(f"🎯 Генерация поста для: {test_url}")
        print(f"🎨 Стиль: ироничный\n")
        
        post = agent.generate_post(test_url, "ироничный")
        
        print("✅ Результат:")
        print(f"{'='*60}")
        print(post)
        print(f"{'='*60}")
        print(f"\n📊 Длина: {len(post)} символов")
        
        # Статистика OpenAI
        stats = agent.openai_client.get_statistics()
        print(f"\n📈 Статистика API:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Тест успешно пройден!")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print(f"   Тип: {type(e).__name__}")
        if hasattr(e, 'user_message'):
            print(f"   Сообщение пользователю: {e.user_message}")

