#!/usr/bin/env python3
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ======== Генерация темы ========
def generate_ai_trend_topic():
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
def clean_old_articles(keep_last=3):
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    content_dir = "content"
    if os.path.exists(content_dir):
        # Удаляем только старые файлы, оставляя последние keep_last
        posts_dir = os.path.join(content_dir, "posts")
        if os.path.exists(posts_dir):
            posts = sorted([f for f in os.listdir(posts_dir) if f.endswith('.md')], 
                          reverse=True)
            for post in posts[keep_last:]:
                os.remove(os.path.join(posts_dir, post))
                logger.info(f"🗑️ Удален старый пост: {post}")
    else:
        os.makedirs("content/posts", exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        logger.info("✅ Создана структура content")

# ======== Генерация статьи ========
def generate_content():
    logger.info("🚀 Запуск генерации контента...")
    
    # Проверка переменных окружения
    check_environment_variables()
    
    clean_old_articles()
    
    topic = generate_ai_trend_topic()
    logger.info(f"📝 Тема статьи: {topic}")
    
    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)
    
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    logger.info(f"✅ Статья создана: {filename}")
    return filename

def check_environment_variables():
    """Проверка всех необходимых переменных окружения"""
    env_vars = {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY')
    }
    
    logger.info("🔍 Проверка переменных окружения:")
    for var_name, var_value in env_vars.items():
        status = "✅ установлен" if var_value else "❌ отсутствует"
        logger.info(f"   {var_name}: {status}")

# ======== Генерация текста через OpenRouter/Groq ========
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview", "llama-3.1-70b-versatile"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku", "anthropic/claude-3-sonnet", "google/gemini-pro-1.5"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    # Если нет API ключей, используем fallback
    if not models_to_try:
        logger.warning("⚠️ Нет доступных API ключей для генерации текста")
        fallback = generate_fallback_content(topic)
        return fallback, "fallback-generator"

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
        "",
        "## Основные тенденции",
        "- Автоматизация процессов разработки",
        "- Интеграция AI в существующие workflow",
        "- Улучшение качества и скорости разработки",
        "",
        "## Практическое применение",
        "Компании внедряют AI решения для оптимизации своих процессов.",
        "",
        "## Заключение",
        "Будущее выглядит promising с развитием AI технологий.",
        "",
        "*Статья сгенерирована автоматически*"
    ]
    return "\n".join(sections)

