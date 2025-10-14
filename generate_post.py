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
        
        # Рандомизация стилей заголовков для разнообразия
        title_styles = [
            "С вопросом для вовлечения: 'Как [тренд] изменит [отрасль] в 2025?'",
            "С цифрой: 'Топ-5 [трендов] в [теме] для 2025 года'",
            "Провокационный: '[Шокирующий факт]: почему [тренд] — будущее ИИ?'",
            "Сторителлинг: 'От [старого] к [новому]: эволюция [темы] в 2025'",
            "Юмористический: 'ИИ в 2025: [смешной сценарий] или реальность?'"
        ]
        random_style = random.choice(title_styles)
        
        title_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "Ты эксперт по ИИ и высоким технологиям. Создай креативные заголовки на русском языке (5-10 слов) на основе последних трендов в области искусственного интеллекта, машинного обучения и высоких технологий на октябрь 2025 года. Создавай заголовки, которые провоцируют любопытство, используют эмоциональный хук (удивление, страх, вдохновение) и адаптированы под тип статьи (обзор — аналитический, урок — практический). Избегай шаблонов, делай их уникальными каждый раз."
                },
                {
                    "role": "user", 
                    "content": f"Придумай один заголовок {type_.lower()} (5-10 слов) на актуальную тему в области ИИ и высоких технологий. Используй стиль: {random_style}. Добавь элемент сюрприза или уникальный угол. Только заголовок, без пояснений."
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

# Выбор подтем для разнообразия статей
subthemes = ["Agentic AI и автономные агенты", "RAG для улучшения генерации", "Sovereign AI и национальные модели", "Physical AI в робототехнике", "Этика ИИ и регуляции", "Квантовое машинное обучение", "AI для устойчивого развития", "Edge AI в IoT"]
selected_subthemes = random.sample(subthemes, random.randint(3, 5))
subthemes_str = ', '.join(selected_subthemes)

# Генерация полного текста статьи
content = f"# {title}\n\n## {type_}\n\nОшибка генерации текста. Сгенерируйте вручную."

if groq_key:
    try:
        # Улучшенный system prompt для полезных статей с сохранением SEO
        system_prompt = """Ты профессиональный автор технических статей по ИИ с 10-летним опытом. Пиши на русском языке увлекательно, как в Forbes или Habr: используй сторителлинг, аналогии, цитаты экспертов (Elon Musk, Andrew Ng), риторические вопросы. Делай контент полезным: включай actionable insights, реальные кейсы (xAI Grok, OpenAI agents, Yandex AI), статистику из 2025 (Gartner: 'AI market $500B', McKinsey: '70% компаний используют AI'). Избегай шаблонов, повторений и filler-текста. Варьируй стиль: мотивирующий для уроков, аналитический для статей. Оптимизируй для SEO: ключевые слова естественно, ссылки на источники (x.ai, habr.com, yandex.ru/blog, mckinsey.com, forbes.com, gartner.com, ibm.com). Добавь ссылку на https://lybra-bee.github.io/lybra-ai-lab/ в введении и заключении как хаб для экспериментов. Для разнообразия: рандомно выбирай подтемы из трендов (Agentic AI, RAG, Sovereign AI, Physical AI, AI ethics, quantum ML, AI in sustainability, edge AI). Избегай кода, фокусируйся на insights."""

        # Динамический user prompt в зависимости от type_ с рандомизацией элементов
        if type_ == "Обзор":
            unique_elements = random.choice(["инфографику в виде нумерованных списков", "цитаты от экспертов", "сравнение с прошлыми годами"])
            user_content = f"Напиши обзор на тему '{title}' объемом 1500–3000 слов, интегрируя подтемы {subthemes_str}. Структура: H1 — заголовок, H2 — тип статьи, H2 'Введение' (с хуком-историей, 200 слов), H2 'Ключевые тренды' (4-6 H3 с кейсами, статистикой, аналогиями, 300 слов каждый), H2 'Сравнение технологий' (таблица 4x4 с плюсами/минусами), H2 'Прогнозы на 2026' (3-5 сценариев с обоснованиями, 200 слов), H2 'Заключение' (с вызовом к действию, 150 слов). Добавь {unique_elements}. Используй реальные примеры, избегай кода."
        elif type_ == "Урок":
            unique_elements = random.choice(["чек-листы после шагов", "мотивирующие примеры успеха", "аналогии из повседневной жизни"])
            user_content = f"Напиши урок на тему '{title}' объемом 1500–3000 слов, интегрируя подтемы {subthemes_str}. Структура: H1 — заголовок, H2 — тип статьи, H2 'Введение' (с вопросом, 200 слов), H2 'Подготовка' (2-3 H3 с инструментами, 200 слов), H2 'Шаги урока' (5-8 H3 с практическими инструкциями, примерами, 250 слов каждый), H2 'Сравнение методов' (таблица 3x3), H2 'Практические советы' (5-10 пунктов, 150 слов), H2 'Заключение' (с вопросом, 150 слов). Добавь {unique_elements}. Избегай кода, фокусируйся на шагах."
        elif type_ == "Мастер-класс":
            unique_elements = random.choice(["ролевые сценарии", "реальные кейсы из компаний", "расширенные упражнения"])
            user_content = f"Напиши мастер-класс на тему '{title}' объемом 1500–3000 слов, интегрируя подтемы {subthemes_str}. Структура: H1 — заголовок, H2 — тип статьи, H2 'Введение' (с вопросом, 200 слов), H2 'Необходимые инструменты' (3-5 H3, 200 слов), H2 'Практические упражнения' (4-6 H3 с сценариями, 300 слов каждый), H2 'Сравнение результатов' (таблица 4x3), H2 'Расширенные техники' (5-7 пунктов, 200 слов), H2 'Заключение' (с вопросом, 150 слов). Добавь {unique_elements}. Используй реальные кейсы."
        elif type_ == "Статья":
            unique_elements = random.choice(["дебаты за/против", "статистика с графиками в тексте", "прогнозы с источниками"])
            user_content = f"Напиши аналитическую статью на тему '{title}' объемом 1500–3000 слов, интегрируя подтемы {subthemes_str}. Структура: H1 — заголовок, H2 — тип статьи, H2 'Введение' (с вопросом, 200 слов), H2 'Анализ трендов' (3-5 H3 с фактами, 300 слов каждый), H2 'Сравнение подходов' (таблица 3x4), H2 'Практические рекомендации' (5-10 пунктов, 200 слов), H2 'Заключение' (с вопросом, 150 слов). Добавь {unique_elements}. Добавь статистику и источники."

        article_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=3000,
            temperature=0.7
        )
        content = article_completion.choices[0].message.content
        content = re.sub(r'<[^>]+>', '', content)  # Удаление HTML-тегов
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

