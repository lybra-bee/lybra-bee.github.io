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

# Бесплатные модели Replicate
REPLICATE_FREE_MODELS = [
    {
        "name": "Google Imagen-4",
        "id": "google/imagen-4",
        "version": "a89b395af3300d5b5dac5e4a8b8f4b1c2d1c1b1a1a1a1a1a1a1a1a1a1a1a1a1",
        "prompt_template": "{topic}, digital art, futuristic, professional, 4k quality"
    },
    {
        "name": "FLUX Kontext Pro",
        "id": "black-forest-labs/flux-kontext-pro",
        "version": "b1e5c1b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "prompt_template": "{topic}, strict prompt following, style control, photorealistic"
    },
    {
        "name": "Ideogram v3 Turbo",
        "id": "ideogram-ai/ideogram-v3-turbo", 
        "version": "c1d1e1f1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "prompt_template": "{topic}, creative generation, posters, products, text included"
    },
    {
        "name": "FLUX 1.1 Pro",
        "id": "black-forest-labs/flux-1.1-pro",
        "version": "d1e1f1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1", 
        "prompt_template": "{topic}, stable quality, diverse images, enhanced FLUX"
    },
    {
        "name": "FLUX Dev",
        "id": "black-forest-labs/flux-dev",
        "version": "e1f1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "prompt_template": "{topic}, experimental, 12B parameters, edge cases"
    }
]