def generate_with_groq(api_key, model_name, topic):
    prompt = f"""Напиши развернутую статью на тему: '{topic}' на русском языке.

Требования:
- Формат Markdown
- 400-600 слов
- Структура: введение, основные разделы, заключение
- Профессиональный стиль
- Конкретные примеры и кейсы
"""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_name, 
            "messages":[{"role":"user","content":prompt}], 
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

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"""Напиши развернутую статью на тему: '{topic}' на русском языке.

Требования:
- Формат Markdown
- 400-600 слов
- Структурированный контент с заголовками
- Практические примеры
- Профессиональный тон
"""
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-content-generator.com",
            "X-Title": "AI Content Generator"
        },
        json={
            "model": model_name, 
            "messages":[{"role":"user","content":prompt}], 
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

# ======== БЕСПЛАТНАЯ Генерация изображений ========
def generate_article_image(topic):
    """Генерация изображения через проверенные бесплатные API"""
    logger.info(f"🎨 Генерация изображения по промпту: {topic}")
    
    prompt = f"{topic}, digital art, futuristic, AI technology, 4k, high quality, trending"
    
    # Самые надежные бесплатные API (проверенные)
    reliable_apis = [
        try_craiyon,            # Craiyon (DALL-E mini) - самый надежный
        try_deepai_public,      # DeepAI с публичным ключом
        try_huggingface_public, # Hugging Face публичные модели
        try_quickai,           # QuickAI
        try_proxyfusion,       # ProxyFusion
        try_openart,           # OpenArt
        try_local_sd,          # Локальная генерация через API
        try_stability_public   # Stability AI публичный
    ]
    
    # Пробуем самые надежные варианты
    for api_func in reliable_apis:
        try:
            logger.info(f"🔄 Пробуем {api_func.__name__}")
            result = api_func(prompt[:150], topic)
            if result:
                logger.info(f"✅ Успешно через {api_func.__name__}")
                return result
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Ошибка в {api_func.__name__}: {e}")
            continue
    
    # Если все API не сработали, используем улучшенный placeholder
    logger.warning("✅ Все API не сработали, используем улучшенный placeholder")
    return generate_enhanced_placeholder(topic)

def try_craiyon(prompt, topic):
    """Craiyon (бывший DALL-E mini) - самый надежный бесплатный"""
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
                # Декодируем первую картинку из base64
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
        # Пробуем разные модели
        models = [
            "runwayml/stable-diffusion-v1-5",
            "stabilityai/stable-diffusion-2-1",
            "prompthero/openjourney-v4"
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

def try_quickai(prompt, topic):
    """QuickAI API"""
    try:
        logger.info("🎨 QuickAI генерация...")
        response = requests.post(
            "https://api.quickai.io/api/v1/generate",
            json={"prompt": prompt, "size": "512x512"},
            timeout=20
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("image"):
                image_data = base64.b64decode(data["image"])
                return save_image_bytes(image_data, topic)
    except Exception as e:
        logger.error(f"❌ QuickAI error: {e}")
    return None

def try_proxyfusion(prompt, topic):
    """ProxyFusion API"""
    try:
        logger.info("🎨 ProxyFusion генерация...")
        response = requests.post(
            "https://api.proxyfusion.ai/generate",
            json={"prompt": prompt, "width": 512, "height": 512},
            timeout=20
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("image_url"):
                return save_image_from_url(data["image_url"], topic)
    except Exception as e:
        logger.error(f"❌ ProxyFusion error: {e}")
    return None

def try_openart(prompt, topic):
    """OpenArt API"""
    try:
        logger.info("🎨 OpenArt генерация...")
        response = requests.post(
            "https://api.openart.ai/v1/generate",
            json={"prompt": prompt, "width": 512, "height": 512},
            timeout=20
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("image_url"):
                return save_image_from_url(data["image_url"], topic)
    except Exception as e:
        logger.error(f"❌ OpenArt error: {e}")
    return None

def try_local_sd(prompt, topic):
    """Локальная Stable Diffusion через публичные API"""
    try:
        logger.info("🎨 Локальная SD генерация...")
        # Публичные Stable Diffusion API
        endpoints = [
            "https://stablediffusionapi.com/api/v3/text2img",
            "https://api.stability.ai/v1/generation/stable-diffusion-512-v2-1/text-to-image"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    json={"prompt": prompt, "width": 512, "height": 512},
                    timeout=25
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("output"):
                        return save_image_from_url(data["output"][0], topic)
                    elif data.get("artifacts"):
                        image_data = base64.b64decode(data["artifacts"][0]["base64"])
                        return save_image_bytes(image_data, topic)
            except:
                continue
    except Exception as e:
        logger.error(f"❌ Local SD error: {e}")
    return None

def try_stability_public(prompt, topic):
    """Stability AI публичный доступ"""
    try:
        logger.info("🎨 Stability AI генерация...")
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-5/text-to-image",
            headers={"Authorization": "Bearer sk-public-demo"},  # Публичный демо-ключ
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 512,
                "width": 512,
                "samples": 1,
                "steps": 30
            },
            timeout=25
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("artifacts"):
                image_data = base64.b64decode(data["artifacts"][0]["base64"])
                return save_image_bytes(image_data, topic)
    except Exception as e:
        logger.error(f"❌ Stability AI error: {e}")
    return None

def save_image_bytes(image_data, topic):
    """Сохранение изображения из bytes"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        
        with open(filename, "wb") as f:
            f.write(image_data)
        
        logger.info(f"💾 Изображение сохранено: {filename}")
        return filename
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

def generate_enhanced_placeholder(topic):
    """Улучшенный placeholder с AI-стилем"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        width, height = 800, 400
        
        # Создаем футуристический фон
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        # Создаем градиентный фон с AI-стилем
        for i in range(height):
            # Сине-фиолетовый градиент
            r = int(15 + (i/height)*40)
            g = int(23 + (i/height)*60)
            b = int(42 + (i/height)*100)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Добавляем сетку (tech grid effect)
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 25))
        for i in range(0, height, 40):
            draw.line([(0, i), (width, i)], fill=(255, 255, 255, 25))
        
        # Текст
        wrapped_text = textwrap.fill(topic, width=35)
        
        # Пробуем разные шрифты
        try:
            font = ImageFont.truetype("Arial.ttf", 22)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
        
        # Рассчитываем позицию текста
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        # Тень текста
        draw.text((x+3, y+3), wrapped_text, font=font, fill="#000000")
        # Основной текст
        draw.text((x, y), wrapped_text, font=font, fill="#ffffff")
        
        # Добавляем AI badge
        draw.rectangle([(10, height-35), (120, height-10)], fill="#6366f1")
        draw.text((15, height-30), "AI 
