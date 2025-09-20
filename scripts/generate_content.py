#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime
from slugify import slugify
import frontmatter
from pathlib import Path

# — Настройки папок
POSTS_DIR = Path("content/posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# — Получаем ключи из окружения
groq_key = os.getenv("GROQ_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")
deepai_key = os.getenv("DEEPAI_API_KEY")  # для изображения

def generate_text_openrouter(prompt: str) -> str:
    if not openrouter_key:
        return None
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openrouter/auto",  # или другая, доступная модель
        "messages": [
            {"role": "system", "content": "Ты — автор технических статей для блога."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1000,
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    # отдаём контент
    return data["choices"][0]["message"]["content"]

def generate_text_groq(prompt: str) -> str:
    if not groq_key:
        return None
    # Предполагая, что Groq поддерживает совместимый с OpenAI чат-API
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-70b-versatile", 
        "messages": [
            {"role": "system", "content": "Ты — автор технических статей для блога."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1000,
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def generate_image_deepai(prompt: str, output_path: Path) -> bool:
    """Попытка через DeepAI Text2Img"""
    if not deepai_key:
        return False
    try:
        url = "https://api.deepai.org/api/text2img"
        headers = {
            "Api-Key": deepai_key
        }
        data = {
            "text": prompt
        }
        r = requests.post(url, headers=headers, data=data)
        r.raise_for_status()
        res = r.json()
        # ответ содержит URL изображения
        img_url = res.get("output_url")
        if not img_url:
            return False
        img_resp = requests.get(img_url)
        img_resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(img_resp.content)
        return True
    except Exception as e:
        print("DeepAI image error:", e)
        return False

def generate_image_fallback(output_path: Path) -> bool:
    try:
        url = "https://picsum.photos/1200/675"
        r = requests.get(url)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print("Fallback image error:", e)
        return False

def save_post(title: str, body: str, image_filename: str):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    slug = slugify(title)[:60]
    md_path = POSTS_DIR / f"{date_str}-{slug}.md"
    image_rel = f"/{IMAGES_DIR}/{image_filename}"
    metadata = {
        "title": title,
        "date": datetime.utcnow().isoformat(),
        "tags": ["ai","auto"],
        "featured_image": image_rel,
        "draft": False
    }
    post = frontmatter.Post(body, **metadata)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))
    print("Post saved:", md_path)

def main():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    title = f"Автоматическая статья {today}"
    prompt_text = f"Сгенери статью для технического блога-портфолио на тему AI, дата: {today}. Включи заголовок, введение, несколько секций, заключение."
    content = None

    # Попытки по приоритету
    if openrouter_key:
        print("Using OpenRouter for text generation")
        content = generate_text_openrouter(prompt_text)
    elif groq_key:
        print("Using Groq for text generation")
        content = generate_text_groq(prompt_text)
    else:
        print("❌ Нет ключей для генерации текста! Завершаю с ошибкой.")
        sys.exit(1)

    if not content:
        print("❌ Текст не сгенерировался! Завершаю с ошибкой.")
        sys.exit(1)

    # Выбор картинки
    image_filename = f"{slugify(title)}.jpg"
    image_path = IMAGES_DIR / image_filename
    image_prompt = f"{title}. Illustration for technical blog post, high quality."

    if deepai_key:
        print("Попытка создать изображение через DeepAI")
        ok_img = generate_image_deepai(image_prompt, image_path)
    else:
        ok_img = False

    if not ok_img:
        print("DeepAI image failed or no key, пытаюсь fallback")
        if not generate_image_fallback(image_path):
            print("❌ Не удалось создать изображение ни одним методом! Завершаю с ошибкой.")
            sys.exit(1)

    # Сохраняем пост
    save_post(title, content, image_filename)
    print("✅ Всё сгенерировано успешно")
    sys.exit(0)

if __name__ == "__main__":
    main()
