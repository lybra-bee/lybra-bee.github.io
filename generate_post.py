#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_post.py
- Автоматическая генерация статьи (Groq) с выбором модели
- Генерация фотореалистичного изображения (Stable Horde primary)
- Умный fallback: HF / ClipDrop / локальная заглушка
- Robust logging и diagnostics
"""

import os
import re
import time
import json
import base64
import random
import logging
import requests
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional

# ========== CONFIG / ENV ==========
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ENV = os.getenv("GROQ_MODEL")  # опционально: вручную указать модель
HORDE_API_KEY = os.getenv("HORDE_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
CLIPDROP_API_KEY = os.getenv("CLIPDROP_API_KEY")

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

MAX_HORDE_POLL = 180
HORDE_POLL_INTERVAL = 3

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("generation.log", encoding="utf-8"), logging.StreamHandler()]
)
log = logging.getLogger("gen")

# ========== UTILITIES ==========
BANNED_WORDS = [
    "президент", "правительство", "партия", "выбор", "страна",
    "закон", "лидер", "санкц", "война", "войн"
]

def contains_politics(text: str) -> bool:
    t = (text or "").lower()
    return any(b in t for b in BANNED_WORDS)

def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\wа-яё0-9]+", "-", s)
    return s.strip("-")[:60]

# ========== GROQ: dynamic model selection ==========
def get_active_groq_model() -> str:
    """Возвращает рабочую модель Groq:
    1) если указан env GROQ_MODEL — используем её
    2) иначе вызываем GET /openai/v1/models и выбираем подходящую
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY не задан")

    if GROQ_MODEL_ENV:
        log.info("Используем модель из env GROQ_MODEL: %s", GROQ_MODEL_ENV)
        return GROQ_MODEL_ENV

    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        log.exception("Ошибка при запросе списка моделей Groq: %s", e)
        raise

    if r.status_code != 200:
        log.error("Groq /models HTTP %s: %s", r.status_code, r.text[:1000])
        raise RuntimeError(f"Groq models error {r.status_code}")

    data = r.json()
    # data expected to be list of model dicts or dict with 'data'
    models = []
    if isinstance(data, dict) and "data" in data:
        for el in data["data"]:
            mid = el.get("id") or el.get("model") or el.get("name")
            if mid:
                models.append(mid)
    elif isinstance(data, list):
        for el in data:
            mid = el.get("id") or el.get("model") or el.get("name")
            if mid:
                models.append(mid)
    else:
        log.warning("Unexpected Groq models response structure")

    if not models:
        raise RuntimeError("Нет доступных моделей в Groq (response empty)")

    # priority candidates
    priority_keys = ["llama3", "llama-guard", "mixtral", "gemma", "llama"]
    for key in priority_keys:
        for m in models:
            if key in m.lower():
                log.info("Выбрана модель Groq: %s (matched %s)", m, key)
                return m

    # fallback: first model
    chosen = models[0]
    log.info("Выбрана первая доступная модель Groq: %s", chosen)
    return chosen

def groq_chat_completion(model: str, system: str, user: str, max_tokens:int=1500, temperature:float=0.8) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        log.error("Groq chat HTTP %s: %s", r.status_code, r.text[:1000])
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ========== ARTICLE GENERATION ==========
def generate_article_via_groq(topic: str, groq_model: str) -> tuple[str,str]:
    system = (
        "Вы — опытный технический журналист по ИИ. Пишите на русском.\n"
        "СТРОГО: не упоминайте политику, правительства, лидеров, санкции, войны.\n"
        "Пишите подробно, с цифрами и практическими примерами.\n"
        "Формат ответа ОБЯЗАТЕЛЕН: сначала 'ЗАГОЛОВОК: <текст>' в одной строке, затем 'ТЕКСТ:' и текст статьи."
    )
    user = f"Тема: {topic}\n\nПожалуйста, отдайте строго в формате:\nЗАГОЛОВОК: ...\nТЕКСТ:\n..."

    raw = groq_chat_completion(groq_model, system, user, max_tokens=2800, temperature=0.8)
    # robust parsing
    title = None
    body = None
    m_title = re.search(r"ЗАГОЛОВОК[:\-]\s*(.+)", raw, flags=re.IGNORECASE)
    m_body = re.search(r"ТЕКСТ[:\-]\s*([\s\S]+)", raw, flags=re.IGNORECASE)
    if m_title:
        title = m_title.group(1).strip()
    else:
        # fallback: first non-empty line
        first_line = next((ln for ln in [l.strip() for l in raw.splitlines()] if ln), "")
        title = first_line[:120] if first_line else "AI Article"

    if m_body:
        body = m_body.group(1).strip()
    else:
        # fallback: everything except first line
        lines = [l for l in raw.splitlines() if l.strip()]
        body = "\n".join(lines[1:]) if len(lines) > 1 else "\n".join(lines)

    return title, body

