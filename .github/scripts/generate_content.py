#!/usr/bin/env python3
import os
import json
import requests
import time
import yaml
from slugify import slugify
from datetime import datetime

# Пути
POSTS_DIR = 'content/posts'
ASSETS_DIR = 'assets/images/posts'
GALLERY_FILE = 'data/gallery.yaml'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"
    }
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role":"user","content": prompt}]
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data['choices'][0]['message']['content']
        return text
    except Exception as e:
        print(f"❌ Ошибка генерации статьи: {e}")
        return None

def generate_image(prompt, slug):
    headers = {
        "X-Key": f"Key {os.environ['FUSIONBRAIN_API_KEY']}",
        "X-Secret": f"Secret {os.environ['FUSION_SECRET_KEY']}"
    }

    # Получаем pipeline
    r = requests.get("https://api-key.fusionbrain.ai/key/api/v1/pipelines", headers=headers)
    r.raise_for_status()
    pipeline_id = r.json()[0]['id']

    params = {
        "type": "GENERATE",
        "width": 1024,
        "height": 1024,
        "numImages": 1,
        "generateParams": {
            "query": prompt
        }
    }
    files = {
        'pipeline_id': (None, pipeline_id),
        'params': (None, json.dumps(params), 'application/json')
    }

    r = requests.post("https://api-key.fusionbrain.ai/key/api/v1/pipeline/run", headers=headers, files=files)
    r.raise_for_status()
    request_id = r.json()['uuid']

    # Проверяем статус
    attempts = 15
    while attempts > 0:
        r = requests.get(f"https://api-key.fusionbrain.ai/key/api/v1/pipeline/status/{request_id}", headers=headers)
        r.raise_for_status()
        status = r.json()['status']
        if status == 'DONE':
            b64_img = r.json()['result']['files'][0]
            img_path = os.path.join(ASSETS_DIR, f"{slug}.png")
            with open(img_path, "wb") as f:
                f.write(bytes(b64_img, "utf-8"))  # если Base64, декодируй: base64.b64decode()
            return img_path
        time.sleep(5)
        attempts -= 1
    return None

def update_gallery(slug, img_path, title):
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
            gallery = yaml.safe_load(f) or []
    else:
        gallery = []

    gallery.insert(0, {"src": f"/images/posts/{slug}.png", "alt": title, "title": title})
    with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(gallery, f, allow_unicode=True)

def save_article(title, text, slug):
    date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    front_matter = f"---\ntitle: \"{title}\"\ndate: {date}\nmodel: GPT-4.1-mini\nimage: /images/posts/{slug}.png\n---\n\n"
    content = front_matter + text
    path = os.path.join(POSTS_DIR, f"{slug}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def main():
    text = generate_article()
    if not text:
        print("❌ Статья не сгенерирована")
        return

    title = text.split("\n")[0][:50]
    slug = slugify(title)

    img_path = generate_image(title, slug)
    if not img_path:
        print("⚠️ Изображение не сгенерировано, используем placeholder")
        img_path = "/images/placeholder.jpg"

    article_path = save_article(title, text, slug)
    update_gallery(slug, img_path, title)

    print(f"✅ Статья сохранена: {article_path}")
    print(f"✅ Галерея обновлена: {GALLERY_FILE}")

if __name__ == "__main__":
    main()
