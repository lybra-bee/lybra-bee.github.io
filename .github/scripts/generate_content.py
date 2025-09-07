#!/usr/bin/env python3
import os
import json
import requests
import time
import base64
import logging
from datetime import datetime
from slugify import slugify
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSION_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")
BASE_URL = 'https://api-key.fusionbrain.ai/'

AUTH_HEADERS = {
    'X-Key': f'Key {FUSION_API_KEY}',
    'X-Secret': f'Secret {FUSION_SECRET_KEY}',
}

# Папки
POSTS_DIR = 'content/posts'
ASSETS_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)

def generate_title():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и создай ёмкий заголовок для статьи."
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    # OpenRouter
    try:
        logging.info("📝 Генерация заголовка через OpenRouter...")
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip().replace('"', '')
        logging.info("✅ Заголовок получен через OpenRouter")
        return title, "OpenRouter GPT"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")

    # Groq fallback
    try:
        logging.info("📝 Генерация заголовка через Groq...")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post("https://api.groq.com/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip().replace('"', '')
        logging.info("✅ Заголовок получен через Groq")
        return title, "Groq GPT"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации заголовка: {e}")
        return "Новая статья", "None"

def generate_article(title):
    prompt = f"Напиши статью на 400-600 слов по заголовку: {title}"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    # OpenRouter
    try:
        logging.info("📝 Генерация статьи через OpenRouter...")
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter GPT"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")

    # Groq fallback
    try:
        logging.info("📝 Генерация статьи через Groq...")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post("https://api.groq.com/v1/chat/completions",
                          headers=headers,
                          json={"model": "g
