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
        'EDENAI_API_KEY': os.getenv('EDENAI_API_KEY'),
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

# ======== Генерация изображения ========
EDENAI_KEY = os.getenv('EDENAI_API_KEY')

# Рабочие провайдеры (после тестирования)
WORKING_PROVIDERS = [
    "stability",  # Stability AI
    "replicate",  # Replicate
    "deepai"      # DeepAI
]

def generate_article_image(topic):
    logger.info(f"🎨 Генерация изображения по промпту: {topic}")
    
    # Сначала пробуем Eden AI если есть ключ
    if EDENAI_KEY:
        logger.info(f"🔑 Токен Eden AI: {EDENAI_KEY[:8]}...{EDENAI_KEY[-4:]}")
        edenai_result = try_edenai_providers(topic)
        if edenai_result:
            return edenai_result
    
    # Если Eden AI не сработал, используем бесплатные альтернативы
    free_result = try_free_alternatives(topic)
    if free_result:
        return free_result
    
    # Если все провайдеры не сработали, используем placeholder
    logger.warning("✅ Все провайдеры не сработали, используем placeholder")
    return generate_placeholder_image(topic)

def try_edenai_providers(topic):
    """Попытка генерации через Eden AI провайдеры"""
    prompt = topic[:150]
    
    for provider in WORKING_PROVIDERS:
        try:
            logger.info(f"🔄 Пробуем Eden AI провайдер: {provider}")
            
            payload = {
                "providers": provider, 
                "text": prompt, 
                "resolution": "512x512",
                "num_images": 1
            }
            
            start_time = time.time()
            
            resp = requests.post(
                "https://api.edenai.run/v2/image/generation",
                headers={
                    "Authorization": f"Bearer {EDENAI_KEY}", 
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30
            )
            
            response_time = time.time() - start_time
            logger.info(f"⏱️ Время ответа {provider}: {response_time:.2f} сек")
            logger.info(f"📊 Статус код: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                if provider in data and data[provider].get("status") == "success":
                    image_url = data[provider].get("url")
                    if image_url:
                        logger.info(f"✅ Получен URL изображения от {provider}")
                        filename = save_image_from_url(image_url, topic)
                        if filename:
                            return filename
            
            elif resp.status_code == 402:
                logger.error(f"❌ {provider}: Недостаточно средств на счете")
                break
                
        except Exception as e:
            logger.error(f"❌ Ошибка с {provider}: {e}")
        
        time.sleep(2)
    
    return None

def try_free_alternatives(topic):
    """Бесплатные альтернативы Eden AI"""
    prompt = topic[:150]
    
    # Hugging Face API (бесплатный)
    try:
        logger.info("🔄 Пробуем Hugging Face API")
        hf_result = try_huggingface(prompt, topic)
        if hf_result:
            return hf_result
    except Exception as e:
        logger.error(f"❌ Ошибка Hugging Face: {e}")
    
    return None

def try_huggingface(prompt, topic):
    """Попытка через Hugging Face Inference API"""
    try:
        # Пример с Stable Diffusion
        API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"}
        
        payload = {"inputs": prompt}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            filename = f"assets/images/posts/{generate_slug(topic)}.png"
            with open(filename, "wb") as f:
                f.write(response.content)
            logger.info(f"✅ Изображение создано через Hugging Face")
            return filename
            
    except Exception as e:
        logger.error(f"❌ Hugging Face API error: {e}")
    
    return None

def save_image_from_url(url, topic):
    try:
        logger.info(f"📥 Загрузка изображения из: {url[:100]}...")
        resp = requests.get(url, timeout=30)
        
        if resp.status_code == 200:
            os.makedirs("assets/images/posts", exist_ok=True)
            filename = f"assets/images/posts/{generate_slug(topic)}.png"
            
            with open(filename, "wb") as f:
                f.write(resp.content)
            
            logger.info(f"✅ Изображение сохранено: {filename}")
            return filename
        else:
            logger.error(f"❌ Ошибка загрузки изображения: статус {resp.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении изображения: {e}")
        return None

def generate_placeholder_image(topic):
    """Создание placeholder изображения"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        width, height = 800, 400
        
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        # Градиент
        for i in range(height):
            r = int(15 + (i/height)*30)
            g = int(23 + (i/height)*42)
            b = int(42 + (i/height)*74)
            draw.line([(0,i), (width,i)], fill=(r,g,b))
        
        # Текст
        wrapped_text = textwrap.fill(topic, width=30)
        try:
            font = ImageFont.truetype("Arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        x = (width - (bbox[2] - bbox[0])) / 2
        y = (height - (bbox[3] - bbox[1])) / 2
        
        draw.text((x+2, y+2), wrapped_text, font=font, fill="#000000")
        draw.text((x, y), wrapped_text, font=font, fill="#6366f1")
        
        img.save(filename)
        logger.info(f"✅ Placeholder изображение создано: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания placeholder: {e}")
        return "assets/images/default.png"

# ======== Вспомогательные функции ========
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', "'")
    
    frontmatter = f"""---
title: "{escaped_title}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
tags: ["ai", "технологии", "2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о тенденциях AI в 2025 году"
---

{content}
"""
    return frontmatter

# ======== Запуск ========
def main():
    parser = argparse.ArgumentParser(description='Генератор AI контента')
    parser.add_argument('--debug', action='store_true', help='Включить debug режим')
    parser.add_argument('--count', type=int, default=1, help='Количество статей для генерации')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🚀 Запуск генератора контента...")
    print("=" * 50)
    
    check_environment_variables()
    print("=" * 50)
    
    try:
        for i in range(args.count):
            print(f"\n📄 Генерация статьи {i+1}/{args.count}...")
            filename = generate_content()
            print(f"✅ Статья создана: {filename}")
            
            if i < args.count - 1:
                time.sleep(3)
                
        print("\n🎉 Все статьи успешно сгенерированы!")
        
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
