import datetime
import random
import os
import re
import base64
import glob
import time
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
post_num = len([f for f in os.listdir(posts_dir) if f.endswith('.md')]) + 1

post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
if len(post_files) > 9:
    for old_file in post_files[10:]:
        os.remove(old_file)

# Генерация текста через Groq API
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
            model="llama-3.1-8b-instant",
            max_tokens=600,
            temperature=0.7
        )
        content = chat_completion.choices[0].message.content
        print("Текст сгенерирован успешно через Groq.")
    except Exception as e:
        print(f"Ошибка Groq API: {str(e)}")

# Генерация изображения
prompt_img = f"Futuristic illustration of {title.lower()}, with neural network elements in blue-purple gradient, AI high-tech theme, 800x600 resolution, detailed and vibrant."
image_path = f"{assets_dir}/post-{post_num}.png"
image_generated = False

# Clipdrop API (основной с диагностикой)
clipdrop_key = os.getenv("CLIPDROP_API_KEY")
if clipdrop_key and not image_generated:
    try:
        clipdrop_url = "https://clipdrop-api.co/text-to-image/v1"
        clipdrop_response = requests.post(
            clipdrop_url,
            data={'prompt': prompt_img, 'width': 800, 'height': 600},  # Явно указываем размер
            headers={'x-api-key': clipdrop_key},
            timeout=30
        )
        clipdrop_response.raise_for_status()
        with open(image_path, "wb") as img_file:
            img_file.write(clipdrop_response.content)
        print(f"Изображение сгенерировано через Clipdrop: {image_path}")
        image_generated = True
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка Clipdrop API (HTTP {e.response.status_code}): {e.response.text}")
    except Exception as e:
        print(f"Ошибка Clipdrop API: {str(e)}")

# DeepAI API (резерв)
deepai_key = os.getenv("DEEPAI_API_KEY")
if deepai_key and not image_generated:
    try:
        deepai_url = "https://api.deepai.org/api/text2img"
        deepai_response = requests.post(
            deepai_url,
            files={'text': prompt_img},
            headers={'api-key': deepai_key}
        )
        deepai_response.raise_for_status()
        result = deepai_response.json()
        if result.get("output_url"):
            img_response = requests.get(result["output_url"])
            img_response.raise_for_status()
            with open(image_path, "wb") as img_file:
                img_file.write(img_response.content)
            print(f"Изображение сгенерировано через DeepAI: {image_path}")
            image_generated = True
        else:
            print(f"Нет изображения в ответе DeepAI: {result}")
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка DeepAI API (HTTP {e.response.status_code}): {e.response.text}")
    except Exception as e:
        print(f"Ошибка DeepAI API: {str(e)}")

# Fallback для ручной генерации
if not image_generated:
    print(f"Не удалось сгенерировать изображение ни через один API. Сгенерируйте вручную: {prompt_img}")

# Сохранение поста
filename = f"{posts_dir}/{today}-{slug}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"---\ntitle: \"{title}\"\ndate: {today} 00:00:00 -0000\nimage: /assets/images/posts/post-{post_num}.png\n---\n{content}\n")
print(f"Сгенерировано: {filename}")
