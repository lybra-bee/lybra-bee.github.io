#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time
import re

# --- Настройки ключей ---
HF_TOKEN = "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"
DEEP_AI_KEY = "98c841c4"

# --- Генерация темы статьи ---
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

# --- Генерация slug ---
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:60]

# --- Генерация frontmatter ---
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

# --- Очистка старых статей ---
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
            except:
                pass
    except:
        pass

# --- Генерация изображения через Hugging Face ---
def generate_image_huggingface(topic, hf_token):
    print("🔄 Пробуем генератор: HuggingFace")
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
    prompts = [
        f"Futuristic digital illustration for article about {topic}. Clean, professional, neon colors, AI, data visualization, technology theme, no text",
        f"Cyberpunk concept art for {topic}. Neural networks, glowing holographic interfaces, futuristic city, cinematic lighting",
        f"Abstract high-tech illustration for {topic}. Geometric shapes, digital particles, circuits, futuristic style",
        f"Modern AI concept for {topic}. Digital brain, quantum computing elements, sci-fi environment, vibrant colors",
        f"Creative tech visualization for {topic}. Minimalist, professional, glowing effects, digital art style"
    ]
    payload = {"inputs": random.choice(prompts), "options":{"wait_for_model":True}}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "images" in data:
                image_bytes = base64.b64decode(data["images"][0])
                os.makedirs("assets/images/posts", exist_ok=True)
                slug = generate_slug(topic)
                filename = f"posts/{slug}.png"
                full_path = f"assets/images/{filename}"
                with open(full_path,"wb") as f: f.write(image_bytes)
                print(f"✅ Hugging Face: изображение создано: {filename}")
                return f"/images/{filename}"
        print(f"⚠️ Hugging Face не сработал: {response.status_code}")
    except Exception as e:
        print(f"❌ Hugging Face ошибка: {e}")
    return None

# --- Другие генераторы ---
def generate_image_deepai(topic):
    print("🔄 Пробуем генератор: DeepAI")
    try:
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={"text": topic},
            headers={"Api-Key": DEEP_AI_KEY},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            if "output_url" in data:
                print("✅ DeepAI успешно")
                return data["output_url"]
    except:
        pass
    print("⚠️ DeepAI вернул None")
    return None

def generate_image_craiyon(topic):
    print("🔄 Пробуем генератор: Craiyon")
    try:
        response = requests.post(
            "https://backend.craiyon.com/generate",
            json={"prompt": topic},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            if "images" in data and data["images"]:
                print("✅ Craiyon успешно")
                return data["images"][0]
    except:
        pass
    print("⚠️ Craiyon вернул None")
    return None

def generate_image_lexica(topic):
    print("🔄 Пробуем генератор: Lexica")
    try:
        # Заглушка, так как Lexica публичного API нет
        return None
    except:
        return None

def generate_image_artbreeder(topic):
    print("🔄 Пробуем генератор: Artbreeder")
    try:
        # Заглушка, можно подключить через web scraping или их API если есть
        return f"https://placehold.co/1024x1024?text=AI+{topic}"
    except:
        return None

# --- Основная функция генерации изображения ---
def generate_article_image(topic):
    generators = [
        lambda: generate_image_huggingface(topic, HF_TOKEN),
        lambda: generate_image_deepai(topic),
        lambda: generate_image_craiyon(topic),
        lambda: generate_image_lexica(topic),
        lambda: generate_image_artbreeder(topic)
    ]
    for gen in generators:
        img = gen()
        if img:
            return img
    print("⚠️ Не удалось сгенерировать изображение ни одним генератором")
    return None

# --- Генерация статьи через OpenRouter/Groq ---
def generate_article_content(topic):
    # Здесь оставляем как было: OpenRouter в приоритете, Groq запасной
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if openrouter_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct"
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    if groq_key:
        groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))

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

# Заглушки для генерации через OpenRouter/Groq
def generate_with_openrouter(api_key, model_name, topic): return f"Статья по теме {topic}", model_name
def generate_with_groq(api_key, model_name, topic): return f"Статья по теме {topic}", model_name

# --- Основная функция ---
def generate_content():
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")

    # Генерация изображения
    image_filename = generate_article_image(selected_topic)

    # Генерация статьи
    content, model_used = generate_article_content(selected_topic)

    # Создание файла
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_filename)
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