# ========== IMAGE PROMPT HELPERS ==========
def build_image_prompt_from_title(title: str) -> dict:
    """Строит положительный и negative промпты для фоторельности"""
    positive = (
        f"photorealistic photograph, real world scene, cinematic lighting, "
        f"shallow depth of field, ultra detailed, 35mm lens, studio lighting, modern technology, {title}"
    )
    negative = (
        "chart, graph, diagram, infographic, table, plot, numbers, text overlays, watermark, logo, "
        "illustration, drawing, cartoon, anime, schematic, blueprint"
    )
    return {"positive": positive, "negative": negative}

# ========== HORDE (Stable Horde) ==========
HORDE_BASE = "https://stablehorde.net/api/v2"

def horde_send_async(prompt: str, negative: str, width:int=1024, height:int=1024, steps:int=30) -> Optional[str]:
    if not HORDE_API_KEY:
        log.info("HORDE_API_KEY not set, skipping Horde")
        return None
    url = f"{HORDE_BASE}/generate/async"
    headers = {"apikey": HORDE_API_KEY, "Content-Type": "application/json"}
    body = {
        "prompt": prompt,
        "params": {
            "width": width,
            "height": height,
            "steps": steps,
            "sampler_name": "k_euler",
            "cfg_scale": 7,
            "negative_prompt": negative
        },
        "models": ["Realistic Vision", "Juggernaut XL", "Absolute Reality"],
        "nsfw": False
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
    except Exception as e:
        log.exception("Horde async request failed: %s", e)
        return None

    if r.status_code in (200, 201, 202):
        j = r.json()
        tid = j.get("id") or j.get("task_id") or j.get("uuid")
        log.info("Horde task created: %s", tid)
        return tid
    else:
        log.warning("Horde async returned HTTP %s: %s", r.status_code, r.text[:1000])
        return None

def horde_poll_and_save(task_id: str, out_path: Path, timeout:int=MAX_HORDE_POLL) -> bool:
    if not task_id:
        return False
    url_template = f"{HORDE_BASE}/generate/status/{task_id}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url_template, headers={"apikey": HORDE_API_KEY}, timeout=15)
            if r.status_code != 200:
                log.warning("Horde status HTTP %s: %s", r.status_code, r.text[:800])
                time.sleep(HORDE_POLL_INTERVAL)
                continue
            st = r.json()
            # check done & images
            if st.get("done") or st.get("status") == "done":
                # try multiple paths
                gens = st.get("generations") or st.get("images") or st.get("generations_data") or []
                if not gens:
                    log.warning("Horde done but no images in response: %s", st)
                    return False
                # first image: may be base64 string or URL or dict with 'img'
                first = gens[0]
                img_b64 = None
                img_url = None
                if isinstance(first, dict):
                    img_b64 = first.get("img") or first.get("b64") or first.get("base64")
                    img_url = first.get("url") or first.get("image") or first.get("img")
                elif isinstance(first, str):
                    # maybe base64 or url
                    if first.startswith("http"):
                        img_url = first
                    else:
                        img_b64 = first
                # prefer URL if present
                if img_url:
                    try:
                        r2 = requests.get(img_url, timeout=30)
                        if r2.status_code == 200:
                            out_path.write_bytes(r2.content)
                            log.info("Saved Horde image from url to %s", out_path)
                            return True
                    except Exception as e:
                        log.warning("Failed to download Horde image URL: %s", e)
                if img_b64:
                    try:
                        b = base64.b64decode(img_b64)
                        out_path.write_bytes(b)
                        log.info("Saved Horde image (base64) to %s", out_path)
                        return True
                    except Exception as e:
                        log.warning("Failed to decode Horde base64 image: %s", e)
                log.warning("No usable image found in Horde response")
                return False
        except Exception as e:
            log.exception("Horde poll exception: %s", e)
        time.sleep(HORDE_POLL_INTERVAL)
    log.warning("Horde polling timed out after %s seconds", timeout)
    return False

# ========== FALLBACKS: HF / ClipDrop / Random image ==========
def hf_generate(prompt: str) -> Optional[Path]:
    if not HF_API_TOKEN:
        return None
    # call HF inference for an image model (try SDXL turbo)
    model = "stabilityai/stable-diffusion-xl-base-1.0"
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    try:
        r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=60)
        if r.status_code == 200 and r.headers.get("content-type","").startswith("image"):
            out = IMAGES_DIR / f"hf-{int(time.time())}.png"
            out.write_bytes(r.content)
            log.info("Saved HF image to %s", out)
            return out
        else:
            log.warning("HF returned %s: %s", r.status_code, r.text[:400])
    except Exception as e:
        log.exception("HF exception: %s", e)
    return None

