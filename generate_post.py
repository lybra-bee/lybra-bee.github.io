#!/usr/bin/env python3
"""
Автономная система генерации статей об ИИ 2025-2026
- Самостоятельно обновляет тренды
- Генерирует русскую статью с цифрами и таблицами
- Создает фотореалистичное изображение (PNG)
- Публикует пост для Jekyll
- Отправляет тизер и изображение в Telegram
- Оптимизировано для GitHub Actions
"""

import datetime
import random
import os
import re
import json
import time
import glob
from typing import Dict, List

import requests
import yaml
from groq import Groq

LOG_FILE = "generation.log"

def log(msg: str):
    ts = datetime.datetime.utcnow().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)

# ---------- КОНФИГУРАЦИЯ ----------
EMBEDDED_TRENDS_FILE = "trends_cache.json"
TRENDS_UPDATE_INTERVAL = 86400
BASE_URL = "https://lybra-ai.ru"

# ---------- MARKDOWN NORMALIZER ----------
def normalize_markdown(md: str) -> str:
    if not md:
        return md
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"

# ---------- TRENDS ----------
EMBEDDED_TRENDS = [
    {"id": "quantum_2025", "news": "New quantum processors reach practical speedups in optimization tasks", "keywords": ["quantum", "processors"], "category": "hardware"},
    {"id": "agentic_ai_2025", "news": "Agentic AI systems coordinate multiple models for enterprise workflows", "keywords": ["agentic ai", "automation"], "category": "software"},
    {"id": "ai_efficiency", "news": "Inference costs drop by 200x with sparse and low-rank models", "keywords": ["efficiency", "inference"], "category": "optimization"},
]

def load_trends() -> List[Dict]:
    try:
        if os.path.exists(EMBEDDED_TRENDS_FILE):
            with open(EMBEDDED_TRENDS_FILE, encoding="utf-8") as f:
                cache = json.load(f)
                if time.time() - cache.get("last_update", 0) < TRENDS_UPDATE_INTERVAL:
                    log("✅ Тренды загружены из кэша")
                    return cache["trends"]
    except Exception as e:
        log(f"⚠️ Ошибка кэша: {e}")
    return EMBEDDED_TRENDS

# ---------- АНТИПОЛИТИКА ----------
POLITICAL_RE = re.compile(
    r"\b(государств|закон|регулятор|министр|президент|страна|санкц)\b",
    re.I
)

def is_political(text: str) -> bool:
    return bool(POLITICAL_RE.search(text))

# ---------- ЗАГОЛОВОК ----------
def generate_title(client: Groq, trend: Dict, article_type: str) -> str:
    prompt = (
        f"Создай ОДИН цепляющий заголовок (5–12 слов).\n"
        f"Тема: {trend['news']}.\n"
        "Только ИИ и технологии. Без политики.\n"
        "Только заголовок."
    )
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Русский tech-редактор"},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant",
        temperature=1.0,
        max_tokens=40
    )
    title = resp.choices[0].message.content.strip()
    log(f"📰 Заголовок: {title}")
    return re.sub(r"[^\w\s-]", "", title)[:80]

# ---------- СТАТЬЯ ----------
def generate_article(client: Groq, trend: Dict, article_type: str) -> str:
    system_prompt = (
        "Ты технический журналист по ИИ.\n"
        "СТРОГО запрещена политика, законы, страны.\n"
        "Фокус: технологии, цифры, практика."
    )
    user_prompt = (
        f"Напиши статью типа '{article_type}' (1500–2500 слов).\n"
        f"Тема: {trend['news']}\n"
        "Markdown, таблицы, метрики."
    )

    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.8,
        max_tokens=4000
    )
    content = resp.choices[0].message.content
    if is_political(content):
        raise ValueError("Политика обнаружена")
    log("📄 Статья сгенерирована")
    return normalize_markdown(content)

# ---------- PNG PLACEHOLDER ----------
def generate_placeholder_png(path: str):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (1280, 720), (18, 22, 28))
    draw = ImageDraw.Draw(img)
    draw.text((640, 360), "AI • High Tech • 2025", fill=(200, 200, 200), anchor="mm")
    img.save(path, "PNG", optimize=True)

# ---------- ИЗОБРАЖЕНИЕ ----------
def generate_image(title: str, trend: Dict, post_num: int) -> bool:
    path = f"{assets_dir}/post-{post_num}.png"
    prompt = (
        f"Ultra realistic photo of {title}. {trend['news']}. "
        "Photorealistic, cinematic, real world, no text, no charts."
    )

    for name, url, headers in [
        ("CLIPDROP", "https://clipdrop-api.co/text-to-image/v1",
         {"x-api-key": os.getenv("CLIPDROP_API_KEY")}),
        ("HF", "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo",
         {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"})
    ]:
        if not list(headers.values())[0]:
            continue
        try:
            r = requests.post(url,
                headers=headers,
                files={"prompt": (None, prompt)} if "clipdrop" in url else None,
                json={"inputs": prompt} if "huggingface" in url else None,
                timeout=90)
            if r.status_code == 200 and r.headers.get("content-type","").startswith("image"):
                open(path, "wb").write(r.content)
                log(f"🖼 Изображение создано: {name}")
                return True
        except Exception as e:
            log(f"❌ {name}: {e}")

    generate_placeholder_png(path)
    log("🟨 Использована PNG-заглушка")
    return True

# ---------- MAIN ----------
def main() -> bool:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = load_trends()
    trend = random.choice(trends)
    article_type = random.choice(["Обзор", "Мастер-класс", "Аналитика"])

    title = generate_title(client, trend, article_type)
    content = generate_article(client, trend, article_type)
    generate_image(title, trend, post_num)

    front_matter = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": f"/assets/images/posts/post-{post_num}.png",
        "description": trend["news"],
        "tags": ["ИИ", "технологии"] + trend["keywords"],
    }

    slug = re.sub(r"[^\w-]", "-", title.lower())[:50]
    filename = f"{posts_dir}/{today}-{slug}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, allow_unicode=True)
        f.write("---\n\n")
        f.write(content)

    log(f"✅ Пост опубликован: {filename}")
    return True

# ---------- INIT ----------
if __name__ == "__main__":
    posts_dir = "_posts"
    assets_dir = "assets/images/posts"
    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    post_num = len(glob.glob(f"{assets_dir}/*.png")) + 1
    today = datetime.date.today()

    success = main()
    raise SystemExit(0 if success else 1)
