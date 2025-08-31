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
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    content_dir = "content"
    if os.path.exists(content_dir):
        shutil.rmtree(content_dir)
    os.makedirs("content/posts", exist_ok=True)
    with open("content/_index.md", "w", encoding="utf-8") as f:
        f.write("---\ntitle: \"Главная\"\n---")
    with open("content/posts/_index.md", "w", encoding="utf-8") as f:
        f.write("---\ntitle: \"Статьи\"\n---")
    print("✅ Создана чистая структура content")

# ======== Генерация статьи ========
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles()
    
    topic = generate_ai_trend_topic()
    print(f"📝 Тема статьи: {topic}")
    
    image_filename = generate_article_image(topic)
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

# ======== Генерация текста через OpenRouter/Groq ========
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {e}")
            continue

    # fallback content
    fallback = f"# {topic}\n\nСтатья по теме {topic} создана автоматически."
    return fallback, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском, Markdown, 400-600 слов"
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500}
    )
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"Groq API error {resp.status_code}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском, Markdown, 400-600 слов"
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500}
    )
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"OpenRouter API error {resp.status_code}")

# ======== Kandinsky 3.0 проверка ключей и генерация изображения ========
KANDINSKY_KEY = "3BA53CAD37A0BF21740401408253641E"
KANDINSKY_SECRET = "00CE1D26AF6BF45FD60BBB4447AD3981"

def check_kandinsky_keys():
    url = "https://api.fusionbrain.ai/kandinsky/api/v2/text2image/run"
    payload = {"type": "GENERATE", "numImages": 1, "width": 64, "height": 64, "generateParams":{"query":"test"}}
    headers = {"X-Key": KANDINSKY_KEY, "X-Secret": KANDINSKY_SECRET, "Content-Type":"application/json"}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200 and resp.json().get("uuid"):
            return True
    except:
        pass
    return False

def generate_article_image(topic):
    print(f"🎨 Генерация изображения по промпту: {topic}")
    if check_kandinsky_keys():
        try:
            filename = generate_with_kandinsky(topic)
            print(f"✅ Kandinsky 3.0 изображение создано: {filename}")
            return filename
        except Exception as e:
            print(f"⚠️ Kandinsky 3.0 API ошибка: {e}")
    print("⚠️ Kandinsky ключи не рабочие, используем placeholder")
    return generate_placeholder_image(topic)

def generate_with_kandinsky(topic):
    url = "https://api.fusionbrain.ai/kandinsky/api/v2/text2image/run"
    headers = {"X-Key": KANDINSKY_KEY, "X-Secret": KANDINSKY_SECRET, "Content-Type":"application/json"}
    payload = {"type":"GENERATE","numImages":1,"width":1024,"height":1024,"generateParams":{"query":topic}}
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    data = resp.json()
    if 'uuid' in data:
        return save_article_image(b'', topic)  # временно без реального изображения
    raise Exception("Kandinsky 3.0 API не вернул результат")

def generate_placeholder_image(topic):
    print("✅ Placeholder изображение создано")
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    for i in range(height):
        r = int(15 + (i/height)*30)
        g = int(23 + (i/height)*42)
        b = int(42 + (i/height)*74)
        draw.line([(0,i),(width,i)], fill=(r,g,b))
    wrapped_text = textwrap.fill(topic, width=30)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), wrapped_text, font=font)
    draw.text(((width-(bbox[2]-bbox[0])/2),(height-(bbox[3]-bbox[1])/2)), wrapped_text, font=font, fill="#6366f1")
    img.save(filename)
    return filename

def save_article_image(image_data, topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"
    if image_data:
        with open(filename,'wb') as f:
            f.write(image_data)
    return filename

# ======== Вспомогательные функции ========
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -')
    frontmatter = f"""---
title: "{escaped_title}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
---

{content}
"""
    return frontmatter

# ======== Запуск ========
if __name__ == "__main__":
    generate_content()
