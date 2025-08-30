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
OPENAI_API_KEY = "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"
DEEP_AI_KEY = "98c841c4-f3dc-42b0-b02e-de2fcdebd001"

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
    prompt = f"Напиши развёрнутую статью для блога на русском языке по теме: {topic}. Длина статьи не менее 300 слов, структурированная, информативная."
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7
    )
    content = resp.choices[0].message.content.strip()
    return content, "OpenAI GPT-4"

# -------------------- Генерация изображения --------------------
def generate_article_image(topic):
    print("🎨 Генерация изображения...")
    try:
        prompt = f"{topic}, цифровое искусство, футуристический стиль, нейросети, киберпанк"
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
        if response.data and response.data[0].b64_json:
            image_bytes = base64.b64decode(response.data[0].b64_json)
            os.makedirs("assets/images/posts", exist_ok=True)
            slug = generate_slug(topic)
            filename = f"assets/images/posts/{slug}.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Изображение создано через GPT Image 1: {filename}")
            return f"/images/posts/{slug}.png"
    except Exception as e:
        print(f"⚠️ GPT Image 1 не сработал: {e}")

    try:
        print("🔄 Пробуем генератор: DeepAI")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={'text': f"{topic}, цифровое искусство, футуристический стиль"},
            headers={'api-key': DEEP_AI_KEY}
        )
        result = response.json()
        if 'output_url' in result:
            print(f"✅ DeepAI сгенерировал изображение: {result['output_url']}")
            return result['output_url']
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
