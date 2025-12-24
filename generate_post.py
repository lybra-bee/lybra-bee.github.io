#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_post.py
Умный выбор генератора изображений: StabilityAI -> HuggingFace SDXL -> ClipDrop -> Pollinations -> fallback
Хранение статистики провайдеров в image_stats.json
Генерация статей (Groq), проверка на политику, перегенерация до N попыток.
Публикация тизера + изображения в Telegram (если есть ключи).
Логи: generation.log.
"""

import os
import re
import time
import json
import uuid
import glob
import random
import logging
import datetime
from typing import Dict, List, Optional

import requests
import yaml
from groq import Groq
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

# ====== Настройка логов ======
LOG_FILE = "generation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ],
)
log = logging.getLogger()

# ====== Конфигурация путей ======
POSTS_DIR = "_posts"
ASSETS_DIR = "assets/images/posts"
STATS_FILE = "image_stats.json"
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ====== Настройки генерации ======
MAX_ARTICLE_ATTEMPTS = 3
MAX_IMAGE_ATTEMPTS_PER_PROVIDER = 3
BACKOFF_BASE = 1.5  # экспоненциальный бэкoff
HF_MODELS_FOR_PHOTOREAL = ["stabilityai/sdxl-turbo", "stabilityai/stable-diffusion-xl-base-1.0"]
HF_MODELS_ARTISTIC = ["prompthero/openjourney"]

# ====== Ключи (берутся из окружения в workflow) ======
HF_TOKEN = os.getenv("HF_API_TOKEN")
STABILITY_KEY = os.getenv("STABILITYAI_KEY")
CLIPDROP_KEY = os.getenv("CLIPDROP_API_KEY")
# Pollinations не требует ключа

# ====== Встроенные тренды (fallback) ======
EMBEDDED_TRENDS = [
    {"id": "trend_ai_business", "news": "Практическое применение генеративного ИИ в 2025 году", "keywords": ["генеративный ИИ"]},
    {"id": "trend_multimodal", "news": "Мультимодальные модели и их использование", "keywords": ["мультимодальные модели"]},
    {"id": "trend_llm_engineering", "news": "Как инженеры ускоряют разработку с LLM", "keywords": ["LLM", "инжиниринг"]},
]

# ====== Утилиты ======
def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def unique_image_name(prefix: str = "post") -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}-{ts}-{uid}.png"

def is_image_bytes(b: bytes) -> bool:
    try:
        Image.open(io := bytes_to_filelike(b))
        return True
    except Exception:
        return False

def bytes_to_filelike(b: bytes):
    from io import BytesIO
    return BytesIO(b)

# ====== Простая статистика провайдеров ======
# структура: { "provider_name": {"success": int, "fail": int, "last": "ISO timestamp"} }
stats = load_json(STATS_FILE, {})

def record_stat(provider: str, success: bool):
    s = stats.get(provider, {"success": 0, "fail": 0, "last": None})
    if success:
        s["success"] += 1
    else:
        s["fail"] += 1
    s["last"] = datetime.datetime.utcnow().isoformat()
    stats[provider] = s
    try:
        save_json(STATS_FILE, stats)
    except Exception as e:
        log.warning(f"Не удалось сохранить stats: {e}")

def provider_score(provider: str) -> float:
    # простая формула: success_rate * (1 + log(success+1))
    s = stats.get(provider, {"success": 0, "fail": 0})
    succ = s.get("success", 0)
    fail = s.get("fail", 0)
    total = succ + fail
    success_rate = (succ / total) if total > 0 else 0.5
    import math
    return success_rate * (1 + math.log(succ + 1))

# ====== Генерация статьи (Groq) ======
def normalize_markdown(md: str) -> str:
    if not md:
        return md
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"

def contains_politics(text: str) -> bool:
    patterns = [
        r"\bпрезидент", r"\bвыбор", r"\bзакон", r"\bуказ", r"\bсанкц", r"\bправитель", r"\bминстр",
        r"\bстрана\b", r"\bпарламент", r"\bполитик"
    ]
    t = text.lower()
    return any(re.search(p, t) for p in patterns)

def generate_title(client: Groq, trend: Dict, article_type: str) -> str:
    prompt = (
        f"Создай цеплящий заголовок (5-12 слов) для статьи типа '{article_type}'.\n"
        f"Тема: {trend['news']}\n"
        "СТРОГО: без политики, стран, регуляторов, лидеров. Только ИИ/технологии."
    )
    resp = client.chat.completions.create(
        messages=[{"role": "system", "content": "Русский тех-редактор"}, {"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        max_tokens=40,
        temperature=0.9
    )
    title = resp.choices[0].message.content.strip()
    title = re.sub(r"[^\w\s\-]", "", title)[:120]
    log.info(f"📰 Заголовок: {title}")
    return title

def generate_article(client: Groq, trend: Dict, article_type: str) -> str:
    system_prompt = (
        "Ты — технический журналист по ИИ. СТРОГО запрещено: политика, страны, регуляторы, лидеры, законы.\n"
        "Пиши на русском, формат — Markdown, включи 2 таблицы, метрики, практические примеры."
        f"\nТема: {trend['news']}"
    )
    user_prompt = f"Напиши статью '{article_type}' (1200–2000 слов)."

    for attempt in range(1, MAX_ARTICLE_ATTEMPTS + 1):
        resp = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
            temperature=0.8
        )
        content = normalize_markdown(resp.choices[0].message.content)
        if contains_politics(content):
            log.warning("⚠️ Обнаружена политика в статье — регенерируем")
            continue
        return content
    raise RuntimeError("Не удалось сгенерировать статью без политики")

# ====== Провайдеры изображений ======

def attempt_with_backoff(func, prompt: str, path: str, provider_name: str) -> bool:
    """Попытки с экспоненциальным бэкоффом"""
    delay = 1.0
    for i in range(MAX_IMAGE_ATTEMPTS_PER_PROVIDER):
        try:
            ok = func(prompt, path)
            if ok:
                record_stat(provider_name, True)
                return True
            else:
                record_stat(provider_name, False)
        except Exception as e:
            log.warning(f"Ошибка провайдера {provider_name} (итерация {i+1}): {e}")
            record_stat(provider_name, False)
        time.sleep(delay)
        delay *= BACKOFF_BASE
    return False

# --- Stability.ai (official API) ---
def provider_stability(prompt: str, path: str) -> bool:
    if not STABILITY_KEY:
        return False
    url = "https://api.stability.ai/v2beta/stable-image/generate"
    # Stability API can vary; using v2beta core endpoint previously used. Adjust as needed.
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {STABILITY_KEY}"},
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30
            },
            timeout=120
        )
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            with open(path, "wb") as f:
                f.write(r.content)
            log.info("✅ StabilityAI returned image")
            return True
        # Stability sometimes returns JSON with artifacts/urls; try to parse
        try:
            j = r.json()
            # If URL present, try to fetch
            if isinstance(j, dict):
                # search for image bytes or URLs in response
                for v in j.get("artifacts", []):
                    if v.get("type") == "image" and v.get("base64"):
                        import base64
                        b = base64.b64decode(v["base64"])
                        with open(path, "wb") as f:
                            f.write(b)
                        log.info("✅ StabilityAI returned image (artifacts.base64)")
                        return True
        except Exception:
            pass
        log.warning(f"StabilityAI returned status {r.status_code}")
    except Exception as e:
        log.warning(f"StabilityAI exception: {e}")
    return False

# --- Hugging Face models ---
def provider_hf_model(prompt: str, path: str, model_name: str) -> bool:
    if not HF_TOKEN:
        return False
    url = f"https://api-inference.huggingface.co/models/{model_name}"
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {HF_TOKEN}"}, json={"inputs": prompt}, timeout=120)
        # if image bytes
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and ct.startswith("image"):
            with open(path, "wb") as f:
                f.write(r.content)
            log.info(f"✅ HF model {model_name} returned image")
            return True
        # sometimes HF returns JSON with artifacts/urls
        try:
            j = r.json()
            # If HF returns base64 or data URL, handle
            if isinstance(j, dict):
                # some models return {"error":...}
                log.warning(f"HF model {model_name} returned JSON, not image: {j.get('error') or 'no image'}")
        except Exception:
            pass
        log.warning(f"HF model {model_name} returned status {r.status_code} content-type {ct}")
    except Exception as e:
        log.warning(f"HF exception {model_name}: {e}")
    return False

# --- ClipDrop ---
def provider_clipdrop(prompt: str, path: str) -> bool:
    if not CLIPDROP_KEY:
        return False
    url = "https://clipdrop-api.co/text-to-image/v1"
    try:
        r = requests.post(url, headers={"x-api-key": CLIPDROP_KEY}, files={"prompt": (None, prompt)}, timeout=120)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            with open(path, "wb") as f:
                f.write(r.content)
            log.info("✅ ClipDrop returned image")
            return True
        log.warning(f"ClipDrop returned {r.status_code}")
    except Exception as e:
        log.warning(f"ClipDrop exception: {e}")
    return False

# --- Pollinations (no key) ---
def provider_pollinations(prompt: str, path: str) -> bool:
    try:
        url = "https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt)
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            with open(path, "wb") as f:
                f.write(r.content)
            log.info("✅ Pollinations returned image")
            return True
    except Exception as e:
        log.warning(f"Pollinations exception: {e}")
    return False

# --- Fallback: simple PNG (Pillow) ---
def provider_fallback_png(prompt: str, path: str) -> bool:
    try:
        from PIL import ImageDraw, ImageFont
        img = Image.new("RGB", (1280, 720), color=(18, 22, 28))
        draw = ImageDraw.Draw(img)
        title = "AI • Technology"
        subtitle = prompt[:120]
        try:
            # try default font
            fnt = ImageFont.load_default()
            draw.text((640, 300), title, font=fnt, anchor="mm", fill=(220, 220, 220))
            draw.text((640, 360), subtitle, font=fnt, anchor="mm", fill=(180, 180, 180))
        except Exception:
            draw.text((640, 350), title, fill=(220, 220, 220), anchor="mm")
        img.save(path, format="PNG", optimize=True)
        log.info("🟨 Fallback PNG created")
        return True
    except Exception as e:
        log.error(f"Fallback PNG error: {e}")
        return False

# ====== Смарт-выбор провайдеров ======
def available_providers(style: str) -> List[str]:
    """Возвращает список провайдеров в предпочтительном порядке в зависимости от наличия ключей и статистики"""
    candidates = []
    # preference by style (photorealistic vs artistic)
    if style == "photoreal":
        # prefer Stability -> HF SDXL -> ClipDrop -> Pollinations -> fallback
        if STABILITY_KEY: candidates.append("stability")
        if HF_TOKEN:
            for m in HF_MODELS_FOR_PHOTOREAL:
                candidates.append(f"hf::{m}")
        if CLIPDROP_KEY: candidates.append("clipdrop")
        candidates.append("pollinations")
        candidates.append("fallback")
    else:
        # artistic: HF openjourney first
        if HF_TOKEN:
            for m in HF_MODELS_ARTISTIC:
                candidates.append(f"hf::{m}")
        if CLIPDROP_KEY: candidates.append("clipdrop")
        if STABILITY_KEY: candidates.append("stability")
        candidates.append("pollinations")
        candidates.append("fallback")

    # sort by provider_score to prefer historically reliable providers
    # compute unique provider keys for hf models we use provider key as "hf::modelname"
    scored = []
    for p in candidates:
        base = p.split("::")[0]
        score = provider_score(p)  # uses p as key (distinct for model variants)
        scored.append((score, p))
    # sort descending by score (higher first), preserve candidate order for ties
    scored.sort(key=lambda x: x[0], reverse=True)
    ordered = [p for _, p in scored]
    # ensure uniqueness while preserving order
    seen = set()
    final = []
    for p in ordered:
        if p not in seen:
            final.append(p)
            seen.add(p)
    log.info(f"Provider order (style={style}): {final}")
    return final

# ====== Генерация изображения: обход провайдеров ======
def generate_image_smart(title: str, keywords: List[str]) -> Optional[str]:
    # Determine style heuristically from title/keywords: prefer photoreal by default
    style = "photoreal"
    text_for_prompt = f"{title}. Keywords: {' '.join(keywords)}"
    # build prompt
    prompt = (
        f"Ultra-realistic photo illustration of {title}. "
        f"{' '.join(keywords)}. Cinematic lighting, professional photography, "
        "shallow depth of field, modern technology, no charts, no diagrams, no text overlays, photorealistic, 8k"
    )

    image_name = unique_image_name("post")
    path = os.path.join(ASSETS_DIR, image_name)

    providers = available_providers(style)
    # map to functions
    for prov in providers:
        log.info(f"Trying provider {prov}")
        if prov.startswith("hf::"):
            model = prov.split("::", 1)[1]
            ok = attempt_with_backoff(lambda p, out: provider_hf_model(p, out, model), prompt, path, prov)
        elif prov == "stability":
            ok = attempt_with_backoff(provider_stability, prompt, path, "stability")
        elif prov == "clipdrop":
            ok = attempt_with_backoff(provider_clipdrop, prompt, path, "clipdrop")
        elif prov == "pollinations":
            ok = attempt_with_backoff(provider_pollinations, prompt, path, "pollinations")
        elif prov == "fallback":
            ok = provider_fallback_png(prompt, path)
            # record fallback as success for stability of pipeline
            record_stat("fallback", ok)
        else:
            ok = False

        if ok:
            # quick validation: try to open with PIL
            try:
                Image.open(path).verify()
                log.info(f"Image successfully created by {prov}: {path}")
                return path
            except Exception as e:
                log.warning(f"Validation failed for image from {prov}: {e}")
                record_stat(prov, False)
                # try next provider

    log.error("Все провайдеры не сработали, и fallback не сохранил изображение.")
    return None

# ====== Сохранение поста ======
def save_post_file(title: str, content: str, image_path: Optional[str], trend_id: str, keywords: List[str]) -> str:
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-zA-Z0-9а-яА-Я\-]+", "-", title.lower()).strip("-")[:60]
    filename = f"{POSTS_DIR}/{today}-{slug}.md"
    image_rel = ""
    if image_path:
        image_rel = f"/{image_path.replace(os.sep, '/')}"
    front_matter = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": image_rel,
        "description": f"{trend_id}",
        "tags": ["ИИ", "технологии"] + (keywords or [])
    }
    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, allow_unicode=True, sort_keys=False)
        f.write("---\n\n")
        f.write(content)
    log.info(f"Saved post: {filename}")
    return filename

# ====== Telegram отправка ======
def escape_md_v2(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

def send_to_telegram(title: str, content: str, image_path: Optional[str]):
    bot = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not bot or not chat:
        log.info("Telegram keys missing, skipping Telegram send")
        return
    teaser = " ".join(content.split()[:30]) + "…"
    caption = f"*{escape_md_v2(title)}*\n\n{escape_md_v2(teaser)}\n\n[Читать на сайте](https://lybra-ai.ru)"
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as ph:
                files = {"photo": (os.path.basename(image_path), ph, "image/png")}
                data = {"chat_id": chat, "caption": caption, "parse_mode": "MarkdownV2"}
                r = requests.post(f"https://api.telegram.org/bot{bot}/sendPhoto", data=data, files=files, timeout=30)
                log.info(f"Telegram sendPhoto status: {r.status_code}")
                if r.status_code != 200:
                    log.warning(f"Telegram sendPhoto error: {r.text}")
        except Exception as e:
            log.warning(f"Telegram exception when sending photo: {e}")
    else:
        # fallback to simple text message
        try:
            msg = f"Новая статья: {title}\n\nЧитать на сайте: https://lybra-ai.ru"
            r = requests.post(f"https://api.telegram.org/bot{bot}/sendMessage", data={"chat_id": chat, "text": msg}, timeout=10)
            log.info(f"Telegram sendMessage status: {r.status_code}")
        except Exception as e:
            log.warning(f"Telegram fallback exception: {e}")

# ====== Основной flow ======
def main():
    log.info("=== START GENERATION ===")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = EMEBED_OR_LOADED := EMEBED_OR_LOADED = EMEBED_OR_LOADED = None
    # try to use cached trends or embedded
    try:
        # try loading cached trends file if exists
        if os.path.exists("trends_cache.json"):
            with open("trends_cache.json", "r", encoding="utf-8") as f:
                cache = json.load(f)
                if time.time() - cache.get("last_update", 0) < 86400:
                    trends = cache.get("trends", EMEBED_OR_LOADED)
    except Exception as e:
        log.warning(f"Unable to read trends cache: {e}")
    if not trends:
        trends = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED = EMEBED_OR_LOADED  # fallback to embedded
        # simpler: use EMBEDDED_TRENDS
        trends = EMBEDDED_TRENDS

    trend = random.choice(trends)
    article_type = random.choice(["Обзор", "Урок", "Статья", "Мастер-класс"])

    # generate article with attempts and anti-politics
    try:
        title = generate_title(client, trend, article_type)
        content = generate_article(client, trend, article_type)
    except Exception as e:
        log.error(f"Article generation failed: {e}")
        return False

    # smart image generation
    try:
        image_path = generate_image_smart(title, trend.get("keywords", []))
    except Exception as e:
        log.error(f"Image generation flow failed unexpectedly: {e}")
        image_path = None

    # save post with unique image name (image_path already unique)
    post_file = save_post_file(title, content, image_path, trend.get("id", ""), trend.get("keywords", []))

    # send to telegram
    try:
        send_to_telegram(title, content, image_path)
    except Exception as e:
        log.warning(f"Telegram send failed: {e}")

    log.info("=== FINISHED ===")
    return True

if __name__ == "__main__":
    try:
        ok = main()
        exit(0 if ok else 1)
    except Exception as e:
        log.exception(f"Unhandled exception: {e}")
        exit(1)
