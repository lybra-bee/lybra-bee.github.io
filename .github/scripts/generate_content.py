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

# -------------------- Настройки ключей --------------------
DEEP_AI_KEY = "98c841c4-f3dc-42b0-b02e-de2fcdebd001"

# -------------------- Генерация темы --------------------
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

# -------------------- Генерация контента статьи --------------------
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')

    models_to_try = []

    # OpenRouter модели (приоритет)
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

    # Groq модели (запасной вариант)
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

    # Перебор моделей
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

    # Fallback
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"# {topic}\n\nСтатья временно сгенерирована как заглушка."
    return fallback_content, "fallback-generator"

# -------------------- Генерация изображения через DeepAI --------------------
def generate_article_image(topic):
    print("🎨 Генерация изображения через DeepAI...")
    try:
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={'text': f"{topic}, цифровое искусство, футуристический стиль, нейросети, киберпанк"},
            headers={'api-key': DEEP_AI_KEY}
        )
        result = response.json()
        if 'output_url' in result and result['output_url']:
            image_url = result['output_url']
            print(f"✅ Изображение создано через DeepAI: {image_url}")
            return image_url
        else:
            print(f"⚠️ DeepAI вернул некорректный результат: {result}")
            return None
    except Exception as e:
        print(f"⚠️ Ошибка при генерации изображения DeepAI: {e}")
        return None

# -------------------- Вспомогательные функции --------------------
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"','').replace("'",'').replace('\\','')
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
            os.remove(article_path)
            slug = os.path.basename(article_path).replace('.md','')
            image_path = f"assets/images/posts/{slug}.png"
            if os.path.exists(image_path):
                os.remove(image_path)
    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")

# -------------------- Основной запуск --------------------
def generate_content():
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)

    topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {topic}")

    image_url = generate_article_image(topic)
    content, model_used = generate_article_content(topic)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_url)

    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
