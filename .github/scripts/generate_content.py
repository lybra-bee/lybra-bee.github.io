#!/usr/bin/env python3
"""
Генератор контента для Hugo блога с AI-статьями и изображениями
"""

import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import time
import logging
import argparse
import base64
import sys

# Добавляем путь к скриптам
sys.path.append(os.path.dirname(__file__))

from helpers import generate_slug, generate_frontmatter, generate_enhanced_placeholder

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ======== КОНФИГУРАЦИЯ ========
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_telegram_bot_token_here')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'your_telegram_chat_id_here')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# ======== Генерация темы ========
def generate_ai_trend_topic():
    """Генерация случайной темы про AI тренды"""
    current_trends_2025 = [
        "Multimodal AI интеграция текста изображений и аудио в единых моделях",
        "AI агенты автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение прорыв в производительности",
        "Нейроморфные вычисления энергоэффективные архитектуры нейросетей",
        "Generative AI создание контента кода и дизайнов искусственным интеллектом",
        "Edge AI обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности предиктивная защита от угроз",
        "Этичный AI ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare диагностика разработка лекарств и персонализированная медицина",
        "Автономные системы беспилотный транспорт и робототехника",
        "AI оптимизация сжатие моделей и ускорение inference",
        "Доверенный AI объяснимые и прозрачные алгоритмы",
        "AI для климата оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты индивидуализированные цифровые помощники",
        "AI в образовании адаптивное обучение и персонализированные учебные планы"
    ]
    
    application_domains = [
        "в веб разработке и cloud native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес аналитике",
        "в компьютерной безопасности и киберзащите",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях и EdTech"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025 {trend} для {domain}",
        f"{trend} будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    
    return random.choice(topic_formats)

# ======== Очистка старых статей ========
def clean_old_articles(keep_last=5):
    """Очистка старых статей, оставляем только последние"""
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
    content_dir = "content/posts"
    images_dir = "static/images/posts"
    
    # Очистка старых статей
    if os.path.exists(content_dir):
        posts = sorted([f for f in os.listdir(content_dir) if f.endswith('.md') and f != '_index.md'], 
                      reverse=True)
        for post in posts[keep_last:]:
            os.remove(os.path.join(content_dir, post))
            logger.info(f"🗑️ Удален старый пост: {post}")
            
            # Пробуем удалить соответствующее изображение
            image_name = os.path.splitext(post)[0] + '.jpg'
            image_path = os.path.join(images_dir, image_name)
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"🗑️ Удалено старое изображение: {image_name}")
    
    # Создаем структуру если не существует
    os.makedirs(content_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # Создаем индексные файлы если не существуют
    if not os.path.exists("content/posts/_index.md"):
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---\n\nВсе AI-статьи, сгенерированные автоматически.")

# ======== Генерация статьи ========
def generate_content():
    """Основная функция генерации контента"""
    logger.info("🚀 Запуск генерации контента для Hugo...")
    
    # Проверка переменных окружения
    check_environment_variables()
    
    # Очистка старых статей
    clean_old_articles()
    
    # Генерация темы
    topic = generate_ai_trend_topic()
    logger.info(f"📝 Тема статьи: {topic}")
    
    # Генерация изображения
    image_filename = generate_article_image(topic)
    
    # Генерация текста статьи
    content, model_used = generate_article_content(topic)
    
    # Создание файла статьи
    slug = generate_slug(topic)
    filename = f"content/posts/{slug}.md"
    
    # Генерация frontmatter для Hugo
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    
    # Сохранение статьи
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    logger.info(f"✅ Статья для Hugo создана: {filename}")
    return filename

def check_environment_variables():
    """Проверка всех необходимых переменных окружения"""
    env_vars = {
        'OPENROUTER_API_KEY': OPENROUTER_API_KEY,
        'GROQ_API_KEY': GROQ_API_KEY,
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    
    logger.info("🔍 Проверка переменных окружения:")
    for var_name, var_value in env_vars.items():
        status = "✅ установлен" if var_value and var_value != 'your_telegram_bot_token_here' else "❌ отсутствует"
        logger.info(f"   {var_name}: {status}")

# ======== Генерация текста через OpenRouter/Groq ========
def generate_article_content(topic):
    """Генерация текста статьи через AI API"""
    models_to_try = []

    if GROQ_API_KEY:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview", "llama-3.1-70b-versatile"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(m, topic)))
    
    if OPENROUTER_API_KEY:
        openrouter_models = ["anthropic/claude-3-haiku", "anthropic/claude-3-sonnet", "google/gemini-pro-1.5"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(m, topic)))

    # Если нет API ключей, используем fallback
    if not models_to_try:
        logger.warning("⚠️ Нет доступных API ключей для генерации текста")
        fallback = generate_fallback_content(topic)
        return fallback, "fallback-generator"

    # Пробуем все доступные модели
    for model_name, generate_func in models_to_try:
        try:
            logger.info(f"🔄 Пробуем генерацию текста: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                logger.info(f"✅ Успешно через {model_name}")
                return result, model_name
            else:
                logger.warning(f"⚠️ Пустой ответ от {model_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка {model_name}: {e}")
            continue

    logger.warning("⚠️ Все модели не сработали, используем fallback")
    fallback = generate_fallback_content(topic)
    return fallback, "fallback-generator"

def generate_fallback_content(topic):
    """Fallback контент если все API не работают"""
    sections = [
        f"# {topic}",
        "",
        "## Введение",
        f"Тема '{topic}' становится increasingly important в 2025 году. ",
        "Искусственный интеллект продолжает трансформировать различные отрасли,",
        "предлагая инновационные решения для сложных задач.",
        "",
        "## Основные тенденции",
        "- Автоматизация процессов разработки и тестирования",
        "- Интеграция AI в существующие workflow и системы",
        "- Улучшение качества и скорости разработки программного обеспечения",
        "- Персонализация пользовательского опыта с помощью машинного обучения",
        "",
        "## Практическое применение",
        "Компании по всему миру активно внедряют AI решения для оптимизации",
        "своих бизнес-процессов. От автоматизации рутинных задач до сложного",
        "анализа данных - искусственный интеллект находит применение в самых",
        "разных областях.",
        "",
        "## Заключение",
        "Будущее выглядит promising с развитием AI технологий. По мере того как",
        "алгоритмы становятся более sophisticated, мы можем ожидать появления",
        "еще более инновационных решений, которые изменят нашу жизнь к лучшему.",
        "",
        "*Статья сгенерирована автоматически*",
        f"*Тема: {topic}*",
        f"*Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    ]
    return "\n".join(sections)

def generate_with_groq(model_name, topic):
    """Генерация через Groq API"""
    prompt = f"""Напиши развернутую статью на тему: '{topic}' на русском языке.

Требования:
- Формат Markdown
- 400-600 слов
- Структура: введение, основные разделы, заключение
- Профессиональный стиль написания
- Конкретные примеры и кейсы использования
- Актуальная информация на 2025 год
- Практические рекомендации
"""
    
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model_name, 
            "messages": [{"role": "user", "content": prompt}], 
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"Groq API error {resp.status_code}: {resp.text}")

def generate_with_openrouter(model_name, topic):
    """Генерация через OpenRouter API"""
    prompt = f"""Напиши развернутую статью на тему: '{topic}' на русском языке.

Требования:
- Формат Markdown
- 400-600 слов
- Структурированный контент с заголовками разных уровней
- Практические примеры и case studies
- Профессиональный тон написания
- Актуальные данные и статистика
- Выводы и рекомендации для читателей
"""
    
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-content-generator.com",
            "X-Title": "AI Content Generator"
        },
        json={
            "model": model_name, 
            "messages": [{"role": "user", "content": prompt}], 
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"OpenRouter API error {resp.status_code}: {resp.text}")

# ======== Генерация изображений ========
def generate_article_image(topic):
    """Умная генерация изображения с приоритетами"""
    logger.info(f"🎨 Генерация изображения: {topic}")
    
    # 1. Пробуем Telegram бота
    telegram_result = generate_via_telegram(topic)
    if telegram_result:
        return telegram_result
    
    # 2. Пробуем бесплатные API
    for api_func in [try_craiyon, try_deepai_public, try_huggingface_public]:
        try:
            result = api_func(topic[:150], topic)
            if result:
                return result
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Ошибка в {api_func.__name__}: {e}")
            continue
    
    # 3. Fallback на качественный placeholder
    logger.warning("✅ Все API не сработали, используем улучшенный placeholder")
    return generate_enhanced_placeholder(topic)

def generate_via_telegram(topic):
    """Генерация изображения через Telegram-бота"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return None
        
    prompt = f"{topic}, digital art, futuristic, professional, 4k, high quality, trending"
    
    try:
        # Отправляем запрос боту
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": prompt
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Запрос отправлен боту")
            # Ждем генерации
            time.sleep(35)
            return f"/images/posts/{generate_slug(topic)}.jpg"
            
    except Exception as e:
        logger.error(f"❌ Ошибка Telegram API: {e}")
    
    return None

# ======== Бесплатные API для изображений ========
def try_craiyon(prompt, topic):
    """Craiyon (бывший DALL-E mini)"""
    try:
        logger.info("🎨 Craiyon генерация...")
        response = requests.post(
            "https://api.craiyon.com/v3",
            json={"prompt": prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("images"):
                image_data = base64.b64decode(data["images"][0])
                return save_image_bytes(image_data, topic)
    except Exception as e:
        logger.error(f"❌ Craiyon error: {e}")
    return None

def try_deepai_public(prompt, topic):
    """DeepAI с публичным ключом"""
    try:
        logger.info("🎨 DeepAI генерация...")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            headers={'api-key': 'quickstart-credential'},
            data={'text': prompt},
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('output_url'):
                return save_image_from_url(data['output_url'], topic)
    except Exception as e:
        logger.error(f"❌ DeepAI error: {e}")
    return None

def try_huggingface_public(prompt, topic):
    """Hugging Face публичные модели"""
    try:
        logger.info("🎨 Hugging Face генерация...")
        models = [
            "runwayml/stable-diffusion-v1-5",
            "stabilityai/stable-diffusion-2-1"
        ]
        
        for model in models:
            try:
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    json={"inputs": prompt},
                    timeout=30
                )
                if response.status_code == 200:
                    return save_image_bytes(response.content, topic)
            except:
                continue
    except Exception as e:
        logger.error(f"❌ HF error: {e}")
    return None

def save_image_bytes(image_data, topic):
    """Сохранение изображения из bytes"""
    try:
        os.makedirs("static/images/posts", exist_ok=True)
        filename = f"static/images/posts/{generate_slug(topic)}.jpg"
        
        with open(filename, "wb") as f:
            f.write(image_data)
        
        logger.info(f"💾 Изображение сохранено: {filename}")
        return f"/images/posts/{os.path.basename(filename)}"
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return None

def save_image_from_url(url, topic):
    """Сохранение изображения из URL"""
    try:
        logger.info(f"📥 Загрузка из URL: {url[:80]}...")
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return save_image_bytes(response.content, topic)
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки URL: {e}")
    return None

# ======== ЗАПУСК ========
def main():
    """Основная функция запуска"""
    parser = argparse.ArgumentParser(description='Генератор AI контента для Hugo блога')
    parser.add_argument('--debug', action='store_true', help='Включить debug режим')
    parser.add_argument('--count', type=int, default=1, help='Количество статей для генерации')
    parser.add_argument('--keep', type=int, default=5, help='Сколько статей оставлять при очистке')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🔧 Debug режим включен")
    
    print("🚀 AI Генератор контента для Hugo блога")
    print("=" * 50)
    
    # Проверка переменных окружения
    check_environment_variables()
    print("=" * 50)
    
    try:
        for i in range(args.count):
            print(f"\n📄 Генерация статьи {i+1}/{args.count}...")
            filename = generate_content()
            print(f"✅ Статья создана: {filename}")
            
            # Пауза между генерациями
            if i < args.count - 1:
                time.sleep(2)
                
        print("\n🎉 Все статьи успешно сгенерированы!")
        print(f"📁 Статьи сохранены в: content/posts/")
        print(f"🖼️ Изображения в: static/images/posts/")
        
    except KeyboardInterrupt:
        print("\n⏹️ Генерация прервана пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
