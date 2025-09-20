#!/usr/bin/env python3
import os, requests, datetime, textwrap, json

# Папки
POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images/posts"
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# API-ключи из GitHub Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")

today = datetime.date.today().strftime("%Y-%m-%d")
slug = f"{today}-ai-article"
filename = os.path.join(POSTS_DIR, f"{slug}.md")

prompt = "Напиши урок или обзор по современным технологиям AI, примерно на 700-900 слов, с подзаголовками."

# --- Генерация текста через OpenRouter ---
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
)

if resp.status_code == 200:
    article_text = resp.json()["choices"][0]["message"]["content"]
else:
    article_text = "Ошибка генерации текста."
    print(resp.text)

# --- Генерация картинки через DeepAI ---
img_prompt = "Futuristic AI concept art, high quality, digital illustration"
img_url = None
try:
    r = requests.post(
        "https://api.deepai.org/api/text2img",
        data={"text": img_prompt},
        headers={"api-key": DEEPAI_API_KEY}
    )
    img_url = r.json().get("output_url")
    if img_url:
        img_data = requests.get(img_url).content
        img_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
        with open(img_path, "wb") as f:
            f.write(img_data)
except Exception as e:
    print("Ошибка генерации изображения:", e)

# --- Сохраняем пост ---
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"""---
title: "AI Article {today}"
date: {today}
draft: false
tags: ["AI", "Technology"]
featuredImage: "/images/posts/{slug}.jpg"
---

{article_text}
""")

print("✅ Пост сгенерирован:", filename)
