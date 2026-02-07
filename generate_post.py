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
from io import BytesIO
import base64

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
            clean = clean.replace('\n', ' ').strip()
            return clean[:100]
            
        except Exception as e:
            logger.error(f"Prompt generation error: {e}")
            return "technology business automation, modern digital illustration, professional"

    def generate_image_craiyon(self, title):
        """
        Генерация изображения через Craiyon (бывший DALL-E mini)
        Полностью бесплатно, без API ключа
        """
        logger.info("=== IMAGE GENERATION (Craiyon) ===")
        
        try:
            # Получаем английский промпт
            english_prompt = self.generate_english_prompt(title)
            logger.info(f"Prompt: {english_prompt}")
            
            # Craiyon API endpoint
            url = "https://api.craiyon.com/v3"
            
            payload = {
                "prompt": english_prompt,
                "token": None,  # Не требуется для базового использования
                "model": "photo",  # art, drawing, photo, none
                "negative_prompt": "",
                "version": "35s5hfwn9n78gb06"
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            logger.info("Sending request to Craiyon...")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Craiyon возвращает список изображений в base64
                images = data.get('images', [])
                if images:
                    # Берём первое изображение
                    img_data = images[0]
                    
                    # Декодируем base64
                    if ',' in img_data:
                        img_data = img_data.split(',')[1]
                    
                    image_bytes = base64.b64decode(img_data)
                    
                    # Сохраняем локально
                    image_filename = f"craiyon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    image_path = Path('assets/images/posts') / image_filename
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    logger.info(f"Image saved: {image_path} ({len(image_bytes)} bytes)")
                    return f"/assets/images/posts/{image_filename}"
                else:
                    logger.error("No images in response")
                    return None
            else:
                logger.error(f"Craiyon error: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Craiyon error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def generate_image_pollinations(self, title):
        """
        Fallback: Pollinations.ai (если Craiyon не сработает)
        """
        logger.info("=== IMAGE GENERATION (Pollinations fallback) ===")
        
        try:
            english_prompt = self.generate_english_prompt(title)
            encoded_prompt = urllib.parse.quote(english_prompt)
            
            seed = random.randint(1, 100000)
            image_url = (
                f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                f"?width=1024&height=768&nologo=true&seed={seed}"
            )
            
            logger.info(f"Trying Pollinations: {image_url[:80]}...")
            
            # Скачиваем изображение
            response = requests.get(image_url, timeout=60)
            if response.status_code == 200 and len(response.content) > 1000:
                image_filename = f"pollinations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                image_path = Path('assets/images/posts') / image_filename
                image_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Image saved: {image_path}")
                return f"/assets/images/posts/{image_filename}"
            else:
                logger.error(f"Pollinations failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Pollinations error: {e}")
            return None

    def generate_image(self, title):
        """Генерация изображения с fallback"""
        # Попытка 1: Craiyon
        image_url = self.generate_image_craiyon(title)
        if image_url:
            return image_url
        
        # Попытка 2: Pollinations
        logger.warning("Craiyon failed, trying Pollinations...")
        image_url = self.generate_image_pollinations(title)
        if image_url:
            return image_url
        
        # Попытка 3: Unsplash (гарантированно работает)
        logger.warning("All AI generation failed, using Unsplash...")
        keywords = urllib.parse.quote("technology,computer,business,abstract")
        return f"https://source.unsplash.com/1024x768/?{keywords}"

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
        
        try:
            # 1. Тема и заголовок
            topic = self.get_trending_topic()
            title = self.generate_title(topic)
            
            # 2. Статья
            body = self.generate_article(title)
            
            # 3. Изображение (с несколькими fallback)
            image_url = self.generate_image(title)
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
