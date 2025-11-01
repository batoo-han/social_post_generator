/**
 * Social Post Generator - Frontend Application
 * Управляет UI, взаимодействием с API и пользовательским опытом
 */

class SocialPostApp {
    constructor() {
        // API endpoints
        this.apiBase = window.location.origin;
        this.apiGenerate = `${this.apiBase}/api/generate`;
        this.apiStyles = `${this.apiBase}/api/styles`;
        
        // DOM элементы
        this.form = document.getElementById('generatorForm');
        this.urlInput = document.getElementById('urlInput');
        this.styleGrid = document.getElementById('styleGrid');
        this.generateBtn = document.getElementById('generateBtn');
        this.resultCard = document.getElementById('resultCard');
        this.postPreview = document.getElementById('postPreview');
        this.resultStyle = document.getElementById('resultStyle');
        this.resultLength = document.getElementById('resultLength');
        this.copyBtn = document.getElementById('copyBtn');
        this.newPostBtn = document.getElementById('newPostBtn');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.toastContainer = document.getElementById('toastContainer');
        this.lengthSlider = document.getElementById('lengthSlider');
        this.lengthInput = document.getElementById('lengthInput');
        
        // Состояние
        this.isGenerating = false;
        this.availableStyles = [];
        this.currentPost = null;
        this.selectedStyle = 'ироничный';
        this.maxLength = 800;
        
        // Инициализация
        this.init();
    }
    
    /**
     * Инициализация приложения
     */
    async init() {
        console.log('🚀 Инициализация Social Post Generator...');
        
        // Загружаем доступные стили
        await this.loadStyles();
        
        // Настраиваем обработчики событий
        this.setupEventListeners();
        
        // Проверяем параметры URL (для предзаполнения)
        this.checkUrlParams();
        
        console.log('✅ Приложение готово к работе');
    }
    
    /**
     * Загрузка доступных стилей из API
     */
    async loadStyles() {
        try {
            console.log('📥 Загрузка стилей...');
            
            const response = await fetch(this.apiStyles);
            const data = await response.json();
            
            if (data.success && data.styles) {
                this.availableStyles = data.styles;
                this.renderStyles();
                console.log(`✅ Загружено ${data.styles.length} стилей`);
            } else {
                throw new Error('Неожиданный формат ответа');
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки стилей:', error);
            this.showToast(
                'Не удалось загрузить стили. Используется стиль по умолчанию.',
                'error'
            );
            // Рендерим fallback
            this.renderFallbackStyles();
        }
    }
    
    /**
     * Рендеринг стилей в сетку
     */
    renderStyles() {
        this.styleGrid.innerHTML = '';
        
        this.availableStyles.forEach((style, index) => {
            const isChecked = index === 0; // Первый стиль выбран по умолчанию
            
            const styleOption = document.createElement('div');
            styleOption.className = 'style-option';
            styleOption.innerHTML = `
                <input 
                    type="radio" 
                    id="style-${style.id}" 
                    name="style" 
                    value="${style.name}" 
                    ${isChecked ? 'checked' : ''}
                >
                <label for="style-${style.id}" class="style-label">
                    <div class="style-emoji">${style.emoji}</div>
                    <div class="style-name">${style.name}</div>
                    <div class="style-desc">${style.description}</div>
                </label>
            `;
            
            this.styleGrid.appendChild(styleOption);
        });
        
        // Устанавливаем выбранный стиль
        if (this.availableStyles.length > 0) {
            this.selectedStyle = this.availableStyles[0].name;
        }
    }
    
    /**
     * Fallback стили если API недоступен
     */
    renderFallbackStyles() {
        const fallbackStyles = [
            { id: 'ironic', name: 'Ироничный', emoji: '😏', description: 'Умный юмор' },
            { id: 'professional', name: 'Профессиональный', emoji: '💼', description: 'Деловой стиль' },
            { id: 'motivational', name: 'Мотивационный', emoji: '🚀', description: 'Вдохновляющий' }
        ];
        
        this.availableStyles = fallbackStyles;
        this.renderStyles();
    }
    
    /**
     * Настройка обработчиков событий
     */
    setupEventListeners() {
        // Отправка формы
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleGenerate();
        });
        
