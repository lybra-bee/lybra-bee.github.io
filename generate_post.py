import datetime
import random
import requests
import os
import re
import base64
import glob

themes = ["Прогресс нейронных сетей", "Этика ИИ", "Квантовый ИИ", "Генеративные модели", "Робототехника", "Блокчейн ИИ", "AR/VR", "Кибер ИИ", "NLP", "Автономные системы"]
types = ["Обзор", "Урок", "Мастер-класс", "Статья"]

today = datetime.date.today()
title = random.choice(themes)
slug = re.sub(r'[^а-яА-Яa-zA-Z0-9-]', '-', title.lower().replace(" ", "-"))
type_ = random.choice(types)

# Папки и номер поста
posts_dir = '_posts'
assets_dir = 'assets/images/posts'
os.makedirs(assets_dir, exist_ok=True)
os.makedirs(posts_dir, exist_ok=True)
post_num = len([f for f in os.listdir(posts_dir) if f.endswith('.md')]) + 1

# Ограничение до 10 постов
post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
if len(post_files) > 9:  # Удаляем старые, оставляя 10
    for old_file in post_files[10:]:
        os.remove(old_file)

# Генерация текста через Groq API
groq_key = os.getenv("GROQ_API_KEY")
groq_url = "https://api.grok.x.ai/v1/completions"  # Проверьте endpoint
prompt_text = f"Напишите {type_.lower()} на русском языке на тему '{title}' (400 слов, в стиле ИИ/технологий, для блога). Формат: заголовок H1, подзаголовок H2 ({type_}), текст с абзацами, без лишних заголовков."

try:
    groq_response = requests.post(groq_url, json={
        "model": "grok-3b",  # Или другая модель
        "prompt": prompt_text,
        "max_tokens": 600
    }, headers={"Authorization": f"Bearer {groq_key}"}, timeout=30)
    groq_response.raise_for_status()
    content = groq_response.json().get("choices", [{}])[0].get("text", f"# {title}\n\n## {type_}\n\nОшибка генерации текста.")
except Exception as e:
    content = f"# {title}\n\n## {type_}\n\nОшибка Groq API: {str(e)}. Сгенерируйте текст вручную."

# Генерация изображения через OpenRouter API
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
prompt_img = f"Generate a futuristic illustration of {title.lower()}, with neural network elements in blue-purple gradient, AI high-tech theme, 800x600 resolution, detailed and vibrant."

try:
    openrouter_response = requests.post(openrouter_url, json={
        "model": "google/gemini-2.5-flash-image-preview",  # Замените, если нужно
        "messages": [{"role": "user", "content": prompt_img}],
        "modalities": ["image", "text"],
        "max_tokens": 100
    }, headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}, timeout=60)
    openrouter_response.raise_for_status()
    result = openrouter_response.json()
    image_path = f"{assets_dir}/post-{post_num}.png"
    if result.get("choices"):
        message = result["choices"][0]["message"]
        if message.get("images"):
            image_data_url = message["images"][0]["image_url"]["url"]
            image_data = base64.b64decode(image_data_url.split(',')[1])
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)
            print(f"Изображение сохранено: {image_path}")
        else:
            print(f"Нет изображения в ответе. Промпт: {prompt_img}")
    else:
        print(f"Ошибка ответа OpenRouter. Промпт: {prompt_img}")
except Exception as e:
    print(f"Ошибка OpenRouter API: {str(e)}. Сгенерируйте изображение вручную: {prompt_img}")

# Сохранение поста
filename = f"{posts_dir}/{today}-{slug}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"---\ntitle: \"{title}\"\ndate: {today} 00:00:00 -0000\nimage: /assets/images/posts/post-{post_num}.png\n---\n{content}\n")
print(f"Сгенерировано: {filename}")
