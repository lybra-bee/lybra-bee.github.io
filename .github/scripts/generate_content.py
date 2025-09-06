#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import requests
import shutil
import logging
import time
from pathlib import Path

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Пути ---
CONTENT_DIR = Path("content/posts")
OLD_DIR = CONTENT_DIR / "old"
GALLERY_DIR = Path("static/images/gallery")
GALLERY_DIR.mkdir(parents=True, exist_ok=True)
OLD_DIR.mkdir(parents=True, exist_ok=True)

# --- Ключи из GitHub Secrets ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSION_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")

# --- FusionBrain API ---
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = 'https://api-key.fusionbrain.ai/'
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate_image(self, prompt, pipeline_id, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        data = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        return response.json()['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            attempts -= 1
            time.sleep(delay)
        raise Exception("Не удалось получить изображение FusionBrain за отведённое время")


# --- Функции генерации статьи ---
def generate_article_groq(prompt="Напиши статью про нейросети и высокие технологии, свежие тренды 2025 года."):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY не задан")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {"prompt": prompt, "max_tokens": 800}
    try:
        response = requests.post("https://api.groq.ai/v1/complete", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        text = data.get("completion") or data.get("text") or ""
        logging.info("📝 Статья сгенерирована через Groq")
        return text
    except Exception as e:
        logging.warning(f"Ошибка Groq: {e}")
        return None


def generate_article_hf(prompt):
    """Фолбек Hugging Face GPT-Neo"""
    url = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-2.7B"
    try:
        response = requests.post(url, headers={"Accept": "application/json"}, json={"inputs": prompt}, timeout=30)
        response.raise_for_status()
        text = response.json()[0]['generated_text']
        logging.info("📝 Статья сгенерирована через Hugging Face GPT-Neo")
        return text
    except Exception as e:
        logging.warning(f"Ошибка Hugging Face: {e}")
        return None


def generate_article_textsynth(prompt):
    """Фолбек TextSynth публичный API"""
    url = "https://textsynth.com/api/v1/engines/gptj_6B/completions"
    payload = {"prompt": prompt, "max_tokens": 800}
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        text = response.json()['text']
        logging.info("📝 Статья сгенерирована через TextSynth")
        return text
    except Exception as e:
        logging.warning(f"Ошибка TextSynth: {e}")
        return None


def generate_article():
    prompt = "Напиши статью про нейросети и высокие технологии, свежие тренды 2025 года."
    text = generate_article_groq(prompt)
    if not text:
        text = generate_article_hf(prompt)
    if not text:
        text = generate_article_textsynth(prompt)
    if not text:
        raise Exception("Не удалось сгенерировать статью ни через один API")
    # Заголовок — первая строка
    lines = text.split("\n")
    title = lines[0].strip() if lines else "Нейросети и высокие технологии"
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else text
    return title, content


def save_article(title, content):
    # Сохраняем старые статьи
    all_posts = sorted(CONTENT_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    while len(all_posts) >= 5:
        old_post = all_posts.pop()
        shutil.move(str(old_post), OLD_DIR / old_post.name)

    # Сохраняем новую статью
    filename = f"{title.replace(' ', '-').replace(':','').replace('/','')}.md"
    filepath = CONTENT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: {title}\n---\n\n{content}\n")
    logging.info(f"📄 Статья сохранена: {filepath}")
    return filepath


def generate_image_for_article(title):
    if not FUSION_API_KEY or not FUSION_SECRET_KEY:
        logging.warning("Нет ключей FusionBrain, изображение не сгенерировано")
        return None
    api = FusionBrainAPI(FUSION_API_KEY, FUSION_SECRET_KEY)
    pipeline_id = api.get_pipeline()
    uuid = api.generate_image(title, pipeline_id)
    files = api.check_generation(uuid)
    # Сохраняем изображение
    image_data = requests.get(files[0]).content
    image_path = GALLERY_DIR / f"{title.replace(' ','-')}.png"
    with open(image_path, "wb") as f:
        f.write(image_data)
    logging.info(f"🎨 Изображение сохранено: {image_path}")
    return image_path


def main():
    title, content = generate_article()
    save_article(title, content)
    generate_image_for_article(title)


if __name__ == "__main__":
    main()
