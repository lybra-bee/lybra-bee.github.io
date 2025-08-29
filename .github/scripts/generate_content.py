#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time
import urllib.parse
import re

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе реальных трендов AI 2025"""
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

def generate_content():
    """Генерирует контент статьи через AI API"""
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    # Генерируем изображение через все доступные генераторы
    image_filename = generate_article_image(selected_topic)
    
    # Генерируем текст статьи
    content, model_used = generate_article_content(selected_topic)
    
    # Создаем файл статьи
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

# --------------------- Генерация статьи --------------------- #

def generate_article_content(topic):
    """Генерация содержания статьи через доступные API"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    models_to_try = []
    
    if groq_key:
        print("🔑 Groq API ключ найден")
        groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    
    if openrouter_key:
        print("🔑 OpenRouter API ключ найден")
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro", 
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))
    
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue
    
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы

## Технические детали
Модели искусственного интеллекта для {topic} используют современные архитектуры нейросетей.

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта.
"""
    return fallback_content, "fallback-generator"

# --------------------- Генераторы изображений --------------------- #

def generate_article_image(topic):
    """Генерирует изображение через несколько API, возвращает первый удачный результат"""
    print("🎨 Генерация изображения...")
    
    generators = [
        ("StabilityAI", lambda: generate_image_stabilityai(topic, os.getenv("STABILITYAI_KEY"))),
        ("DeepAI", lambda: generate_image_deepai(topic, "98c841c4")),
        ("Craiyon", lambda: generate_image_craiyon(topic)),
        ("Lexica", lambda: generate_image_lexica(topic)),
        ("Picsum", lambda: generate_image_picsum(topic))
    ]
    
    for name, func in generators:
        try:
            image_filename = func()
            if image_filename:
                print(f"✅ Изображение создано через {name}")
                return image_filename
        except Exception as e:
            print(f"⚠️ {name} не сработал: {str(e)[:150]}")
            continue
    
    print("⚠️ Все генераторы не сработали, используем placeholder")
    return generate_image_picsum(topic)

# --- Каждый генератор --- #

def generate_image_stabilityai(topic, key):
    if not key:
        return None
    prompt = f"{topic}, futuristic, digital art, professional style, no text"
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    payload = {
        "text_prompts": [{"text": prompt, "weight": 1.0}],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30,
        "style_preset": "digital-art"
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code == 200:
        data = r.json()
        if "artifacts" in data and data["artifacts"]:
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            return save_article_image(image_data, topic)
    return None

def generate_image_deepai(topic, key):
    prompt = f"{topic}, futuristic, digital art, professional style, no text"
    url = "https://api.deepai.org/api/text2img"
    headers = {"Api-Key": key}
    r = requests.post(url, headers=headers, data={"text": prompt}, timeout=60)
    if r.status_code == 200:
        data = r.json()
        if "output_url" in data:
            image_url = data["output_url"]
            image_data = requests.get(image_url).content
            return save_article_image(image_data, topic)
    return None

def generate_image_craiyon(topic):
    prompt = f"{topic}, futuristic, digital art"
    url = "https://backend.craiyon.com/generate"
    r = requests.post(url, json={"prompt": prompt}, timeout=60)
    if r.status_code == 200:
        data = r.json()
        if "images" in data and data["images"]:
            image_data = base64.b64decode(data["images"][0])
            return save_article_image(image_data, topic)
    return None

def generate_image_lexica(topic):
    prompt = urllib.parse.quote(topic)
    url = f"https://lexica.art/api/v1/search?q={prompt}"
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        data = r.json()
        if "images" in data and data["images"]:
            image_url = data["images"][0]["src"]
            image_data = requests.get(image_url).content
            return save_article_image(image_data, topic)
    return None

def generate_image_picsum(topic):
    """Placeholder генератор через Picsum"""
    url = "https://picsum.photos/1024"
    image_data = requests.get(url).content
    return save_article_image(image_data, topic)

# --------------------- Общие функции --------------------- #

def save_article_image(image_data, topic):
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"posts/{slug}.png"
        full_path = f"assets/images/{filename}"
        with open(full_path, 'wb') as f:
            f.write(image_data)
        return f"/images/{filename}"
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-').replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', '').replace("'", "").replace('\\', '')
    frontmatter_lines = [
        "---",
        f'title: "{escaped_title}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI", "машинное обучение", "технологии", "2025"]',
        'categories: ["Искусственный интеллект"]',
        'summary: "Автоматически сгенерированная статья об искусственном интеллекте"'
    ]
    if image_url:
        frontmatter_lines.append(f'image: "{image_url}"')
    frontmatter_lines.append("---")
    frontmatter_lines.append(content)
    return "\n".join(frontmatter_lines)

def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles:
            print("📁 Нет статей для очистки")
            return
        articles.sort(key=os.path.getmtime, reverse=True)
        articles_to_keep = articles[:keep_last]
        articles_to_delete = articles[keep_last:]
        for article_path in articles_to_delete:
            try:
                os.remove(article_path)
                slug = os.path.basename(article_path).replace('.md', '')
                image_path = f"assets/images/posts/{slug}.png"
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception:
                continue
    except Exception:
        pass

# --------------------- Генерация через API Groq/OpenRouter --------------------- #

def generate_with_groq(api_key, model_name, topic):
    prompt = f"""Напиши техническую статью на тему: "{topic}". Markdown, 400-600 слов, русский язык, для разработчиков, 2025"""
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"""Напиши техническую статью на тему: "{topic}". Markdown, 400-600 слов, русский язык, для разработчиков, 2025"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

if __name__ == "__main__":
    generate_content()
