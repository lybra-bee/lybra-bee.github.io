#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, requests, base64, random
from datetime import datetime, timezone
import glob

# Конфиги
NEWS_DIR = "content/news"
IMG_DIR = "static/images/news"

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Убедиться, что нужные директории есть
os.makedirs(NEWS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def get_topic():
    prompt = (
        "Сгенерируй короткий заголовок (до 8 слов) на русском про "
        "самые свежие тренды в мире искусственного интеллекта и высоких технологий 2025."
    )
    for fn, key in [("Groq", GROQ_KEY), ("OpenRouter", OPENROUTER_KEY)]:
        if key:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions" if fn == "Groq" else "https://openrouter.ai/api/v1/chat/completions"
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": "llama-3.1-8b-instant" if fn=="Groq" else "anthropic/claude-3-haiku",
                          "messages":[{"role":"user","content":prompt}],
                          "max_tokens":50},
                    timeout=30
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"].splitlines()[0].strip()
                if content:
                    print(f"Тема получена через {fn}: {content}")
                    return content
            except Exception as e:
                print(f"Ошибка {fn} при генерации темы: {e}")
    fallback = random.choice([
        "ИИ-агенты для бизнеса 2025", "AI для медицины и биотеха", "Мультимодальные модели на грани революции"
    ])
    print(f"Fallback тема: {fallback}")
    return fallback

def get_article(topic):
    prompt = (
        f"Напиши техническую статью на русском (400–600 слов, Markdown) "
        f"на тему: {topic}. Для разработчиков, с примерами, подзаголовками, акцент на 2025."
    )
    for fn, key in [("Groq", GROQ_KEY), ("OpenRouter", OPENROUTER_KEY)]:
        if key:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions" if fn == "Groq" else "https://openrouter.ai/api/v1/chat/completions"
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": "llama-3.1-70b-versatile" if fn=="Groq" else "mistralai/mistral-7b-instruct",
                          "messages":[{"role":"user","content":prompt}],
                          "max_tokens":1000},
                    timeout=60
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                print(f"Статья получена через {fn}")
                return content, fn
            except Exception as e:
                print(f"Ошибка {fn} при генерации статьи: {e}")
    fallback = f"# {topic}\n\nСтатья о {topic}. Подробнее скоро…"
    return fallback, "fallback"

def get_image(topic):
    if not OPENROUTER_KEY:
        return None
    prompt = f"Иллюстрация для статьи: '{topic}', стиль: футуристичный, без текста."
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/images",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
            json={"model":"stabilityai/stable-diffusion-xl-base-1.0","prompt":prompt,"response_format":"b64_json","size":"1024x1024"},
            timeout=120
        )
        resp.raise_for_status()
        b64 = resp.json()["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64)
        fname = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + ".png"
        path = os.path.join(IMG_DIR, fname)
        with open(path, "wb") as f: f.write(img_bytes)
        print(f"Изображение сохранено: {path}")
        return f"/images/news/{fname}"
    except Exception as e:
        print(f"Ошибка генерации изображения: {e}")
        return None

def slugify(text):
    slug = "".join(c if c.isalnum() or c==" " else "-" for c in text.lower())
    return "-".join(slug.split())[:70]

def write_news(topic, article, model, image_url):
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = slugify(topic)
    md_path = os.path.join(NEWS_DIR, f"{slug}.md")
    front = f"""---
title: "{topic}"
date: {date}
draft: false
model: "{model}"
"""
    if image_url:
        front += f'image: "{image_url}"\n'
    front += "---\n\n"
    body = article
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(front + body)
    print(f"Статья сохранена: {md_path}")

def clean_old():
    files = sorted(glob.glob(f"{NEWS_DIR}/*.md"), key=os.path.getmtime, reverse=True)
    for p in files[5:]:
        os.remove(p)
        print(f"Удалена старая статья: {p}")

def main():
    print("=== START GENERATION ===")
    topic = get_topic()
    article, model = get_article(topic)
    image_url = get_image(topic)
    write_news(topic, article, model, image_url)
    clean_old()
    print("=== DONE ===")

if __name__ == "__main__":
    main()
