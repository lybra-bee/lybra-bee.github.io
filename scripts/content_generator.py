import os
import sys
import random
import subprocess
from datetime import datetime
import json
from pathlib import Path


from PIL import Image, ImageDraw, ImageFilter, ImageFont


# Параметры
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = REPO_ROOT / 'content' / 'posts'
IMAGES_DIR = REPO_ROOT / 'assets' / 'images' / 'posts'
CONTENT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')


# Темы и шаблоны для генерации без ключей
TYPES = ['Обзор', 'Урок', 'Мастер-класс', 'Статья']
TOPICS = [
'обучение нейросетей',
'генерация изображений',
'реалистичное видео из текста',
'оптимизация моделей',
'этика и ИИ',
'инфраструктура для ИИ',
]


PARAGRAPHS = [
'Сегодня мир искусственного интеллекта развивается невероятно быстро. В этой статье мы разберёмся с ключевыми концепциями и практическими шагами.',
'Практические советы помогут вам быстрее запустить прототип и снизить затраты на обучение модели.',
'Мы пройдём пошагово: от подготовки данных до деплоя и мониторинга качества модели в продакшн.',
'Обратите внимание на ошибки, которые чаще всего допускают новички — и как их избегать.'
]




def generate_text_fallback(topic, post_type):
title = f"{post_type}: {topic.capitalize()} — краткое руководство"
date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
intro = f"В этом {post_type.lower()}е мы обсудим {topic}."
body = '\n\n'.join(random.sample(PARAGRAPHS, k=3))
conclusion = 'Подводя итог — экспериментируйте и не бойтесь тестировать новые подходы.'
content = f"---\ntitle: \"{title}\"\ndate: {date}\ntags: [\"{topic}\"]\nsummary: \"Короткое руководство по {topic}\"\n---\n\n{intro}\n\n{body}\n\n## Пример кода\n\n```\n# Псевдокод\nprint(\"Hello, AI\")\n```\n\n{conclusion}\n"
return title, content




def generate_image_fallback(text_prompt, filename):
# создаём абстрактную картинку по шаблону — бесплатно
w, h = 1200, 675
img = Image.new('RGB', (w, h), color=(20, 20, 30))
draw = ImageDraw.Draw(img)


# несколько цветных эллипсов
for i in range(8):
bbox = [random.randint(-200, w), random.randint(-200, h), random.randint(0, w+200), random.randint(0, h+200)]
color = tuple(random.randint(60, 230) for _ in range(3))
draw.ellipse(bbox, fill=color, outline=None)


img = img.filter(ImageFilter.GaussianBlur(radius=6))


# добавляем заголовок
print('Готово. Файл:', md_path, 'Изображение:', img_path)
