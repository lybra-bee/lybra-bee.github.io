#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import time
import urllib.parse

# Проверяем PIL
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None
    print("⚠️ PIL не установлен. Placeholder изображения будут ограничены.")

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

def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        content_dir = "content"
        if os.path.exists(content_dir):
            shutil.rmtree(content_dir)
        os.makedirs("content/posts", exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        print("✅ Создана чистая структура content")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")

def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles()
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Тема статьи: {selected_topic}")
    image_filename = generate_article_image(selected_topic)
    content, model_used = generate_article_content(selected_topic)
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
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []
    if groq_key:
        groq_models = ["llama-3.1-8b-instant","llama-3.2-1b-preview"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku","meta-llama/llama-3-8b-instruct"]
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
{topic} - ключевое направление в AI 2025.

## Основные аспекты
- Технологические инновации
- Практическое применение
- Перспективы развития

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта.
"""
    return fallback_content, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши развернутую статью на тему: {topic} (технический стиль, русский язык)"
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type": "application/json","Authorization": f"Bearer {api_key}"},
        json={"model": model_name,"messages":[{"role":"user","content":prompt}],"max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"Groq API ошибка {response.status_code}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши статью на тему: {topic} (технический стиль, русский язык)"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type": "application/json","Authorization": f"Bearer {api_key}"},
        json={"model": model_name,"messages":[{"role":"user","content":prompt}],"max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"OpenRouter API ошибка {response.status_code}")

def generate_article_image(topic):
    print(f"🎨 Генерация изображения по промпту: {topic}")
    # Если есть PIL
    if Image:
        try:
            width, height = 800, 400
            img = Image.new('RGB', (width, height), color='#0f172a')
            draw = ImageDraw.Draw(img)
            for i in range(height):
                r = int(15 + (i / height) * 30)
                g = int(23 + (i / height) * 42)
                b = int(42 + (i / height) * 74)
                draw.line([(0, i), (width, i)], fill=(r, g, b))
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            wrapped_text = topic[:50]
            draw.text((20, height//2 - 12), wrapped_text, font=font, fill="#6366f1")
            os.makedirs("assets/images/posts", exist_ok=True)
            slug = generate_slug(topic)
            filename = f"assets/images/posts/{slug}.png"
            img.save(filename)
            print(f"✅ Placeholder изображение создано: {filename}")
            return f"/images/posts/{slug}.png"
        except Exception as e:
            print(f"⚠️ Ошибка генерации placeholder: {e}")
    return None

def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = [
        "---",
        f'title: "{title}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI", "машинное обучение", "технологии", "2025"]',
        'categories: ["Искусственный интеллект"]',
        'summary: "Автоматически сгенерированная статья об AI"'
    ]
    if image_url:
        frontmatter.append(f'image: "{image_url}"')
    frontmatter.append("---")
    frontmatter.append(content)
    return "\n".join(frontmatter)

if __name__ == "__main__":
    generate_content()
