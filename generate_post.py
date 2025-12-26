#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import glob
import random
import logging
import datetime
from typing import Dict, List
import requests
import yaml
from groq import Groq

# ---------------------------------------
# LOGGER
# ---------------------------------------

logging.basicConfig(
    filename="generation.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)
log = logging.getLogger()

# ---------------------------------------
# DIRECTORIES
# ---------------------------------------

POSTS_DIR = "_posts"
ASSETS_DIR = "assets/images/posts"
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ---------------------------------------
# TRENDS
# ---------------------------------------

EMBEDDED_TRENDS = [
    {"id": "ai2025", "news": "Multimodal AI adoption accelerates in 2025", "keywords": ["multimodal", "AI"]},
    {"id": "efficiency2025", "news": "LLM inference becomes 300x cheaper", "keywords": ["LLM", "economics"]},
    {"id": "agentic2025", "news": "Agentic AI adoption in enterprise", "keywords": ["agentic", "AI"]},
]

def load_trends() -> List[Dict]:
    try:
        if os.path.exists("trends_cache.json"):
            with open("trends_cache.json", "r", encoding="utf-8") as f:
                cache = json.load(f)
                if time.time() - cache.get("last_update", 0) < 86400:
                    log.info("Loaded trends from cache")
                    return cache.get("trends", [])
    except Exception as e:
        log.warning(f"Cache error: {e}")
    log.info("Using embedded trends")
    return EMBEDDED_TRENDS

# ---------------------------------------
# TEXT GENERATION (Groq)
# ---------------------------------------

POLITICAL_WORDS = [
    "президент", "правительство", "политик",
    "выбор", "страна", "лидер", "санкц"
]

def contains_politics(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in POLITICAL_WORDS)

def slugify(text: str) -> str:
    return re.sub(r"[^\wа-я0-9]+", "-", text.lower()).strip("-")

def generate_title(client: Groq, trend: Dict) -> str:
    prompt = (
        f"Создай цепляющий заголовок (5–10 слов) на тему: {trend['news']}. "
        "Запрещено: политика, страны, лидеры."
    )
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"Русский техредактор"},
            {"role":"user","content":prompt}
        ],
        max_tokens=40,
        temperature=0.9
    )
    return r.choices[0].message.content.strip()

def generate_article(client: Groq, trend: Dict) -> str:
    prompt = (
        f"Напишите статью (1200–2000 слов).\nТема: {trend['news']}\n"
        "Запрещено: политика, страны, лидеры.\nMarkdown."
    )
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":"Технический журналист по ИИ"},
            {"role":"user","content":prompt}
        ],
        max_tokens=3500,
        temperature=0.8
    )
    return re.sub(r"\n{3,}", "\n\n", r.choices[0].message.content.strip())

# ---------------------------------------
# IMAGE GENERATION VIA HORDE
# ---------------------------------------

HORDE_BASE = "https://stablehorde.net/api/v2"
HORDE_KEY = os.getenv("HORDE_API_KEY")

def horde_generate_async(prompt: str) -> str:
    """
    Отправляет async задачу на Horde, возвращает task id
    """
    url = f"{HORDE_BASE}/generate/async"
    headers = {
        "apikey": HORDE_KEY or "0000000000",
        "Content-Type": "application/json"
    }
    body = {
        "prompt": prompt,
        "params": {"width":1024, "height":1024, "steps":30}
    }
    r = requests.post(url, headers=headers, json=body, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("id") or data.get("task_id")

def horde_check_status(task_id: str) -> dict:
    url = f"{HORDE_BASE}/generate/status/{task_id}"
    headers = {"apikey": HORDE_KEY or "0000000000"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def generate_image_horde(title: str) -> str:
    prompt = f"Photorealistic image of {title}, modern AI theme, 8k, cinematic"
    log.info("Horde generate async prompt")
    tid = horde_generate_async(prompt)
    log.info(f"Task ID: {tid}")
    for i in range(60):
        time.sleep(3)
        status = horde_check_status(tid)
        if status.get("done", False):
            image_b64 = status["images"][0]["img"]
            img_bytes = requests.utils.unquote(image_b64).encode() if "%" in image_b64 else status["images"][0]["img"].encode()
            path = f"{ASSETS_DIR}/post-{len(glob.glob(f'{ASSETS_DIR}/*.png'))+1}.png"
            with open(path, "wb") as f:
                f.write(requests.utils.unquote_to_bytes(image_b64))
            log.info(f"Image saved: {path}")
            return path
    log.warning("Horde generation timed out")
    return ""

# ---------------------------------------
# TELEGRAM
# ---------------------------------------

def send_telegram(title: str, image_path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        log.info("No Telegram keys")
        return
    with open(image_path, "rb") as ph:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id":chat, "caption": title, "parse_mode":"Markdown"},
            files={"photo":ph}
        )

# ---------------------------------------
# MAIN
# ---------------------------------------

def main():
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = load_trends()
    trend = random.choice(trends)

    title = generate_title(client, trend)
    content = generate_article(client, trend)

    img_path = generate_image_horde(title)

    today = datetime.date.today().isoformat()
    slug = slugify(title)
    fname = f"{POSTS_DIR}/{today}-{slug}.md"
    fm = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": f"/{img_path}",
        "tags": trend.get("keywords", []),
    }
    with open(fname, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(fm, f, allow_unicode=True)
        f.write("---\n\n")
        f.write(content)

    send_telegram(title, img_path)
    log.info("Post saved: " + fname)

if __name__ == "__main__":
    main()
