"""
Веб-сервер приложения на FastAPI.

Предоставляет REST API для генерации постов и веб-интерфейс.
"""

import time
import psutil
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn
from collections import defaultdict
from datetime import datetime, timedelta

from config import settings
from logger import get_logger, LogContext
from agent import get_agent, SocialPostAgent
from openai_module import get_openai_client
from exceptions import (
    SocialPostGeneratorException,
    handle_exception,
    URLValidationError,
    URLFetchError,
    TextExtractionError,
    OpenAIError,
    PostGenerationError
)

logger = get_logger(__name__)

# Простой rate limiter без зависимостей (избегаем проблем с кодировкой .env в slowapi)
class SimpleRateLimiter:
    """Простой rate limiter на основе IP адресов."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Проверить разрешен ли запрос."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Очищаем старые запросы
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        # Проверяем лимит
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Добавляем текущий запрос
        self.requests[key].append(now)
        return True

# Инициализируем rate limiter (10 запросов в минуту)
rate_limiter = SimpleRateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)


# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения."""
    # Startup
    logger.info("🚀 Запуск приложения...")
    logger.info(f"📍 Порт: {settings.port}")
    logger.info(f"🔧 Режим отладки: {settings.debug}")
    logger.info(f"📊 Уровень логирования: {settings.log_level}")
    
    # Инициализируем агента и OpenAI клиента
    try:
        agent = get_agent()
        logger.info("✅ Агент инициализирован")
        
        # Проверяем доступность OpenAI
        if agent.openai_client.check_health():
            logger.info("✅ OpenAI API доступен")
        else:
            logger.warning("⚠️ OpenAI API недоступен")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 Остановка приложения...")
    
    # Выводим финальную статистику
    try:
        agent = get_agent()
        stats = agent.openai_client.get_statistics()
        logger.info(f"📊 Финальная статистика: {stats}")
    except:
        pass


# Создаем приложение FastAPI
app = FastAPI(
    title="Social Post Generator",
    description="Генератор постов для социальных сетей с использованием AI",
    version="1.0.0",
    lifespan=lifespan
)

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware для rate limiting."""
    # Получаем IP адрес клиента
    client_ip = request.client.host
    
    # Проверяем только API запросы
    if request.url.path.startswith("/api/"):
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(f"⚠️ Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Превышен лимит запросов. Пожалуйста, подождите перед следующей попыткой.",
                    "error_code": "RATE_LIMIT_ERROR",
                    "retry_after": 60
                }
            )
    
    response = await call_next(request)
    return response


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования всех запросов."""
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(
        f"📨 {request.method} {request.url.path} "
        f"from {request.client.host}"
    )
    
    # Обрабатываем запрос
    try:
        response = await call_next(request)
        
        # Логируем ответ
        duration = time.time() - start_time
        logger.info(
            f"✅ {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration:.3f}s)"
        )
        
        return response
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"❌ {request.method} {request.url.path} "
            f"→ ERROR ({duration:.3f}s): {e}"
        )
        raise


