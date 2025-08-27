#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time

def get_gigachat_token():
    client_id = os.getenv('GIGACHAT_CLIENT_ID')
    client_secret = os.getenv('GIGACHAT_CLIENT_SECRET')
    if not client_id or not client_secret:
        print("❌ GIGACHAT_CLIENT_ID или GIGACHAT_CLIENT_SECRET не найдены")
        return None
    auth_string = f"{client_id}:{client_secret}"
    auth_key = base64.b64encode(auth_string.encode()).decode()
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": f"rq-{random.randint(100000, 999999)}-{int(time.time())}",
        "Authorization": f"Basic {auth_key}"
    }
    data = {"scope": "GIGACHAT_API_PERS"}
    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"❌ Ошибка получения токена GigaChat: {e}")
    return None

def generate_ai_trend_topic():
    trends = [
        "Multimodal AI", "AI агенты", "Квантовые вычисления и ML",
        "Нейроморфные вычисления", "Generative AI", "Edge AI",
        "AI для кибербезопасности", "Этичный AI", "AI в healthcare",
        "Автономные системы", "AI оптимизация", "Доверенный AI",
        "AI для климата", "Персональные AI ассистенты", "AI в образовании"
    ]
    domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес-аналитике",
        "в компьютерной безопасности и киберзащите",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях и EdTech"
    ]
    trend = random.choice(trends)
    domain = random.choice(domains)
    formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    return random.choice(formats)

def generate_slug(topic):
    slug = topic.lower()
    replacements = {' ': '-', ':': '', '(': '', ')': '', '/': '-', '\\': '-', '.': '', ',': '', '--': '-'}
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug[:50]

def clean_old_articles(keep_last=3):
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime)
    for f in articles[:-keep_last]:
        os.remove(f)

def save_article_image(image_data, topic):
    os.makedirs("static/images/posts", exist_ok=True)
    slug = generate_slug(topic)
    filename = f"images/posts/{slug}.jpg"  # путь для frontmatter без начального /
    full_path = f"static/{filename}"
    with open(full_path, 'wb') as f:
        f.write(image_data)
    return filename

def generate_frontmatter(topic, content, model_used, image_filename=None):
    current_time = datetime.utcnow()
    tags = ["искусственный-интеллект", "технологии", "инновации", "2025", "ai"]
    image_line = f"image: {image_filename}\n" if image_filename else ""
    return f"""---
title: "{topic}"
date: {current_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
description: "Автоматически сгенерированная статья о {topic}"
{image_line}tags: {json.dumps(tags, ensure_ascii=False)}
categories: ["Технологии"]
---

# {topic}

{f'![]({image_filename})' if image_filename else ''}

{content}

---

### 🔧 Технические детали

- **Модель AI:** {model_used}
- **Дата генерации:** {current_time.strftime("%d.%m.%Y %H:%M UTC")}
- **Тема:** {topic}
- **Год актуальности:** 2025
- **Статус:** Чистая AI генерация

> *Сгенерировано автоматически через GitHub Actions*
"""

def generate_content():
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    topic = generate_ai_trend_topic()
    slug = generate_slug(topic)
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"content/posts/{date}-{slug}.md"

    # Здесь можно вызвать функции генерации контента и изображения через OpenRouter / Stability
    content = f"Техническая статья по теме {topic}.\n\n(контент AI)"
    model_used = "OpenRouter / Stability AI"
    
    # Генерация изображения (можно закомментировать, если кредиты закончились)
    # image_filename = save_article_image(b"", topic)  # пустое изображение заглушка
    image_filename = None

    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    try:
        generate_content()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        exit(1)
