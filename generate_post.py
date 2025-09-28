import datetime
import random
import os
import re
import glob
from groq import Groq
import requests

themes = ["Прогресс нейронных сетей", "Этика ИИ", "Квантовый ИИ", "Генеративные модели", "Робототехника", "Блокчейн ИИ", "AR/VR", "Кибер ИИ", "NLP", "Автономные системы"]
types = ["Обзор", "Урок", "Мастер-класс", "Статья"]

today = datetime.date.today()
title = random.choice(themes)
slug = re.sub(r'[^а-яА-Яa-zA-Z0-9-]', '-', title.lower().replace(" ", "-"))
type_ = random.choice(types)

posts_dir = '_posts'
assets_dir = 'assets/images/posts'
os.makedirs(assets_dir, exist_ok=True)
os.makedirs(posts_dir, exist_ok=True)

# === Определяем правильный номер картинки ===
existing_images = [f for f in os.listdir(assets_dir) if f.startswith("post-") and f.endswith(".png")]
if existing_images:
    max_num = max(int(re.search(r'post-(\d+)\.png', f).group(1)) for f in existing_images)
    post_num = max_num + 1
else:
    post_num = 1

image_path = f"{assets_dir}/post-{post_num}.png"

# === Оставляем только 10 последних постов ===
post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
if len(post_files) > 9:
    for old_file in post_files[10:]:
        os.remove(old_file)

# === Генерация текста через Groq API ===
groq_key = os.getenv("GROQ_API_KEY")
content = f"# {title}\n\n## {type_}\n\nОшибка генерации текста. Сгенерируйте вручную."
if groq_key:
    try:
        client = Groq(api_key=groq_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты эксперт по ИИ и технологиям. Пиши на русском, информативно и увлекательно. Не добавляй HTML-теги."},
                {"role": "user", "content": f"Напишите {type_.lower()} на тему '{title}' (400 слов, для блога). Формат: заголовок H1, подзаголовок H2 ({type_}), текст с абзацами."}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=600,
            temperature=0.7
        )
        content = chat_completion.choices[0].message.content
        content = re.sub(r'<[^>]+>', '', content)  # Удаляем HTML-теги
        print("Текст сгенерирован успешно через Groq.")
    except Exception as e:
        print(f"Ошибка Groq API: {str(e)}")

# === Перевод темы на английский для промпта ===
if groq_key:
    try:
        translation = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты переводчик. Переводи на английский точно и естественно."},
                {"role": "user", "content": f"Переведи на английский: {title}"}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=20,
            temperature=0.1
        )
        title_en = translation.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка перевода: {str(e)}")
        title_en = title.lower().replace(" ", "-")
else:
    title_en = title.lower().replace(" ", "-")

# === Генерация изображения через Clipdrop API ===
prompt_img = f"Futuristic illustration of {title_en}, with neural network elements in blue-purple gradient, AI high-tech theme."
image_generated = False

clipdrop_key = os.getenv("CLIPDROP_API_KEY")
if clipdrop_key:
    clipdrop_url = "https://clipdrop-api.co/text-to-image/v1"
    print(f"Инициализация запроса к Clipdrop. Промпт: {prompt_img}")
    try:
        clipdrop_response = requests.post(
            clipdrop_url,
            files={'prompt': (None, prompt_img)},
            headers={'x-api-key': clipdrop_key},
            timeout=30
        )
        if clipdrop_response.status_code == 200:
            with open(image_path, "wb") as img_file:
                img_file.write(clipdrop_response.content)
            print(f"Изображение успешно сохранено: {image_path}")
            image_generated = True
        else:
            print(f"Ошибка Clipdrop ({clipdrop_response.status_code}): {clipdrop_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к Clipdrop API: {str(e)}")

if not image_generated:
    print(f"Не удалось сгенерировать изображение. Сгенерируйте вручную: {prompt_img}")

# === Сохраняем пост с правильной ссылкой на картинку ===
filename = f"{posts_dir}/{today}-{slug}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(
        f"---\n"
        f"title: \"{title}\"\n"
        f"date: {today} 00:00:00 -0000\n"
        f"image: /assets/images/posts/post-{post_num}.png\n"
        f"---\n"
        f"{content}\n"
    )

print(f"Сгенерировано: {filename}")
