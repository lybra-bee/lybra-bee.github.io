import os
import random
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO

POSTS_DIR = "content/posts"
IMG_DIR = "static/images/gallery"

# Темы для генерации статей
PROMPTS = [
    "Обзор новой архитектуры нейросети",
    "Урок по использованию Python для ИИ",
    "Мастер-класс: генерация изображений нейросетями",
    "Будущее высоких технологий",
    "Нейросети в медицине",
    "ИИ и кибербезопасность",
    "Как работает обучение с подкреплением",
    "Тенденции машинного обучения 2025",
]

# Темы для генерации изображений
IMAGE_PROMPTS = [
    "futuristic neural network visualization, neon cyberpunk style, high tech background",
    "AI laboratory, futuristic style, neon lights, advanced tech",
    "digital art of artificial intelligence in a futuristic city",
]

# Функция для безопасного имени файла
def sanitize_filename(name: str):
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in name)

# Функция генерации уникального имени изображения
def get_next_image_name():
    os.makedirs(IMG_DIR, exist_ok=True)
    existing = [f for f in os.listdir(IMG_DIR) if f.startswith("post-") and f.endswith(".png")]
    if not existing:
        next_index = 1
    else:
        numbers = [int(f.split('-')[1].split('.')[0]) for f in existing]
        next_index = max(numbers) + 1
    return f"post-{next_index}.png"

# Генерация текста статьи через OpenRouter
def generate_text(title):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY не найден!")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"Ты пишешь статьи для блога про ИИ и технологии. Стиль — обзор, урок или мастер-класс."},
            {"role":"user","content":f"Напиши статью на тему: {title}"}
        ],
        "max_tokens": 1000
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        r.raise_for_status()
        result = r.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Ошибка генерации статьи: {e}")
        return "Ошибка генерации статьи."

# Генерация изображения по промпту
def generate_image(prompt):
    os.makedirs(IMG_DIR, exist_ok=True)
    img_name = get_next_image_name()
    img_path = os.path.join(IMG_DIR, img_name)
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ','%20')}"
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image.save(img_path)
        return img_name
    except Exception as e:
        print(f"Ошибка генерации изображения: {e}")
        return None

# Создание статьи с изображением
def create_post():
    os.makedirs(POSTS_DIR, exist_ok=True)
    title = random.choice(PROMPTS)
    content = generate_text(title)
    img_prompt = random.choice(IMAGE_PROMPTS)
    img_file = generate_image(img_prompt)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}-{sanitize_filename(title)}.md"
    filepath = os.path.join(POSTS_DIR, filename)
    front_matter = f"""+++
title = "{title}"
date = "{today}"
draft = false
image = "/images/gallery/{img_file}"
+++
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter)
        f.write("\n")
        f.write(content)
    print(f"Создан пост: {filepath}")

if __name__ == "__main__":
    create_post()
