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

# Force flush stdout для немедленного вывода логов
class FlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Настройка логирования
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
        """Отправка запроса к Groq с повторами при ошибках"""
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
            "AI tools", "machine learning", "automation", 
            "digital transformation", "productivity apps",
            "chatbots", "neural networks", "cloud computing"
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
Статья должна содержать 5-7 разделов.
Каждый раздел должен иметь чёткое название на русском языке.
Формат:
1. [Название раздела]
2. [Название раздела]
...
Последний раздел всегда "Заключение"."""

        response = self.groq_request([
            {"role": "system", "content": "Ты профессиональный редактор и контент-менеджер."},
            {"role": "user", "content": prompt}
        ])
        
        sections = re.findall(r'\d+\.\s*(.+)', response)
        if not sections:
            sections = ["Введение", "Основная часть", "Заключение"]
        
        logger.info(f"Outline: {len(sections)} sections")
        return sections

    def generate_section(self, title, section_name, context=""):
        """Генерация текста для одного раздела"""
        logger.info(f"Generating section: {section_name}")
        
        prompt = f"""Напиши раздел "{section_name}" для статьи "{title}".
Контекст предыдущих разделов: {context[:500] if context else "Нет"}

Требования:
- Объём: 300-500 слов
- Стиль: информативный, профессиональный, но доступный
- Используй маркированные списки где уместно
- Добавь практические советы или примеры"""

        response = self.groq_request([
            {"role": "system", "content": "Ты профессиональный технический писатель."},
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

    def generate_image(self, title):
        """
        Генерация изображения через Pollinations.ai
        Возвращает URL изображения или None
        """
        logger.info("=== IMAGE GENERATION START ===")
        
        try:
            # Создаём промпт на основе заголовка
            # Упрощаем: используем ключевые слова из заголовка
            keywords = title.replace(':', '').replace(',', '').replace('.', '')[:50]
            
            # Базовый промпт на английском
            base_prompt = f"technology business illustration, {keywords}, modern digital art, professional, clean design, blue colors"
            encoded_prompt = urllib.parse.quote(base_prompt)
            
            # Формируем URL
            seed = random.randint(1, 100000)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={seed}"
            
            logger.info(f"Image URL: {image_url}")
            logger.info(f"Prompt: {base_prompt}")
            
            # Проверяем URL (Pollinations генерирует на лету)
            logger.info("Testing image URL...")
            
            # Делаем HEAD запрос для проверки
            try:
                response = requests.head(image_url, timeout=30, allow_redirects=True)
                logger.info(f"HEAD status: {response.status_code}")
                
                if response.status_code in [200, 301, 302]:
                    logger.info("Image URL is valid")
                    logger.info("=== IMAGE GENERATION SUCCESS ===")
                    return image_url
                else:
                    logger.warning(f"Unexpected status: {response.status_code}")
                    return None
                    
            except Exception as e:
                logger.error(f"Request failed: {e}")
                # Даже если проверка не сработала, URL может быть рабочим
                # Вернём его на свой страх и риск
                logger.info("Returning URL without verification")
                return image_url
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def save_post(self, title, body, image_url):
        """Сохранение поста в файл"""
        logger.info("Saving post...")
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Транслитерация для имени файла
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': '-', ',': '', '.': '', '!': '', '?': '', ':': '', ';': ''
        }
        
        slug = ''
        for char in title.lower():
            slug += translit_map.get(char, char)
        
        slug = re.sub(r'[^a-z0-9]+', '-', slug)[:50].strip('-')
        filename = f"{date_str}-{slug}.md"
        filepath = Path('_posts') / filename
        
        filepath.parent.mkdir(exist_ok=True)
        
        # Front matter
        front_matter = f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} +0300
categories: ai technology
image: "{image_url}"
---

"""
        
        full_content = front_matter + body
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Post saved: {filepath}")
        return filepath

    def send_telegram(self, title, filepath, image_url):
        """Отправка уведомления в Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not set")
            return
        
        try:
            message = f"📝 Новая статья: {title}\n\n🖼 Изображение: {image_url}"
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            logger.info(f"Telegram response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Telegram sent successfully")
            else:
                logger.warning(f"Telegram error: {response.text}")
                
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    def cleanup_old_posts(self, keep_days=30):
        """Удаление старых постов"""
        try:
            posts_dir = Path('_posts')
            if not posts_dir.exists():
                return
            
            now = datetime.now()
            count = 0
            for post_file in posts_dir.glob('*.md'):
                date_match = re.match(r'(\d{4}-\d{2}-\d{2})', post_file.name)
                if date_match:
                    post_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    days_old = (now - post_date).days
                    
                    if days_old > keep_days:
                        post_file.unlink()
                        count += 1
                        logger.info(f"Removed old post: {post_file.name}")
            
            if count > 0:
                logger.info(f"Total removed: {count} posts")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def run(self):
        """Основной процесс генерации"""
        logger.info("=" * 50)
        logger.info("STARTING ARTICLE GENERATION")
        logger.info("=" * 50)
        
        image_url = None
        
        try:
            # 1. Тема
            topic = self.get_trending_topic()
            
            # 2. Заголовок
            title = self.generate_title(topic)
            
            # 3. Статья
            body = self.generate_article(title)
            
            # 4. Изображение (с несколькими попытками)
            logger.info("Attempting image generation...")
            for attempt in range(3):
                logger.info(f"Image attempt {attempt + 1}/3")
                image_url = self.generate_image(title)
                if image_url:
                    break
                time.sleep(2)
            
            if not image_url:
                logger.error("All image attempts failed, using placeholder")
                safe_title = urllib.parse.quote(title[:20])
                image_url = f"https://via.placeholder.com/1024x768/4a90e2/ffffff?text={safe_title}"
            
            logger.info(f"Final image URL: {image_url}")
            
            # 5. Сохранение
            filepath = self.save_post(title, body, image_url)
            
            # 6. Telegram
            self.send_telegram(title, filepath, image_url)
            
            # 7. Очистка
            self.cleanup_old_posts()
            
            logger.info("=" * 50)
            logger.info("SUCCESS")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error("=" * 50)
            logger.error(f"FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 50)
            raise

if __name__ == "__main__":
    generator = ArticleGenerator()
    generator.run()