# Улучшенный промпт для изображения с фотореализмом и разнообразием
styles = [
    "photorealistic ultra-detailed photo, 8K, realistic shadows and lighting, cinematic composition",
    "hyper-realistic render, like a stock photo from Getty Images, diverse people interacting with tech",
    "conceptual art with real-world elements, high-res, vibrant colors, reflecting 2025 trends",
    "infographic-style visualization, photo-real elements blended with diagrams, clean and modern",
    "sci-fi realistic scene, like from a movie poster, dynamic action, diverse environments"
]
random_style = random.choice(styles)
subthemes_keywords = ' '.join([theme.lower() for theme in selected_subthemes])
prompt_img = f"Photorealistic image of {title_en} in 2025 AI trends, incorporating {subthemes_keywords}, {random_style}, high quality, detailed textures, diverse composition that captures the essence: people using AI agents in daily life or quantum computers in lab. Avoid abstract; make it look like a real photo."

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
    f.write(f"""---
title: "{title}"
date: {today} 00:00:00 -0000
layout: post
image: /assets/images/posts/post-{post_num}.png
image_alt: "ИИ и IoT 2025: {title}"
description: "{type_.lower()} о трендах ИИ 2025 года: {title.lower()}"
tags: [ИИ, технологии, {type_.lower()}]
---
{content}
""")
print(f"Сгенерирован пост: {filename}")
