#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import logging
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ======== Настройка логирования ========
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

# ======== Проверка переменных окружения ========
def check_environment_variables():
    env_vars = {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'EDENAI_API_KEY': os.getenv('EDENAI_API_KEY')
    }
    logger.info("🔍 Проверка переменных окружения:")
    for var_name, var_value in env_vars.items():
        status = "✅ установлен" if var_value else "❌ отсутствует"
        logger.info(f"   {var_name}: {status}")

# ======== Генерация статьи ========
def generate_content():
    logger.info("🚀 Запуск генерации контента...")
    check_environment_variables()

    topic = generate_ai_trend_topic()
    logger.info(f"📝 Тема: {topic}")

    # Генерация изображения через Eden AI
    image_filename = generate_article_image(topic)

    # Генерация текста через OpenRouter/Groq
    content, model_used = generate_article_content(topic)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    os.makedirs("content/posts", exist_ok=True)
    filename = f"content/posts/{date}-{slug}.md"

    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    logger.info(f"✅ Статья создана: {filename}")
    return filename

def generate_frontmatter(topic, content, model_used, image_filename):
    return f"""---
title: "{topic}"
date: "{datetime.now(timezone.utc).isoformat()}"
model: "{model_used}"
image: "{image_filename}"
---
{content}
"""

def generate_slug(text):
    import re
    text = text.lower().replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:60]

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
        except Exception as e:
            logger.error(f"❌ Ошибка {model_name}: {e}")
            continue

    logger.warning("⚠️ Все модели не сработали, используем fallback")
    fallback = generate_fallback_content(topic)
    return fallback, "fallback-generator"

def generate_fallback_content(topic):
    sections = [
        f"# {topic}",
        "",
        "## Введение",
        f"Тема '{topic}' становится increasingly important в 2025 году.",
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
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском языке.\nФормат Markdown, 400-600 слов, структурированный контент"
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":2000},
        timeout=30
    )
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"Groq API error {resp.status_code}: {resp.text}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском языке.\nФормат Markdown, 400-600 слов, структурированный контент"
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":2000},
        timeout=30
    )
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"OpenRouter API error {resp.status_code}: {resp.text}")

# ======== Генерация изображения через Eden AI ========
EDENAI_KEY = os.getenv("EDENAI_API_KEY")
EDENAI_PROVIDERS = ["deepai", "openai", "stabilityai", "replicate"]

def generate_article_image(topic):
    logger.info(f"🎨 Генерация изображения: {topic}")
    if not EDENAI_KEY:
        logger.warning("⚠️ Eden AI ключ не установлен — используем placeholder")
        return generate_placeholder_image(topic)

    headers = {"Authorization": f"Bearer {EDENAI_KEY}", "Content-Type": "application/json"}
    prompt = f"{topic}, digital art, futuristic, AI technology, 4k, high quality, trending"

    for provider in EDENAI_PROVIDERS:
        payload = {"providers": [provider], "text": prompt, "resolution": "1024x1024"}
        try:
            resp = requests.post("https://api.edenai.run/v2/image/generation", headers=headers, json=payload, timeout=60)
            data = resp.json()
            if resp.status_code == 200 and "result" in data and data["result"]:
                image_url = data["result"][0].get("url")
                if image_url:
                    return save_image_from_url(image_url, topic)
            else:
                logger.warning(f"⚠ Eden AI ({provider}) не сработал: {data}")
        except Exception as e:
            logger.error(f"❌ Eden AI ошибка через {provider}: {e}")

    logger.warning("⚠ Все провайдеры Eden AI не сработали — используем placeholder")
    return generate_placeholder_image(topic)

def save_image_from_url(url, topic):
    import requests
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            logger.info(f"💾 Изображение сохранено: {filename}")
            return filename
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки URL: {e}")
    return generate_placeholder_image(topic)

def generate_placeholder_image(topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    for i in range(height):
        r = int(15 + (i/height)*40)
        g = int(23 + (i/height)*60)
        b = int(42 + (i/height)*100)
        draw.line([(0,i),(width,i)], fill=(r,g,b))
    wrapped_text = textwrap.fill(topic, width=35)
    try:
        font = ImageFont.truetype("Arial.ttf", 22)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), wrapped_text, font=font)
    draw.text(((width-(bbox[2]-bbox[0])/2),(height-(bbox[3]-bbox[1])/2)), wrapped_text, font=font, fill="#ffffff")
    img.save(filename)
    logger.info(f"✅ Placeholder изображение создано: {filename}")
    return filename

# ======== Запуск генерации ========
if __name__ == "__main__":
    generate_content()
