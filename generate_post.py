import datetime
import random
import os
import re
import base64
import glob
from groq import Groq  # Официальная библиотека Groq
import requests  # Для OpenRouter

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

# Ограничение до 10 постов (удаляем старые)
post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
if len(post_files) > 9:
    for old_file in post_files[10:]:
        os.remove(old_file)

# Генерация текста через Groq API (используем официальную библиотеку)
groq_key = os.getenv("GROQ_API_KEY")
content = f"# {title}\n\n## {type_}\n\nОшибка генерации текста. Сгенерируйте вручную."
if groq_key:
    try:
        client = Groq(api_key=groq_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты эксперт по ИИ и технологиям. Пиши на русском, информативно и увлекательно."},
                {"role": "user", "content": f"Напишите {type_.lower()} на тему '{title}' (400 слов, для блога). Формат: заголовок H1, подзаголовок H2 ({type_}), текст с абзацами."}
            ],
            model="llama3-8b-8192",  # Доступная модель Groq
            max_tokens=600,
            temperature=0.7
        )
        content = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Ошибка Groq API: {str(e)}")

# Генерация изображения через OpenRouter API
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
prompt_img = f"Generate a futuristic illustration of {title.lower()}, with neural network elements in blue-purple gradient, AI high-tech theme, 800x600 resolution, detailed and vibrant."
image_path = f"{assets_dir}/post-{post_num}.png"
if openrouter_key:
    try:
        openrouter_response = requests.post(openrouter_url, json={
            "model": "stabilityai/stable-diffusion-xl",  # Надёжная модель для изображений
            "messages": [{"role": "user", "content": prompt_img}],
            "max_tokens": 100
        }, headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}, timeout=60)
        openrouter_response.raise_for_status()
        result = openrouter_response.json()
        if result.get("choices"):
            message = result["choices"][0]["message"]
            if "content" in message and "data:image/png;base64," in message["content"]:
                # Парсим base64 из ответа (OpenRouter может возвращать в content)
                image_data_url = message["content"].split("data:image/png;base64,")[1].split('"')[0]
                image_data = base64.b64decode(image_data_url)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_data)
                print(f"Изображение сохранено: {image_path}")
            else:
                print(f"Нет изображения в ответе. Промпт: {prompt_img}")
        else:
            print(f"Ошибка ответа OpenRouter. Промпт: {prompt_img}")
    except Exception as e:
        print(f"Ошибка OpenRouter API: {str(e)}. Сгенерируйте изображение вручную: {prompt_img}")
else:
    print(f"Промпт для изображения: {prompt_img}")

# Сохранение поста
filename = f"{posts_dir}/{today}-{slug}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"---\ntitle: \"{title}\"\ndate: {today} 00:00:00 -0000\nimage: /assets/images/posts/post-{post_num}.png\n---\n{content}\n")
print(f"Сгенерировано: {filename}")
