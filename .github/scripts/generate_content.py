#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import re
import time
from openai import OpenAI

# -------------------- Настройки ключей --------------------
OPENROUTER_API_KEY = "your_openrouter_api_key"
GROQ_API_KEY = "your_groq_api_key"
DEEP_AI_KEY = "98c841c4-f3dc-42b0-b02e-de2fcdebd001"
CRAION_API_URL = "https://api.craiyon.com/v3/draw"  # URL Craiyon

client = OpenAI(api_key=OPENROUTER_API_KEY)

# -------------------- Генерация темы --------------------
def generate_ai_trend_topic():
    prompt = "Предложи одну актуальную тему для статьи 2025 года о трендах в искусственном интеллекте, кратко и ёмко"
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0.8
    )
    topic = resp.choices[0].message.content.strip()
    return topic

# -------------------- Генерация текста статьи --------------------
def generate_article_content(topic):
    models_to_try = []

    # OpenRouter API
    if OPENROUTER_API_KEY:
        print("🔑 OpenRouter API ключ найден")
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(m, topic)))

    # Groq API
    if GROQ_API_KEY:
        print("🔑 Groq API ключ найден")
        groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(m, topic)))

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

# -------------------- Генерация изображения --------------------
def generate_article_image(topic):
    print("🎨 Генерация изображения...")
    slug = generate_slug(topic)
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{slug}.png"

    # --- Попытка через Craiyon ---
    try:
        print("🔄 Пробуем генератор: Craiyon")
        payload = {
            "prompt": f"{topic}, цифровое искусство, футуристический стиль, киберпанк",
            "model": "none"
        }
        response = requests.post(CRAION_API_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            if "images" in data and data["images"]:
                image_b64 = data["images"][0]  # берём первое изображение
                image_bytes = base64.b64decode(image_b64)
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"✅ Craiyon сгенерировал изображение: {filename}")
                return f"/images/posts/{slug}.png"
        else:
            print(f"⚠️ Craiyon ответил ошибкой: {response.text}")
    except Exception as e:
        print(f"⚠️ Craiyon не сработал: {e}")

    # --- Попытка через DeepAI ---
    try:
        print("🔄 Пробуем генератор: DeepAI")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={'text': f"{topic}, цифровое искусство, футуристический стиль"},
            headers={'api-key': DEEP_AI_KEY}
        )
        result = response.json()
        if 'output_url' in result:
            img_url = result['output_url']
            img_data = requests.get(img_url).content
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"✅ DeepAI сгенерировал изображение: {filename}")
            return f"/images/posts/{slug}.png"
    except Exception as e:
        print(f"⚠️ DeepAI не сработал: {e}")

    print("⚠️ Не удалось сгенерировать изображение, используем заглушку")
    return None

# -------------------- Вспомогательные функции --------------------
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
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


if __name__ == "__main__":
    generate_content()
