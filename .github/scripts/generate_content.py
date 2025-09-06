#!/usr/bin/env python3
import os
import time
import json
import requests
import logging
from pathlib import Path
from datetime import datetime, timezone
import shutil

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("generator")

# Пути
CONTENT_DIR = Path("content/posts")
GALLERY_DIR = Path("static/images/gallery")
CONTENT_DIR.mkdir(parents=True, exist_ok=True)
GALLERY_DIR.mkdir(parents=True, exist_ok=True)

# Ключи из GitHub Secrets
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

# ---------- ТЕКСТ СТАТЬИ ----------

def prompt_text():
    return (
        "Напиши развернутую профессиональную статью на русском языке о современных "
        "тенденциях в области нейросетей и высоких технологий (фокус — 2024–2025 годы). "
        "Объём 500–800 слов. Формат — Markdown с заголовками (##, ###). "
        "Аудитория — разработчики и технические менеджеры. Включи summary, технические разделы и вывод."
    )

def gen_text_openrouter():
    log.info("📝 Генерация статьи через OpenRouter")
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": prompt_text()}],
        "max_tokens": 1500,
        "temperature": 0.7,
    }
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def gen_text_groq():
    log.info("📝 Генерация статьи через Groq")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt_text()}],
        "max_tokens": 1500,
        "temperature": 0.7,
    }
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def generate_article_text():
    try:
        return gen_text_openrouter()
    except Exception as e:
        log.warning(f"⚠️ OpenRouter ошибка: {e}, пробуем Groq")
        return gen_text_groq()

# ---------- FUSIONBRAIN IMAGE ----------

def get_fusion_pipeline_id():
    headers = {"X-Key": f"Key {FUSIONBRAIN_API_KEY}", "X-Secret": f"Secret {FUSION_SECRET_KEY}"}
    resp = requests.get("https://api-key.fusionbrain.ai/key/api/v1/pipelines", headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    for p in data:
        if "kandinsky" in p.get("name", "").lower():
            return p["id"]
    return data[0]["id"]

def generate_image_fusion(prompt, pipeline_id, width=1024, height=512, attempts=20, delay=3):
    log.info("🎨 Генерация изображения через FusionBrain")
    headers = {"X-Key": f"Key {FUSIONBRAIN_API_KEY}", "X-Secret": f"Secret {FUSION_SECRET_KEY}"}
    params = {
        "type": "GENERATE",
        "numImages": 1,
        "width": width,
        "height": height,
        "generateParams": {"query": prompt}
    }
    files = {
        "pipeline_id": (None, pipeline_id),
        "params": (None, json.dumps(params), "application/json")
    }
    resp = requests.post("https://api-key.fusionbrain.ai/key/api/v1/pipeline/run", headers=headers, files=files, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    uuid = data.get("uuid")
    if not uuid:
        raise RuntimeError("FusionBrain response lacks uuid")

    for _ in range(attempts):
        time.sleep(delay)
        status_resp = requests.get(f"https://api-key.fusionbrain.ai/key/api/v1/pipeline/status/{uuid}", headers=headers, timeout=15)
        status_resp.raise_for_status()
        st = status_resp.json()
        if st.get("status") == "DONE":
            files_list = st.get("result", {}).get("files", [])
            if files_list and isinstance(files_list[0], dict) and files_list[0].get("url"):
                img_url = files_list[0]["url"]
                img_resp = requests.get(img_url, timeout=30)
                img_resp.raise_for_status()
                return img_resp.content
        elif st.get("status") == "FAIL":
            raise RuntimeError(f"FusionBrain FAIL: {st.get('errorDescription')}")
    raise RuntimeError("FusionBrain timeout")

# ---------- СОХРАНЕНИЕ ----------

def save_post(title, body, img_bytes):
    safe_title = title.replace('"', "'")
    slug = "-".join(title.lower().split()[:6])
    post_dir = CONTENT_DIR / slug
    post_dir.mkdir(exist_ok=True)

    img_path = post_dir / "image.png"
    with open(img_path, "wb") as f:
        f.write(img_bytes)

    gallery_img = GALLERY_DIR / f"{slug}.png"
    with open(gallery_img, "wb") as f:
        f.write(img_bytes)

    content = "\n".join([
        "---",
        f'title: "{safe_title}"',
        f'date: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}',
        "draft: false",
        f'image: "image.png"',
        'tags: ["ai","технологии","2025"]',
        "---",
        "",
        body
    ])
    with open(post_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(content)
    return slug

def move_home_to_prev():
    home = Path("content/_index.md")
    if home.exists():
        prev_slug = f"archived-{int(time.time())}"
        newdir = CONTENT_DIR / prev_slug
        newdir.mkdir(exist_ok=True)
        home.rename(newdir / "index.md")

def create_home_index(slug, title, body):
    home = Path("content/_index.md")
    content = "\n".join([
        "---",
        f'title: "{title}"',
        f'date: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}',
        f'image: "/images/gallery/{slug}.png"',
        "---",
        "",
        body
    ])
    home.write_text(content, encoding="utf-8")

def prune_posts(keep=5):
    dirs = [d for d in CONTENT_DIR.iterdir() if d.is_dir()]
    dirs_sorted = sorted(dirs, key=lambda d: (d / "index.md").stat().st_mtime, reverse=True)
    for d in dirs_sorted[keep:]:
        shutil.rmtree(d)

# ---------- MAIN ----------

def main():
    body = generate_article_text()
    title_line = body.splitlines()[0].strip("# ").strip()
    title = title_line or "Новая статья"
    log.info(f"✅ Сгенерирован заголовок: {title}")

    pipeline_id = get_fusion_pipeline_id()
    img_bytes = generate_image_fusion(title, pipeline_id)

    slug = save_post(title, body, img_bytes)

    move_home_to_prev()
    create_home_index(slug, title, body)
    prune_posts(keep=5)

    log.info("🎉 Генерация завершена успешно")

if __name__ == "__main__":
    main()
