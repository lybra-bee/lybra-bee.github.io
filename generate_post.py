#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import random
import logging
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests
from groq import Groq

# Force flush stdout
class FlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

handler = FlushHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

# Конфигурация
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY не установлен")

client = Groq(api_key=GROQ_API_KEY)

class ArticleGenerator:
    def __init__(self):
        self.max_retries = 4
        self.retry_delay = 2
        
    def groq_request(self, messages, temperature=0.7):
        """Отправка запроса к Groq"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Groq request attempt {attempt}/{self.max_retries}")
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq error (attempt {attempt}): {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
                else:
                    raise
        return None

    def get_trending_topic(self):
        """Получение трендовой темы"""
        logger.info("=== Fetching topic ===")
        
        fallback_topics = [
            "AI automation", "machine learning", "digital transformation", 
            "cloud computing", "data science", "cybersecurity", "blockchain",
            "artificial intelligence", "big data", "IoT", "quantum computing"
        ]
        
        try:
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                titles = re.findall(r'<title>(.*?)</title>', response.text)
                if len(titles) > 1:
                    topic = random.choice(titles[1:min(6, len(titles))])
                    topic = re.sub(r'&#39;', "'", topic)
                    topic = re.sub(r'&quot;', '"', topic)
                    logger.info(f"Topic from Trends: {topic}")
                    return topic
            
            topic = random.choice(fallback_topics)
            logger.info(f"Fallback topic: {topic}")
            return topic
            
        except Exception as e:
            logger.warning(f"Trends error: {e}")
            topic = random.choice(fallback_topics)
            logger.info(f"Fallback topic: {topic}")
            return topic

    def generate_title(self, topic):
        """Генерация заголовка статьи"""
        logger.info(f"Generating title for: {topic}")
        
        prompt = f"""Создай привлекательный заголовок для статьи блога на тему "{topic}".
Заголовок должен быть на русском языке, информативным и SEO-оптимизированным.
Длина: 60-100 символов.
Формат ответа: ЗАГОЛОВОК: [твой заголовок]"""

        response = self.groq_request([
            {"role": "system", "content": "Ты профессиональный копирайтер и SEO-специалист."},
            {"role": "user", "content": prompt}
        ])
        
        match = re.search(r'ЗАГОЛОВОК:\s*(.+)', response, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
        else:
            title = response.strip().split('\n')[0][:100]
        
        logger.info(f"Title: {title}")
        return title

    def generate_outline(self, title):
        """Генерация структуры статьи"""
        logger.info("Generating outline")
        
        prompt = f"""Создай подробный план статьи с заголовком: "{title}"
Статья должна содержать 5-7 разделов на русском языке.
Формат:
1. [Название раздела]
2. [Название раздела]
...
Последний раздел всегда "Заключение"."""

        response = self.groq_request([
            {"role": "system", "content": "Ты профессиональный редактор."},
            {"role": "user", "content": prompt}
        ])
        
        sections = re.findall(r'\d+\.\s*(.+)', response)
        if not sections:
            sections = ["Введение", "Основная часть", "Заключение"]
        
        logger.info(f"Outline: {len(sections)} sections")
        return sections

    def generate_section(self, title, section_name, context=""):
        """Генерация текста для раздела"""
        logger.info(f"Generating section: {section_name}")
        
        prompt = f"""Напиши раздел "{section_name}" для статьи "{title}".
Контекст: {context[:300] if context else "Нет"}

Требования:
- Объём: 300-500 слов
- Стиль: информативный, профессиональный
- Используй списки где уместно"""

        response = self.groq_request([
            {"role": "system", "content": "Ты технический писатель."},
            {"role": "user", "content": prompt}
        ])
        
        return response.strip()

    def generate_article(self, title):
        """Генерация полной статьи"""
        outline = self.generate_outline(title)
        sections_content = []
        
        context = ""
        for section in outline:
            content = self.generate_section(title, section, context)
            sections_content.append(f"## {section}\n\n{content}")
            context += f"{section}: {content[:200]}... "
            time.sleep(0.5)
        
        body = "\n\n".join(sections_content)
        logger.info(f"Article length: {len(body)} chars")
        return body

    def generate_english_prompt(self, title):
        """Перевод заголовка в английский промпт для изображения"""
        try:
            prompt = f"""Translate this Russian article title to English (5-7 words): "{title}"