def clipdrop_generate(prompt: str) -> Optional[Path]:
    if not CLIPDROP_API_KEY:
        return None
    url = "https://clipdrop-api.co/text-to-image/v1"
    try:
        r = requests.post(url, headers={"x-api-key": CLIPDROP_API_KEY}, files={"prompt": (None, prompt)}, timeout=90)
        if r.status_code == 200:
            out = IMAGES_DIR / f"clipdrop-{int(time.time())}.png"
            out.write_bytes(r.content)
            log.info("Saved ClipDrop image to %s", out)
            return out
        else:
            log.warning("ClipDrop returned %s: %s", r.status_code, r.text[:400])
    except Exception as e:
        log.exception("ClipDrop exception: %s", e)
    return None

def fallback_random_image() -> Path:
    # use picsum placeholder for safety (photo-like)
    try:
        url = "https://picsum.photos/1024/1024"
        r = requests.get(url, timeout=20)
        out = IMAGES_DIR / f"fallback-{int(time.time())}.jpg"
        out.write_bytes(r.content)
        log.info("Saved fallback random photo to %s", out)
        return out
    except Exception as e:
        log.exception("Fallback random image failed: %s", e)
        # as final fallback create small blank PNG
        out = IMAGES_DIR / f"blank-{int(time.time())}.png"
        out.write_bytes(b"")
        return out

# ========== SMART IMAGE GENERATION ==========
def generate_image_for_title(title: str) -> Path:
    p = build_image_prompt_from_title(title)
    positive = p["positive"]
    negative = p["negative"]

    # 1) Horde
    if HORDE_API_KEY:
        tid = horde_send = horde_send_async(positive, negative)
        if tid:
            out_path = IMAGES_DIR / f"post-{int(time.time())}.png"
            ok = horde_poll_and_save(tid, out_path)
            if ok:
                return out_path
            log.warning("Horde failed or returned no image, falling back")

    # 2) HF
    hf = hf_generate(positive)
    if hf:
        return hf

    # 3) ClipDrop
    cd = clipdrop_generate(positive)
    if cd:
        return cd

    # 4) final fallback
    return fallback_random_image()

# ========== TELEGRAM ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_to_telegram(title: str, image_path: Path, text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.info("Telegram credentials not set — skipping")
        return
    caption = f"*Новая статья*\n\n{title}\n\n{' '.join(text.split()[:30])}…"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, "rb") as ph:
            r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": ph}, timeout=30)
        log.info("Telegram status %s", r.status_code)
    except Exception as e:
        log.exception("Telegram send failed: %s", e)

# ========== MAIN FLOW ==========
def main():
    log.info("=== START ===")
    # get groq model
    try:
        groq_model = get_active_groq_model()
    except Exception as e:
        log.exception("Cannot select Groq model: %s", e)
        raise

    # choose topic
    topics = [
        "Практическое применение генеративного ИИ в 2025 году",
        "Как LLM ускоряют разработку ПО",
        "Мультимодальные модели и реальные кейсы",
        "ИИ в автоматизации контента",
        "Эффективность инференса и optimisation"
    ]

    for attempt in range(1, 4):
        topic = random.choice(topics)
        log.info("Article attempt %d: %s", attempt, topic)
        try:
            title, body = generate_article_via_groq(topic, groq_model)
        except Exception as e:
            log.exception("Groq article generation failed: %s", e)
            if attempt < 3:
                time.sleep(2)
                continue
            else:
                raise

        if contains_politics(title + "\n" + body):
            log.warning("Politics detected in article — retrying")
            continue
        break

    # generate image
    try:
        image_path = generate_image_for_title(title)
    except Exception as e:
        log.exception("Image generation failed: %s", e)
        image_path = fallback_random_image()

    # save post
    today = datetime.utcnow().date().isoformat()
    slug = slugify(title)
    post_file = POSTS_DIR / f"{today}-{slug}.md"
    metadata = {
        "title": title,
        "date": today,
        "layout": "post",
        "image": f"/{image_path.as_posix()}"
    }
    with open(post_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        json_meta = json.dumps(metadata, ensure_ascii=False)
        # better to write YAML front matter - keep simple
        f.write(f"title: \"{title}\"\n")
        f.write(f"date: {today}\n")
        f.write(f"image: /{image_path.as_posix()}\n")
        f.write("---\n\n")
        f.write(body)

    log.info("Saved post: %s", post_file)

    # send to telegram
    try:
        send_to_telegram(title, image_path, body)
    except Exception as e:
        log.exception("Telegram send exception: %s", e)

    log.info("=== DONE ===")
    return True

if __name__ == "__main__":
    main()
