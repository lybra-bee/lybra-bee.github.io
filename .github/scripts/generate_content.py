#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import re
from openai import OpenAI

# -------------------- Настройки ключей --------------------
OPENAI_API_KEY = "your-openai-api-key"  # Этот ключ всё ещё может быть у вас на месте
DEEP_AI_KEY = "98c841c4-f3dc-42b0-b02e-de2fcdebd001"

# Подтягиваем ключи из секретов GitHub
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Получаем OpenRouter API ключ из GitHub Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Получаем Groq API ключ из GitHub Secrets

CRAION_API_URL = "https://api.craiyon.com/generate"  # Craiyon endpoint

client = OpenAI(api_key=OPENAI_API_KEY)

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

    # OpenRouter модели (приоритет)
    if OPENROUTER_API_KEY:
        print("🔑 OpenRouter API ключ найден")
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro", 
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(OPENROUTER_API_KEY, m, topic)))

    # Groq модели (запасной вариант)
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
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(GROQ_API_KEY, m, topic)))

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

    # Попытка генерации изображения через Craiyon
    try:
        print("🔄 Пробуем генератор: Craiyon (DALL·E Mini)")
        response = requests.post(
            CRAION_API_URL,
            json={"prompt": f"{topic}, цифровое искусство, футуристический стиль, нейросети, киберпанк"},
        )
        response.raise_for_status()
        result = response.json()
        if result and 'images' in result:
            image_url = result['images'][0]  # Первое сгенерированное изображение
            image_response = requests.get(image_url)
            image_bytes = image_response.content
            os.makedirs("assets/images/posts", exist_ok=True)
            slug = generate_slug(topic)
            filename = f"assets/images/posts/{slug}.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Изображение создано через Craiyon: {filename}")
            return f"/images/posts/{slug}.png"
    except Exception as e:
        print(f"⚠️ Craiyon не сработал: {e}")

    # Попытка генерации изображения через DeepAI
    try:
        print("🔄 Пробуем генератор: DeepAI")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={'text': f"{topic}, цифровое искусство, футуристический стиль"},
            headers={'api-key': DEEP_AI_KEY}
        )
        response.raise_for_status()
        result = response.json()
        if 'output_url' in result:
            print(f"✅ DeepAI сгенерировал изображение: {result['output_url']}")
            image_response = requests.get(result['output_url'])
            image_bytes = image_response.content
            os.makedirs("assets/images/posts", exist_ok=True)
            slug = generate_slug(topic)
            filename = f"assets/images/posts/{slug}.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            return f"/images/posts/{slug}.png"
    except Exception as e:
        print(f"⚠️ DeepAI не сработал: {e}")

    # Если оба генератора не сработали, возвращаем заглушку
    print("⚠️ Не удалось сгенерировать изображение, используем заглушку")
    return "/images/posts/default.png"

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