# ======== Генерация темы ========
def generate_ai_trend_topic():
    current_trends_2025 = [
        "Multimodal AI интеграция текста изображений и аудио в единых моделях",
        "AI агенты автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение прорыв в производительности",
        "Нейроморфные вычисления энергоэффективные архитектуры нейросетей",
        "Generative AI создание контента кода и дизайнов искусственным интеллектом",
        "Edge AI обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности предиктивная защиот угроз",
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
    
    # Генерируем изображение (пробуем разные методы)
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
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'HF_API_TOKEN': os.getenv('HF_API_TOKEN'),
        'REPLICATE_API_TOKEN': os.getenv('REPLICATE_API_TOKEN')
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

# ======== Генерация изображений ========
def generate_article_image(topic):
    """Генерация изображения через различные API"""
    logger.info(f"🎨 Генерация изображения для: {topic}")
    
    # Пробуем разные методы в порядке приоритета
    methods = [
        try_replicate_free_models,  # Новый метод - бесплатные модели Replicate
        try_lexica_art_api,
        try_craiyon_api,
        try_deepai_api,
        generate_enhanced_placeholder
    ]
    
    for method in methods:
        try:
            logger.info(f"🔄 Пробуем метод: {method.__name__}")
            result = method(topic)
            if result:
                logger.info(f"✅ Изображение создано через {method.__name__}")
                return result
        except Exception as e:
            logger.error(f"❌ Ошибка в {method.__name__}: {e}")
            continue
    
    return generate_enhanced_placeholder(topic)

def try_replicate_free_models(topic):
    """Используем бесплатные модели Replicate"""
    REPLICATE_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    if not REPLICATE_TOKEN:
        logger.warning("⚠️ Replicate токен не найден")
        return None
    
    # Перемешиваем модели для разнообразия
    random.shuffle(REPLICATE_FREE_MODELS)
    
    for model_info in REPLICATE_FREE_MODELS:
        try:
            logger.info(f"🔄 Пробуем модель: {model_info['name']}")
            
            prompt = model_info['prompt_template'].format(topic=topic)
            
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Bearer {REPLICATE_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": model_info["version"],
                    "input": {
                        "prompt": prompt,
                        "width": 512,
                        "height": 512,
                        "num_outputs": 1,
                        "num_inference_steps": 20
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                prediction_id = response.json()['id']
                logger.info(f"✅ Предсказание создано: {prediction_id}")
                
                # Ждем завершения генерации
                for attempt in range(10):
                    time.sleep(3)
                    status_response = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Bearer {REPLICATE_TOKEN}"},
                        timeout=20
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', '')
                        
                        if status == 'succeeded':
                            image_url = status_data['output'][0]
                            logger.info(f"✅ Изображение готово: {image_url}")
                            img_data = requests.get(image_url, timeout=30).content
                            return save_image_bytes(img_data, topic)
                        elif status == 'failed':
                            logger.warning(f"⚠️ Генерация не удалась: {status_data.get('error', 'Unknown error')}")
                            break
                        else:
                            logger.info(f"⏳ Статус: {status} (попытка {attempt + 1})")
                    else:
                        logger.warning(f"⚠️ Ошибка статуса: {status_response.status_code}")
                        break
            else:
                logger.warning(f"⚠️ Ошибка API: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка модели {model_info['name']}: {e}")
            continue
    
    return None

def try_lexica_art_api(topic):
    """Lexica Art API - бесплатный поиск изображений"""
    try:
        prompt = f"{topic}, digital art, futuristic"
        
        search_response = requests.get(
            f"https://lexica.art/api/v1/search?q={requests.utils.quote(prompt)}",
            timeout=20
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            if data.get('images') and len(data['images']) > 0:
                image_url = data['images'][0]['src']
                img_data = requests.get(image_url, timeout=30).content
                return save_image_bytes(img_data, topic)
                
    except Exception as e:
        logger.error(f"❌ Ошибка Lexica Art: {e}")
    
    return None

def try_craiyon_api(topic):
    """Craiyon API"""
    try:
        prompt = f"{topic}, digital art, futuristic"
        
        response = requests.post(
            "https://api.craiyon.com/generate",
            json={"prompt": prompt},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("images"):
                image_data = base64.b64decode(data["images"][0])
                return save_image_bytes(image_data, topic)
                
    except Exception as e:
        logger.error(f"❌ Ошибка Craiyon: {e}")
    
    return None

def try_deepai_api(topic):
    """DeepAI API"""
    try:
        prompt = f"{topic}, digital art, futuristic style"
        
        api_keys = ['quickstart-credential', 'demo-key', 'test-key']
        
        for api_key in api_keys:
            try:
                response = requests.post(
                    "https://api.deepai.org/api/text2img",
                    headers={'api-key': api_key},
                    data={'text': prompt},
                    timeout=25
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('output_url'):
                        img_data = requests.get(data['output_url'], timeout=30).content
                        return save_image_bytes(img_data, topic)
                        
            except:
                continue
                
    except Exception as e:
        logger.error(f"❌ Ошибка DeepAI: {e}")
    
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
        logger.error(f"❌ Ошибка сохранения изображения: {e}")
        return None

def generate_enhanced_placeholder(topic):
    """Улучшенный placeholder"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        width, height = 800, 400
        
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        # Градиентный фон
        for i in range(height):
            r = int(15 + (i/height)*40)
            g = int(23 + (i/height)*60)
            b = int(42 + (i/height)*100)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Сетка
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 25))
        for i in range(0, height, 40):
            draw.line([(0, i), (width, i)], fill=(255, 255, 255, 25))
        
        # Текст
        wrapped_text = textwrap.fill(topic, width=35)
        
        try:
            font = ImageFont.truetype("Arial.ttf", 22)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        draw.text((x+3, y+3), wrapped_text, font=font, fill="#000000")
        draw.text((x, y), wrapped_text, font=font, fill="#ffffff")
        
        draw.rectangle([(10, height-35), (120, height-10)], fill="#6366f1")
        draw.text((15, height-30), "AI GENERATED", font=ImageFont.load_default(), fill="#ffffff")
        
        img.save(filename)
        logger.info(f"🎨 Создан placeholder: {filename}")
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
        logger.info("🔧 Debug режим включен")
    
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
                time.sleep(2)
                
        print("\n🎉 Все статьи успешно сгенерированы!")
        
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
