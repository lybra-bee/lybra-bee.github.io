#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_post.py
Генерация статьи + изображение через Horde (Stable Horde) с fallback'ами.
Логи пишутся в generation.log
"""

import os
import re
import time
import json
import glob
import base64
import logging
import datetime
from typing import List, Dict, Optional

import requests
import yaml
from groq import Groq

# ---------- LOGGING ----------
logging.basicConfig(
    filename="generation.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger()

# ---------- PATHS / CONFIG ----------
POSTS_DIR = "_posts"
ASSETS_DIR = "assets/images/posts"
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

HORDE_BASE = "https://stablehorde.net/api/v2"
HORDE_KEY = os.getenv("HORDE_API_KEY")  # должен быть в secrets

HF_TOKEN = os.getenv("HF_API_TOKEN")
CLIPDROP_KEY = os.getenv("CLIPDROP_API_KEY")

MAX_HORDE_POLL_SECONDS = 180  # максимум ожидать результата от Horde
HORDE_POLL_INTERVAL = 3       # интервал опроса статуса

# ---------- TRENDS ----------
EMBEDDED_TRENDS = [
    {"id": "ai2025", "news": "Multimodal AI adoption accelerates in 2025", "keywords": ["multimodal", "AI"]},
    {"id": "efficiency2025", "news": "LLM inference becomes much cheaper", "keywords": ["LLM", "economics"]},
    {"id": "agentic2025", "news": "Agentic AI adoption in enterprise", "keywords": ["agentic", "AI"]},
]

def load_trends():
    try:
        if os.path.exists("trends_cache.json"):
            with open("trends_cache.json", "r", encoding="utf-8") as f:
                cache = json.load(f)
                if time.time() - cache.get("last_update", 0) < 86400:
                    log.info("Тренды загружены из кэша")
                    return cache.get("trends", EMBEDDED_TRENDS)
    except Exception as e:
        log.warning("Ошибка чтения кэша трендов: %s", e)
    log.info("Используем встроенные тренды")
    return EMBEDDED_TRENDS

# ---------- TEXT GENERATION ----------
POLITICAL_WORDS = ["президент", "правительство", "политик", "выбор", "страна", "лидер", "санкц"]

def contains_politics(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in POLITICAL_WORDS)

def slugify(text: str) -> str:
    s = re.sub(r"[^\wа-яА-Я0-9]+", "-", text.lower())
    return s.strip("-")[:60]

def generate_title(groq_client: Groq, trend: Dict) -> str:
    prompt = f"Создай цеплящий технический заголовок (5-10 слов). Тема: {trend['news']}. Строго без политики."
    try:
        resp = groq_client.chat.completions.create(
            messages=[{"role":"system","content":"Русский техредактор"},{"role":"user","content":prompt}],
            model="llama-3.1-8b-instant", max_tokens=40, temperature=0.9
        )
        title = resp.choices[0].message.content.strip()
        log.info("Генерация заголовка: %s", title)
        return title
    except Exception as e:
        log.exception("Ошибка генерации заголовка: %s", e)
        return "AI Article"

def generate_article(groq_client: Groq, trend: Dict) -> str:
    prompt = (
        f"Напиши техническую статью (1200-2000 слов) на русском языке. Тема: {trend['news']}. "
        "СТРОГО: без политики, стран, регуляторов. Формат — Markdown, добавь таблицы и метрики."
    )
    for attempt in range(1, 4):
        try:
            resp = groq_client.chat.completions.create(
                messages=[{"role":"system","content":"Технический журналист по ИИ"},{"role":"user","content":prompt}],
                model="llama-3.3-70b-versatile", max_tokens=4000, temperature=0.8
            )
            content = resp.choices[0].message.content
            content = re.sub(r"<[^>]+>", "", content)
            content = re.sub(r"\n{3,}", "\n\n", content).strip()
            if contains_politics(content):
                log.warning("Обнаружена политика в статье — попытка %d", attempt)
                continue
            log.info("Статья сгенерирована (попытка %d)", attempt)
            return content
        except Exception as e:
            log.exception("Ошибка генерации статьи (попытка %d): %s", attempt, e)
            time.sleep(1)
    raise RuntimeError("Не удалось сгенерировать статью без политики")

# ---------- HORDE: async generation ----------
def _post_horde_async(prompt: str, headers: dict, body: dict) -> requests.Response:
    url = f"{HORDE_BASE}/generate/async"
    return requests.post(url, headers=headers, json=body, timeout=15)

def horde_generate_async(prompt: str) -> Optional[str]:
    """Посылаем задачу в Horde. Возвращаем task id или None."""
    if not HORDE_KEY:
        log.info("HORDE_API_KEY не задан — пропускаем Horde")
        return None

    body = {
        "prompt": prompt,
        "params": {"width": 1024, "height": 1024, "steps": 30}
    }

    # Попробуем оба варианта заголовка: apikey и Authorization
    header_variants = [
        {"apikey": HORDE_KEY, "Content-Type": "application/json"},
        {"Authorization": f"Bearer {HORDE_KEY}", "Content-Type": "application/json"}
    ]

    for headers in header_variants:
        try:
            r = _post_horde_async(prompt, headers, body)
            log.info("Horde async response status: %s", r.status_code)
            if r.status_code == 200 or r.status_code == 201:
                job = r.json()
                # возможные ключи: id, task_id
                tid = job.get("id") or job.get("task_id")
                log.info("Horde task created: %s (headers variant=%s)", tid, "apikey" in headers)
                return tid
            else:
                # логируем тело для диагностики (403/401)
                try:
                    log.warning("Horde returned body: %s", r.text)
                except Exception:
                    pass
                # если 403 — сразу вернуть None, чтобы не зацикливаться
                if r.status_code in (401, 403):
                    log.warning("Horde auth error %s", r.status_code)
                    return None
        except Exception as e:
            log.exception("Exception while creating Horde task: %s", e)
            # пробуем следующий заголовок вариант
            continue
    return None

def horde_check_status(task_id: str) -> Optional[dict]:
    if not HORDE_KEY:
        return None
    try:
        url = f"{HORDE_BASE}/generate/status/{task_id}"
        headers = {"apikey": HORDE_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            log.warning("Horde status HTTP %s body: %s", r.status_code, r.text)
            return None
    except Exception as e:
        log.exception("Horde status exception: %s", e)
        return None

def extract_image_from_status(status: dict) -> Optional[bytes]:
    """
    Поддерживаем несколько форматов ответа:
    - status['generations'][0]['img'] (base64)
    - status['images'][0]['img'] (base64)
    - status may include direct binary? unlikely
    """
    if not status:
        return None
    # check 'generations'
    gens = status.get("generations") or status.get("generations_data") or status.get("images")
    if isinstance(gens, list) and len(gens) > 0:
        first = gens[0]
        # common keys: 'img' (base64), 'b64' (maybe)
        img_b64 = first.get("img") or first.get("b64") or first.get("image") or first.get("base64")
        if img_b64:
            try:
                return base64.b64decode(img_b64)
            except Exception as e:
                log.warning("Ошибка декодирования base64: %s", e)
                # maybe it's url (data: or direct url) — try to handle if startswith http
                if isinstance(img_b64, str) and img_b64.startswith("http"):
                    try:
                        r = requests.get(img_b64, timeout=10)
                        if r.status_code == 200:
                            return r.content
                    except Exception as e2:
                        log.warning("Ошибка скачивания изображения по url: %s", e2)
    # sometimes status may contain 'done': True and 'image' keys
    if status.get("done") and isinstance(status.get("images"), list) and status["images"]:
        try:
            b64 = status["images"][0].get("img") or status["images"][0].get("b64")
            if b64:
                return base64.b64decode(b64)
        except Exception:
            pass
    return None

def generate_image_via_horde(title: str) -> Optional[str]:
    """Генерирует через Horde. Возвращает путь к файлу или None."""
    tid = horde_generate_async(title)
    if not tid:
        log.info("Horde task not created or auth failed")
        return None

    log.info("Polling Horde for task %s", tid)
    start = time.time()
    while time.time() - start < MAX_HORDE_POLL_SECONDS:
        status = horde_check_status(tid)
        if not status:
            time.sleep(HORDE_POLL_INTERVAL)
            continue
        # many horde responses use 'done' or 'status' fields
        done = status.get("done") or status.get("success") or (status.get("status") == "done")
        if done:
            img_bytes = extract_image_from_status(status)
            if img_bytes:
                fname = f"post-{len(glob.glob(os.path.join(ASSETS_DIR, '*.png')))+1}.png"
                path = os.path.join(ASSETS_DIR, fname)
                try:
                    with open(path, "wb") as f:
                        f.write(img_bytes)
                    log.info("Saved Horde image to %s", path)
                    return path
                except Exception as e:
                    log.exception("Failed to write Horde image: %s", e)
                    return None
            else:
                log.warning("Horde marked done but no image extracted, body: %s", status)
                return None
        # not done yet
        time.sleep(HORDE_POLL_INTERVAL)
    log.warning("Horde polling timed out after %s seconds", MAX_HORDE_POLL_SECONDS)
    return None

# ---------- FALLBACKS: HF / ClipDrop / Matplotlib ----------
def generate_image_via_hf(prompt: str) -> Optional[str]:
    """Простой HF inference call — модель может вернуть bytes as content."""
    if not HF_TOKEN:
        return None
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    model = "stabilityai/sdxl-turbo"  # можно изменить
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=60)
        if r.status_code == 200 and r.headers.get("content-type","").startswith("image"):
            fname = f"post-{len(glob.glob(os.path.join(ASSETS_DIR,'*.png')))+1}.png"
            path = os.path.join(ASSETS_DIR, fname)
            with open(path, "wb") as f:
                f.write(r.content)
            log.info("Saved HF image %s", path)
            return path
        else:
            log.warning("HF returned status %s body: %s", r.status_code, r.text[:400])
            return None
    except Exception as e:
        log.exception("HF generation error: %s", e)
        return None

def generate_image_via_clipdrop(prompt: str) -> Optional[str]:
    if not CLIPDROP_KEY:
        return None
    url = "https://clipdrop-api.co/text-to-image/v1"
    try:
        r = requests.post(url, headers={"x-api-key": CLIPDROP_KEY}, files={"prompt": (None, prompt)}, timeout=90)
        if r.status_code == 200:
            fname = f"post-{len(glob.glob(os.path.join(ASSETS_DIR,'*.png')))+1}.png"
            path = os.path.join(ASSETS_DIR, fname)
            with open(path, "wb") as f:
                f.write(r.content)
            log.info("Saved ClipDrop image %s", path)
            return path
        else:
            log.warning("ClipDrop status %s body: %s", r.status_code, r.text[:400])
    except Exception as e:
        log.exception("ClipDrop exception: %s", e)
    return None

def generate_image_fallback_chart() -> Optional[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        years = ["2023","2024","2025"]
        vals = [random.randint(40,100), random.randint(100,200), random.randint(200,350)]
        plt.figure(figsize=(12,6))
        plt.plot(years, vals, marker="o", linewidth=3)
        plt.title("AI Trend Growth (fallback)")
        plt.tight_layout()
        fname = f"post-{len(glob.glob(os.path.join(ASSETS_DIR,'*.png')))+1}.png"
        path = os.path.join(ASSETS_DIR, fname)
        plt.savefig(path, dpi=150)
        plt.close()
        log.info("Saved fallback chart %s", path)
        return path
    except Exception as e:
        log.exception("Fallback chart error: %s", e)
        return None

def generate_image_smart(title: str) -> str:
    """Умный перебор: Horde -> HF -> ClipDrop -> fallback"""
    prompt = f"Photorealistic image of {title}. Cinematic, 8k, no charts, no text, photorealistic."
    # 1. Horde
    try:
        path = generate_image_via_horde(prompt)
        if path:
            return path
    except Exception as e:
        log.exception("Horde flow error: %s", e)
    # 2. HF
    try:
        path = generate_image_via_hf(prompt)
        if path:
            return path
    except Exception as e:
        log.exception("HF fallback error: %s", e)
    # 3. ClipDrop
    try:
        path = generate_image_via_clipdrop(prompt)
        if path:
            return path
    except Exception as e:
        log.exception("ClipDrop fallback error: %s", e)
    # 4. final fallback
    path = generate_image_fallback_chart()
    if path:
        return path
    raise RuntimeError("No image generated by any provider")

# ---------- TELEGRAM ----------
def send_telegram(title: str, image_path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        log.info("Telegram keys not set — skipping")
        return
    try:
        with open(image_path, "rb") as ph:
            files = {"photo": ph}
            data = {"chat_id": chat, "caption": title, "parse_mode": "Markdown"}
            r = requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data=data, files=files, timeout=30)
            log.info("Telegram send status: %s", r.status_code)
    except Exception as e:
        log.exception("Telegram send exception: %s", e)

# ---------- MAIN ----------
def main():
    log.info("=== START generation ===")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = load_trends()
    trend = random.choice(trends)

    title = generate_title(client, trend)
    article = generate_article(client, trend)

    # generate image (smart)
    try:
        img_path = generate_image_smart(title)
    except Exception as e:
        log.exception("Image generation failed entirely: %s", e)
        img_path = None

    # save post
    today = datetime.date.today().isoformat()
    slug = slugify(title)
    filename = f"{POSTS_DIR}/{today}-{slug}.md"
    front = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": f"/{img_path.replace(os.sep, '/')}" if img_path else "",
        "tags": trend.get("keywords", [])
    }
    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front, f, allow_unicode=True, sort_keys=False)
        f.write("---\n\n")
        f.write(article)
    log.info("Saved post %s", filename)

    if img_path:
        send_telegram(title, img_path)
    log.info("=== FINISHED ===")

if __name__ == "__main__":
    main()