Then create a short image generation prompt describing: technology, business, modern style.
Return ONLY the English prompt, no explanation."""
            
            response = self.groq_request([
                {"role": "system", "content": "You create image prompts."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            clean = response.strip().strip('"').strip("'").strip()
            clean = re.sub(r'^(Prompt|Image):\s*', '', clean, flags=re.IGNORECASE)
            # Убираем переносы строк
            clean = clean.replace('\n', ' ').strip()
            return clean[:100]
            
        except Exception as e:
            logger.error(f"Prompt generation error: {e}")
            return "technology business automation, modern digital illustration, professional"

    def generate_image(self, title):
        """
        Генерация изображения через Hugging Face Inference API
        Используем бесплатные модели без ограничений
        """
        logger.info("=== IMAGE GENERATION START ===")
        
        if not HF_API_TOKEN:
            logger.error("HF_API_TOKEN not set!")
            return None
        
        try:
            # Получаем английский промпт
            english_prompt = self.generate_english_prompt(title)
            logger.info(f"English prompt: {english_prompt}")
            
            full_prompt = f"{english_prompt}, high quality, detailed, professional illustration, clean design"
            logger.info(f"Full prompt: {full_prompt}")
            
            # Список бесплатных моделей для попыток
            models = [
                "runwayml/stable-diffusion-v1-5",  # SD 1.5 - стабильная
                "CompVis/stable-diffusion-v1-4",   # SD 1.4
                "stabilityai/stable-diffusion-2-1", # SD 2.1
            ]
            
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            
            for model in models:
                try:
                    logger.info(f"Trying model: {model}")
                    API_URL = f"https://api-inference.huggingface.co/models/{model}"
                    
                    payload = {
                        "inputs": full_prompt,
                    }
                    
                    # Для некоторых моделей нужны дополнительные параметры
                    if "stable-diffusion" in model:
                        payload["parameters"] = {
                            "width": 512,  # Меньше размер = быстрее генерация
                            "height": 512,
                            "num_inference_steps": 25,
                            "guidance_scale": 7.5,
                            "seed": random.randint(1, 100000)
                        }
                    
                    logger.info(f"Sending request to {model}...")
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                    
                    logger.info(f"Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        # Успех! Сохраняем изображение
                        image_bytes = response.content
                        
                        # Проверяем, что это действительно изображение
                        if len(image_bytes) < 1000:
                            logger.warning(f"Response too small ({len(image_bytes)} bytes), probably error")
                            continue
                        
                        # Сохраняем локально
                        image_filename = f"ai_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        image_path = Path('assets/images/posts') / image_filename
                        image_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        logger.info(f"Image saved: {image_path} ({len(image_bytes)} bytes)")
                        return f"/assets/images/posts/{image_filename}"
                        
                    elif response.status_code == 503:
                        logger.warning(f"Model {model} is loading, trying next...")
                        continue
                    elif response.status_code == 401:
                        logger.error("Invalid HF token!")
                        return None
                    else:
                        logger.warning(f"Model {model} returned {response.status_code}: {response.text[:100]}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error with model {model}: {e}")
                    continue
            
            logger.error("All HF models failed")
            return None
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def save_post(self, title, body, image_url):
        """Сохранение поста"""
        logger.info("Saving post...")
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Транслитерация
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': '-', ',': '', '.': '', '!': '', '?': '', ':': '', ';': ''
        }
        
        slug = ''.join(translit_map.get(c, c) for c in title.lower())
        slug = re.sub(r'[^a-z0-9]+', '-', slug)[:50].strip('-')
        
        filename = f"{date_str}-{slug}.md"
        filepath = Path('_posts') / filename
        filepath.parent.mkdir(exist_ok=True)
        
        front_matter = f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} +0300
categories: ai technology
image: "{image_url}"
---

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(front_matter + body)
        
        logger.info(f"Post saved: {filepath}")
        return filepath

    def send_telegram(self, title, filepath, image_url):
        """Отправка в Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not set")
            return
        
        try:
            message = f"📝 Новая статья: {title}\n\n🖼 Изображение: {image_url}"
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            logger.info(f"Telegram response: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    def cleanup_old_posts(self, keep_days=30):
        """Удаление старых постов"""
        try:
            posts_dir = Path('_posts')
            if not posts_dir.exists():
                return
            
            now = datetime.now()
            for post_file in posts_dir.glob('*.md'):
                date_match = re.match(r'(\d{4}-\d{2}-\d{2})', post_file.name)
                if date_match:
                    post_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    if (now - post_date).days > keep_days:
                        post_file.unlink()
                        logger.info(f"Removed old post: {post_file.name}")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def run(self):
        """Основной процесс"""
        logger.info("=" * 50)
        logger.info("STARTING GENERATION")
        logger.info("=" * 50)
        
        image_url = None
        
        try:
            # 1. Тема и заголовок
            topic = self.get_trending_topic()
            title = self.generate_title(topic)
            
            # 2. Статья
            body = self.generate_article(title)
            
            # 3. Изображение (до 3 попыток с разными моделями)
            for attempt in range(3):
                logger.info(f"Image attempt {attempt + 1}/3")
                image_url = self.generate_image(title)
                if image_url:
                    break
                time.sleep(5)
            
            # Fallback если не сработало
            if not image_url:
                logger.error("All image attempts failed, using Unsplash fallback")
                # Unsplash - надёжный fallback с реальными фото
                keywords = urllib.parse.quote("technology,computer,business")
                image_url = f"https://source.unsplash.com/1024x768/?{keywords}"
            
            logger.info(f"Final image: {image_url}")
            
            # 4. Сохранение и отправка
            filepath = self.save_post(title, body, image_url)
            self.send_telegram(title, filepath, image_url)
            self.cleanup_old_posts()
            
            logger.info("SUCCESS")
            
        except Exception as e:
            logger.error(f"FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    generator = ArticleGenerator()
    generator.run()