# Pydantic модели для валидации
class GeneratePostRequest(BaseModel):
    """Запрос на генерацию поста."""
    url: str = Field(..., description="URL веб-страницы", min_length=10, max_length=2000)
    style: Optional[str] = Field(
        default="ироничный",
        description="Стиль генерации"
    )
    max_length: Optional[int] = Field(
        default=800,
        ge=400,
        le=4000,
        description="Максимальная длина поста в символах"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Валидация URL."""
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v


class GeneratePostResponse(BaseModel):
    """Ответ с сгенерированным постом."""
    success: bool = Field(default=True)
    post: str = Field(..., description="Сгенерированный пост")
    length: int = Field(..., description="Длина поста в символах")
    style: str = Field(..., description="Использованный стиль")
    url: str = Field(..., description="Обработанный URL")
    timestamp: str = Field(..., description="Время генерации")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Сообщение об ошибке")
    error_code: str = Field(..., description="Код ошибки")


class HealthResponse(BaseModel):
    """Ответ health check."""
    status: str = Field(..., description="Статус сервиса")
    timestamp: str = Field(..., description="Время проверки")
    version: str = Field(default="1.0.0")
    checks: dict = Field(..., description="Проверки компонентов")


class StyleInfo(BaseModel):
    """Информация о стиле."""
    id: str
    name: str
    description: str
    emoji: str


class StylesResponse(BaseModel):
    """Ответ со списком стилей."""
    success: bool = Field(default=True)
    styles: list[StyleInfo]
    default: str


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница с веб-интерфейсом."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>Social Post Generator</title></head>
            <body>
                <h1>🎯 Social Post Generator</h1>
                <p>Веб-интерфейс в разработке. Используйте API напрямую.</p>
                <p>API документация: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """


@app.post(
    "/api/generate",
    response_model=GeneratePostResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        429: {"description": "Too Many Requests"}
    }
)
async def generate_post(request: Request, body: GeneratePostRequest):
    """
    Сгенерировать пост для социальных сетей.
    
    Загружает контент веб-страницы и генерирует короткий пост
    в заданном стиле с помощью AI.
    """
    with LogContext(
        f"API запрос: generate_post(url={body.url}, style={body.style})",
        logger=logger
    ):
        try:
            # Получаем агента
            agent = get_agent()
            
            # Генерируем пост с заданной максимальной длиной
            post = agent.generate_post(
                url=body.url, 
                style=body.style,
                max_length=body.max_length
            )
            
            # Формируем ответ
            response = GeneratePostResponse(
                post=post,
                length=len(post),
                style=body.style or "ироничный",
                url=body.url,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
            
            logger.info("✅ Пост успешно сгенерирован и отправлен клиенту")
            return response
        
        except SocialPostGeneratorException as e:
            # Наше кастомное исключение
            logger.warning(f"⚠️ Ошибка генерации: {e.error_code}")
            error_dict = e.to_dict()
            
            # Определяем HTTP статус код
            if isinstance(e, (URLValidationError,)):
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            elif isinstance(e, (URLFetchError, TextExtractionError, PostGenerationError)):
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            return JSONResponse(
                status_code=status_code,
                content=error_dict
            )
        
        except Exception as e:
            # Неожиданная ошибка
            logger.error(f"❌ Необработанная ошибка: {e}", exc_info=True)
            error_dict = handle_exception(e)
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_dict
            )


@app.get("/api/styles", response_model=StylesResponse)
async def get_styles():
    """
    Получить список доступных стилей генерации.
    
    Возвращает все поддерживаемые стили с описаниями.
    """
    try:
        agent = get_agent()
        styles_list = agent.get_available_styles()
        
        return StylesResponse(
            styles=[StyleInfo(**style) for style in styles_list],
            default="ironic"
        )
    
    except Exception as e:
        logger.error(f"❌ Ошибка получения стилей: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список стилей"
        )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка здоровья сервиса.
    
    Проверяет работоспособность приложения и его зависимостей.
    """
    checks = {}
    overall_status = "healthy"
    
    # Проверка OpenAI
    try:
        agent = get_agent()
        openai_available = agent.openai_client.check_health()
        checks["openai"] = {
            "status": "available" if openai_available else "unavailable"
        }
        if not openai_available:
            overall_status = "degraded"
    except Exception as e:
        checks["openai"] = {
            "status": "unavailable",
            "error": str(e)
        }
        overall_status = "degraded"
    
    # Проверка памяти
    try:
        memory = psutil.virtual_memory()
        checks["memory"] = {
            "used_mb": round(memory.used / 1024 / 1024, 2),
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "percent": memory.percent
        }
        
        if memory.percent > 90:
            overall_status = "degraded"
    except Exception as e:
        checks["memory"] = {"error": str(e)}
    
    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=checks
    )
    
    # Возвращаем 503 если unhealthy
    if overall_status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.dict()
        )
    
    return response


# Монтируем статические файлы
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("⚠️ Директория static не найдена, статика не смонтирована")


# Обработчик 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Обработчик 404 ошибки."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint не найден",
            "error_code": "NOT_FOUND",
            "path": request.url.path
        }
    )


# Обработчик 500
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Обработчик 500 ошибки."""
    logger.error(f"🔥 Internal Server Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Внутренняя ошибка сервера. Администратор уведомлен.",
            "error_code": "INTERNAL_ERROR"
        }
    )


def main():
    """Запуск сервера."""
    logger.info("🎯 Social Post Generator")
    logger.info(f"🌐 Запуск сервера на http://{settings.host}:{settings.port}")
    logger.info(f"📚 API документация: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()

