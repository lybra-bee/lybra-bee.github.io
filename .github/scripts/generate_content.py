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

def generate_content():
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {topic}")
    
    # Генерация изображения
    image_filename = generate_article_image(topic)
    
    # Генерация статьи
    content, model_used = generate_article_content(topic)
    
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    # Здесь можно использовать Groq и OpenRouter как раньше
    fallback_content = f"# {topic}\n\nАвтоматически сгенерированная статья о {topic}."
    return fallback_content, "fallback-generator"

# --- Генерация изображения ---
def generate_article_image(topic):
    print("🎨 Генерация изображения...")
    # Попробуем генераторы по порядку
    generators = [
        generate_image_stabilityai,
        generate_image_deepai,
        generate_image_craiyon,
        generate_image_lexica,
        generate_image_placeholder
    ]
    
    for gen in generators:
        try:
            image_url = gen(topic)
            if image_url:
                return image_url
        except Exception as e:
            print(f"⚠️ Ошибка генерации через {gen.__name__}: {e}")
    
    print("⚠️ Все генераторы не сработали, используем placeholder")
    return generate_image_placeholder(topic)

def generate_image_stabilityai(topic):
    key = os.getenv("STABILITYAI_KEY")
    if not key:
        return None
    # Пример запроса StabilityAI (как в предыдущем коде)
    return None  # Для упрощения пока пропускаем

def generate_image_deepai(topic):
    key = "98c841c4"  # твой ключ
    url = "https://api.deepai.org/api/text2img"
    headers = {"Api-Key": key}
    data = {"text": topic}
    r = requests.post(url, data=data, headers=headers, timeout=30)
    if r.status_code == 200:
        resp = r.json()
        if "output_url" in resp:
            print("✅ Изображение создано через DeepAI")
            return resp["output_url"]
    return None

def generate_image_craiyon(topic):
    url = "https://api.craiyon.com/v1/generate"
    data = {"prompt": topic}
    r = requests.post(url, json=data, timeout=30)
    if r.status_code == 200:
        resp = r.json()
        if "images" in resp:
            print("✅ Изображение создано через Craiyon")
            return resp["images"][0]
    return None

def generate_image_lexica(topic):
    # Псевдо-генератор Lexica, можно адаптировать
    return None

def generate_image_placeholder(topic):
    # Всегда возвращает нейтральную заглушку
    return "https://via.placeholder.com/1024x1024.png?text=AI+Image"

# --- Вспомогательные функции ---
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', '').replace("'", "")
    frontmatter_lines = [
        "---",
        f'title: "{escaped_title}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI","машинное обучение","технологии","2025"]',
        'categories: ["Искусственный интеллект"]',
        'summary: "Автоматически сгенерированная статья об искусственном интеллекте"'
    ]
    if image_url:
        frontmatter_lines.append(f'image: "{image_url}"')
    frontmatter_lines.append("---")
    frontmatter_lines.append(content)
    return "\n".join(frontmatter_lines)

def clean_old_articles(keep_last=3):
    try:
        articles = glob.glob("content/posts/*.md")
        articles.sort(key=os.path.getmtime, reverse=True)
        for old in articles[keep_last:]:
            os.remove(old)
    except:
        pass

if __name__ == "__main__":
    generate_content()