        // Изменение стиля
        this.styleGrid.addEventListener('change', (e) => {
            if (e.target.name === 'style') {
                this.selectedStyle = e.target.value;
                console.log(`🎨 Выбран стиль: ${this.selectedStyle}`);
            }
        });
        
        // Синхронизация ползунка и поля ввода длины
        this.lengthSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            this.lengthInput.value = value;
            this.maxLength = value;
            console.log(`📏 Максимальная длина: ${this.maxLength}`);
        });
        
        this.lengthInput.addEventListener('input', (e) => {
            let value = parseInt(e.target.value);
            
            // Валидация
            if (isNaN(value)) value = 800;
            if (value < 400) value = 400;
            if (value > 4000) value = 4000;
            
            this.lengthSlider.value = value;
            this.maxLength = value;
            console.log(`📏 Максимальная длина: ${this.maxLength}`);
        });
        
        // Кнопка копирования
        this.copyBtn.addEventListener('click', () => {
            this.copyToClipboard();
        });
        
        // Кнопка нового поста
        this.newPostBtn.addEventListener('click', () => {
            this.resetForm();
        });
        
        // Enter в поле URL (только если фокус на нем)
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isGenerating) {
                e.preventDefault();
                this.handleGenerate();
            }
        });
        
        // Валидация URL в реальном времени
        this.urlInput.addEventListener('input', () => {
            this.validateUrl();
        });
    }
    
    /**
     * Проверка параметров URL для предзаполнения
     */
    checkUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const url = params.get('url');
        const style = params.get('style');
        
        if (url) {
            this.urlInput.value = url;
            console.log('📌 URL предзаполнен из параметров');
        }
        
        if (style) {
            const radio = document.querySelector(`input[value="${style}"]`);
            if (radio) {
                radio.checked = true;
                this.selectedStyle = style;
                console.log('📌 Стиль предзаполнен из параметров');
            }
        }
    }
    
    /**
     * Валидация URL
     */
    validateUrl() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.urlInput.style.borderColor = '';
            return true;
        }
        
        try {
            const urlObj = new URL(url);
            if (urlObj.protocol === 'http:' || urlObj.protocol === 'https:') {
                this.urlInput.style.borderColor = 'var(--success-color)';
                return true;
            } else {
                this.urlInput.style.borderColor = 'var(--error-color)';
                return false;
            }
        } catch {
            this.urlInput.style.borderColor = 'var(--error-color)';
            return false;
        }
    }
    
    /**
     * Обработка генерации поста
     */
    async handleGenerate() {
        // Проверка что не идет генерация
        if (this.isGenerating) {
            console.log('⏳ Генерация уже в процессе');
            return;
        }
        
        // Получаем данные формы
        const url = this.urlInput.value.trim();
        
        // Валидация
        if (!url) {
            this.showToast('Пожалуйста, введите URL', 'warning');
            this.urlInput.focus();
            return;
        }
        
        if (!this.validateUrl()) {
            this.showToast('Пожалуйста, введите корректный URL', 'error');
            this.urlInput.focus();
            return;
        }
        
        // Скрываем предыдущий результат
        this.resultCard.classList.add('hidden');
        
        // Показываем загрузку
        this.showLoading();
        
        try {
            console.log(`🚀 Начало генерации: url=${url}, style=${this.selectedStyle}, max_length=${this.maxLength}`);
            
            const response = await fetch(this.apiGenerate, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    style: this.selectedStyle,
                    max_length: this.maxLength
                })
            });
            
            const data = await response.json();
            
            // Проверяем ответ
            if (response.ok && data.success) {
                // Успешная генерация
                console.log('✅ Пост сгенерирован успешно');
                this.currentPost = data.post;
                this.displayResult(data);
                this.showToast('Пост успешно сгенерирован! 🎉', 'success');
            } else {
                // Ошибка от сервера
                console.error('❌ Ошибка генерации:', data);
                this.showToast(
                    data.error || 'Не удалось сгенерировать пост',
                    'error'
                );
            }
        } catch (error) {
            // Ошибка сети или парсинга
            console.error('❌ Ошибка запроса:', error);
            this.showToast(
                'Ошибка соединения с сервером. Попробуйте позже.',
                'error'
            );
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Отображение результата
     */
    displayResult(data) {
        // Устанавливаем текст поста
        this.postPreview.textContent = data.post;
        
        // Устанавливаем метаданные
        this.resultStyle.textContent = data.style;
        this.resultLength.textContent = data.length;
        
        // Показываем карточку с анимацией
        this.resultCard.classList.remove('hidden');
        
        // Плавно скроллим к результату
        setTimeout(() => {
            this.resultCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }
    
    /**
     * Копирование в буфер обмена
     */
    async copyToClipboard() {
        if (!this.currentPost) {
            console.warn('⚠️ Нет поста для копирования');
            return;
        }
        
        try {
            // Используем Clipboard API
            await navigator.clipboard.writeText(this.currentPost);
            
            // Меняем текст кнопки на короткое время
            const originalText = this.copyBtn.querySelector('.btn-text').textContent;
            const originalIcon = this.copyBtn.querySelector('.btn-icon').textContent;
            
            this.copyBtn.querySelector('.btn-text').textContent = 'Скопировано!';
            this.copyBtn.querySelector('.btn-icon').textContent = '✅';
            
            setTimeout(() => {
                this.copyBtn.querySelector('.btn-text').textContent = originalText;
                this.copyBtn.querySelector('.btn-icon').textContent = originalIcon;
            }, 2000);
            
            this.showToast('Пост скопирован в буфер обмена', 'success');
            console.log('📋 Пост скопирован');
        } catch (error) {
            console.error('❌ Ошибка копирования:', error);
            
            // Fallback для старых браузеров
            this.fallbackCopy();
        }
    }
    
    /**
     * Fallback метод копирования для старых браузеров
     */
    fallbackCopy() {
        const textArea = document.createElement('textarea');
        textArea.value = this.currentPost;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showToast('Пост скопирован в буфер обмена', 'success');
        } catch (error) {
            this.showToast('Не удалось скопировать текст', 'error');
        }
        
        document.body.removeChild(textArea);
    }
    
    /**
     * Сброс формы для нового поста
     */
    resetForm() {
        this.urlInput.value = '';
        this.urlInput.style.borderColor = '';
        this.currentPost = null;
        this.resultCard.classList.add('hidden');
        
        // Скроллим к форме
        this.form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Фокусируем поле ввода
        setTimeout(() => {
            this.urlInput.focus();
        }, 500);
        
        console.log('🔄 Форма сброшена');
    }
    
    /**
     * Показать overlay загрузки
     */
    showLoading() {
        this.isGenerating = true;
        this.loadingOverlay.classList.remove('hidden');
        this.generateBtn.disabled = true;
        this.generateBtn.classList.add('loading');
        this.generateBtn.querySelector('.btn-text').textContent = 'Генерируем...';
        this.generateBtn.querySelector('.btn-icon').textContent = '⏳';
        
        console.log('⏳ Загрузка началась');
    }
    
    /**
     * Скрыть overlay загрузки
     */
    hideLoading() {
        this.isGenerating = false;
        this.loadingOverlay.classList.add('hidden');
        this.generateBtn.disabled = false;
        this.generateBtn.classList.remove('loading');
        this.generateBtn.querySelector('.btn-text').textContent = 'Сгенерировать пост';
        this.generateBtn.querySelector('.btn-icon').textContent = '✨';
        
        console.log('✅ Загрузка завершена');
    }
    
    /**
     * Показать toast уведомление
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-message">${message}</div>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(400px)';
            setTimeout(() => {
                if (toast.parentNode) {
                    this.toastContainer.removeChild(toast);
                }
            }, 300);
        }, 5000);
        
        console.log(`📢 Toast [${type}]: ${message}`);
    }
}

// Инициализация приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM загружен');
    window.app = new SocialPostApp();
});

// Обработка ошибок
window.addEventListener('error', (event) => {
    console.error('🔥 Глобальная ошибка:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('🔥 Необработанный Promise:', event.reason);
});

console.log('✨ Social Post Generator загружен');

