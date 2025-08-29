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

    # Генерируем изображение через доступные сервисы
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

    # fallback
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


def generate_article_image(topic):
    """Генерация изображения через различные сервисы с перебором вариантов"""
    print("🎨 Генерация изображения...")

    stability_key = os.getenv('STABILITYAI_KEY')
    deepai_key = "98c841c4"  # твой ключ DeepAI

    image_filename = None

    # 1️⃣ Stability AI
    if stability_key:
        print("🔑 Используем Stability AI")
        image_filename = generate_image_stabilityai(topic, stability_key)
        if image_filename:
            return image_filename

    # 2️⃣ DeepAI
    if deepai_key:
        print("🔑 Используем DeepAI")
        image_filename = generate_image_deepai(topic, deepai_key)
        if image_filename:
            return image_filename

    # 3️⃣ Craiyon (бесплатно)
    print("🌐 Используем Craiyon (бесплатно)")
    image_filename = generate_image_craiyon(topic)
    if image_filename:
        return image_filename

    # 4️⃣ Lexica (бесплатно)
    print("🌐 Используем Lexica (бесплатно)")
    image_filename = generate_image_lexica(topic)
    if image_filename:
        return image_filename

    # 5️⃣ Picsum.photos (placeholder)
    print("🌐 Используем Picsum.photos как fallback")
    image_filename = generate_image_picsum(topic)
    if image_filename:
        return image_filename

    print("⚠️ Не удалось сгенерировать изображение, используем placeholder")
    return None


def generate_image_prompt(topic):
    """Генерирует промпт для изображения"""
    prompts = [
        f"Technology illustration for article about {topic}. Modern futuristic style, abstract technology concept with neural networks, AI, data visualization. Blue and purple color scheme, professional digital art, no text",
        f"AI technology concept art for {topic}. Futuristic cyberpunk style, glowing neural networks, holographic interfaces, digital particles. Dark background with vibrant colors, cinematic lighting",
        f"Abstract technology background for {topic}. Geometric shapes, circuit patterns, data streams, glowing connections. Professional corporate style, clean design, technology theme",
        f"Futuristic AI concept for {topic}. Digital brain, neural connections, data flow, quantum computing elements. Sci-fi style, vibrant colors, depth of field"
    ]
    return random.choice(prompts)


def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"posts/{slug}.png"
        full_path = f"assets/images/{filename}"
        with open(full_path, 'wb') as f:
            f.write(image_data)
        print(f"💾 Изображение сохранено: {filename}")
        return f"/images/{filename}"
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None


def generate_slug(text):
    """Создает безопасный slug из текста"""
    text = text.lower()
    text = text.replace(' ', '-').replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]


def generate_frontmatter(title, content, model_used, image_url):
    """Генерирует frontmatter для Hugo"""
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
    """Оставляет только последние N статей"""
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
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке статей: {e}")


if __name__ == "__main__":
    generate_content()
