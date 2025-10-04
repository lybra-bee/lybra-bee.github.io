import datetime
import random
import os
import re
import glob
from groq import Groq
import requests

types = ["Обзор", "Урок", "Мастер-класс", "Статья"]

today = datetime.date.today()
type_ = random.choice(types)

posts_dir = '_posts'
assets_dir = 'assets/images/posts'
os.makedirs(assets_dir, exist_ok=True)
os.makedirs(posts_dir, exist_ok=True)

# Определение следующего номера изображения
image_files = glob.glob(f"{assets_dir}/*.png") + glob.glob(f"{assets_dir}/*.jpg")
post_num = len(image_files) + 1 if image_files else 1

post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
if len(post_files) > 39:
    for old_file in post_files[40:]:
        os.remove(old_file)

# Генерация заголовка через Groq API
groq_key = os.getenv("GROQ_API_KEY")
title = "Современные тенденции в искусственном интеллекте"  # заголовок по умолчанию

if groq_key:
    try:
        client = Groq(api_key=groq_key)
        title_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "Ты эксперт по ИИ и высоким технологиям. Создай креативные заголовки на русском языке (5-10 слов) на основе последних трендов в области искусственного интеллекта, машинного обучения и высоких технологий на октябрь 2025 года."
                },
                {
                    "role": "user", 
                    "content": f"Придумай один заголовок {type_.lower()} (5-10 слов) на актуальную тему в области ИИ и высоких технологий. Добавь вопрос или цифру для привлечения внимания (например, '5 способов ИИ улучшить IoT в 2025?'). Только заголовок, без пояснений."
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=50,
            temperature=0.8
        )
        title = title_completion.choices[0].message.content.strip()
        title = re.sub(r'^["\']|["\']$', '', title)
        print(f"Заголовок сгенерирован: {title}")
    except Exception as e:
        print(f"Ошибка генерации заголовка: {str(e)}")

slug = re.sub(r'[^а-яА-Яa-zA-Z0-9-]', '-', title.lower().replace(" ", "-"))

# Генерация полного текста статьи
content = f"# {title}\n\n## {type_}\n\nОшибка генерации текста. Сгенерируйте вручную."

if groq_key:
    try:
        article_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "Ты профессиональный автор технических статей. Пиши на русском языке информативно, структурированно и увлекательно. Создавай законченные статьи с введением, основной частью и заключением, оптимизированные для ИИ-поиска (ChatGPT, Yandex.Neyro, GigaChat) в 2025 году. Включи факты, статистику, вопросы, ссылки на источники (например, x.ai, habr.com, yandex.ru) и таблицу сравнения."
                },
                {
                    "role": "user", 
                    "content": f"Напиши {type_.lower()} на тему '{title}' объемом 1500-3000 слов. Структура: H1 — заголовок, H2 — тип статьи, затем: H2 'Введение' с вопросом, H2 'Основные тренды' (3-5 подзаголовков H3 с фактами), H2 'Сравнение' (таблица 3x3), H2 'Практические шаги' (список 5-10 пунктов), H2 'Заключение' с вопросом к читателю. Используй данные октября 2025 года."
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=3000,  # Увеличено для 1500-3000 слов
            temperature=0.7
        )
        content = article_completion.choices[0].message.content
        content = re.sub(r'<[^>]+>', '', content)  # Удаление всех HTML-тегов
        print("Статья сгенерирована успешно через Groq.")
    except Exception as e:
        print(f"Ошибка генерации статьи: {str(e)}")

# Перевод заголовка на английский для промпта изображения
if groq_key:
    try:
        translation = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты переводчик. Переводи на английский точно и естественно."},
                {"role": "user", "content": f"Переведи на английский: {title}"}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=30,
            temperature=0.1
        )
        title_en = translation.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка перевода: {str(e)}")
        title_en = title.lower().replace(" ", "-")
else:
    title_en = title.lower().replace(" ", "-")

# Генерация изображения через Clipdrop API
prompt_img = f"Futuristic digital art illustration of {title_en}, neural networks AI technology, cyberpunk style, blue purple gradient, high quality detailed, 2025 trends"
image_path = f"{assets_dir}/post-{post_num}.png"
image_generated = False

clipdrop_key = os.getenv("CLIPDROP_API_KEY")
if clipdrop_key:
    clipdrop_url = "https://clipdrop-api.co/text-to-image/v1"
    print(f"Генерация изображения для: {title_en}")
    try:
        clipdrop_response = requests.post(
            clipdrop_url,
            files={'prompt': (None, prompt_img)},
            headers={'x-api-key': clipdrop_key},
            timeout=30
        )
        print(f"Статус генерации изображения: {clipdrop_response.status_code}")
        if clipdrop_response.status_code == 200:
            with open(image_path, "wb") as img_file:
                img_file.write(clipdrop_response.content)
            print(f"Изображение успешно сохранено: {image_path}")
            image_generated = True
        else:
            try:
                error_details = clipdrop_response.json()
                print(f"Ошибка Clipdrop: {error_details}")
            except ValueError:
                print(f"Ошибка Clipdrop: {clipdrop_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к Clipdrop API: {str(e)}")

# Fallback для ручной генерации изображения
if not image_generated:
    print(f"Не удалось сгенерировать изображение. Сгенерируйте вручную по промпту: {prompt_img}")

# Сохранение поста
filename = f"{posts_dir}/{today}-{slug}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"---\ntitle: \"{title}\"\ndate: {today} 00:00:00 -0000\nlayout: post\nimage: /assets/images/posts/post-{post_num}.png\ntags: [ИИ, технологии, {type_.lower()}]\n---\n{content}\n")
print(f"Сгенерирован пост: {filename}")
