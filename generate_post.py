#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import random
import logging
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests
from groq import Groq

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Конфигурация
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Проверка обязательных переменных
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
        logger.info("🌍 Fetching Google Trends topic")
        
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
                    logger.info(f"🎯 Topic from Trends: {topic}")
                    return topic
            
            topic = random.choice(fallback_topics)
            logger.info(f"🎯 Fallback topic: {topic}")
            return topic
            
        except Exception as e:
            logger.warning(f"Trends error: {e}, using fallback")
            topic = random.choice(fallback_topics)
            logger.info(f"🎯 Fallback topic: {topic}")
            return topic

    def generate_title(self, topic):
        """Генерация заголовка статьи"""
        logger.info(f"✍️ Generating title: {topic}")
        
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
        
        logger.info(f"✅ Title: {title}")
        return title

    def generate_outline(self, title):
        """Генерация структуры статьи"""
        logger.info("📚 Generating outline")
        
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
        
        logger.info(f"✅ Outline generated: {len(sections)} sections")
        return sections

    def generate_section(self, title, section_name, context=""):
        """Генерация текста для одного раздела"""
        logger.info(f"🧩 Generating section: {section_name}")
        
        prompt = f"""Напиши раздел "{section_name}" для статьи "{title}".
Контекст предыдущих разделов: {context[:500] if context else "Нет"}

Требования:
- Объём: 300-500 слов
- Стиль: информативный, профессиональный, но доступный
- Используй маркированные списки где уместно
- Добавь практические советы или примеры
- Тон: экспертный, но дружелюбный"""

        response = self.groq_request([
            {"role": "system", "content": "Ты профессиональный технический писатель и блогер."},
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
            time.sleep(1)
        
        body = "\n\n".join(sections_content)
        logger.info(f"📏 Body length: {len(body)}")
        return body

    def generate_image_prompt(self, title):
        """Создание английского промпта для изображения"""
        prompt = f"""Create a short English image generation prompt (10-15 words) based on this Russian article title: "{title}"
The prompt should describe a professional illustration suitable for a tech blog.
Focus on: technology, business, modern office, digital innovation.
Return ONLY the English prompt, nothing else."""

        try:
            response = self.groq_request([
                {"role": "system", "content": "You create image generation prompts."},
                {"role": "user", "content": prompt}
            ], temperature=0.5)
            
            clean_prompt = response.strip().strip('"').strip("'")
            enhanced = f"{clean_prompt}, professional illustration, clean design, high quality, detailed"
            return enhanced
        except Exception as e:
            logger.error(f"Failed to generate image prompt: {e}")
            return "technology business concept, modern office, digital innovation, professional illustration"

    def generate_image(self, title):
        """Генерация изображения через Pollinations.ai"""
        logger.info("🎨 Generating image with Pollinations.ai")
        
        try:
            # Получаем промпт
            image_prompt = self.generate_image_prompt(title)
            logger.info(f"📝 Image prompt: {image_prompt}")
            
            # Кодируем для URL
            encoded_prompt = urllib.parse.quote(image_prompt)
            
            # Формируем URL
            seed = random.randint(1, 10000)
            image_url = (
                f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                f"?width=1024&height=768&nologo=true&enhance=true&seed={seed}"
            )
            
            logger.info(f"🔗 Image URL: {image_url[:100]}...")
            
            # Проверяем доступность (Pollinations генерирует на лету, поэтому просто проверим что URL валидный)
            # Делаем GET запрос для проверки
            logger.info("📡 Testing image URL...")
            response = requests.get(image_url, timeout=60, stream=True)
            
            if response.status_code == 200:
                # Проверяем, что это действительно изображение
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    logger.info(f"✅ Image verified: {content_type}")
                    return image_url
                else:
                    logger.warning(f"Unexpected content type: {content_type}")
                    return None
            else:
                logger.warning(f"Image URL returned status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Image generation timeout")
            return None
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None

    def save_post(self, title, body, image_url):
        """Сохранение поста в файл"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        slug = self.transliterate(title.lower())
        slug = re.sub(r'[^a-z0-9]+', '-', slug)[:50].strip('-')
        
        filename = f"{date_str}-{slug}.md"
        filepath = Path('_posts') / filename
        
        filepath.parent.mkdir(exist_ok=True)
        
        front_matter = f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} +0300
categories: ai technology
image: {image_url}
---

"""
        
        full_content = front_matter + body
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"📝 Post saved: {filepath}")
        return filepath

    def transliterate(self, text):
        """Простая транслитерация русского текста"""
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': '-', ',': '', '.': '', '!': '', '?': '', ':': '', ';': ''
        }
        
        result = ''
        for char in text:
            result += translit_dict.get(char, char)
        return result

    def send_telegram(self, title, filepath, image_url=None):
        """Отправка уведомления в Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not set")
            return
        
        try:
            # Отправляем текст
            message = f"📝 Новая статья опубликована!\n\n<b>{title}</b>"
            if image_url:
                message += f"\n\n🖼 <a href='{image_url}'>Изображение</a>"
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("📬 Telegram sent")
            else:
                logger.warning(f"Telegram error: {response.status_code} - {response.text}")
                
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
                    days_old = (now - post_date).days
                    
                    if days_old > keep_days:
                        post_file.unlink()
                        logger.info(f"🧹 Removed old post: {post_file.name}")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def run(self):
        """Основной процесс генерации"""
        logger.info("=== START ===")
        image_url = None
        
        try:
            # 1. Получаем тему
            topic = self.get_trending_topic()
            
            # 2. Генерируем заголовок
            title = self.generate_title(topic)
            
            # 3. Генерируем статью
            body = self.generate_article(title)
            
            # 4. Генерируем изображение
            try:
                image_url = self.generate_image(title)
            except Exception as e:
                logger.error(f"Image generation failed: {e}")
                image_url = None
            
            # Если изображение не сгенерировалось, используем placeholder
            if not image_url:
                logger.warning("⚠ Using placeholder image")
                safe_title = urllib.parse.quote(title[:30])
                image_url = f"https://via.placeholder.com/1024x768/4a90e2/ffffff?text={safe_title}"
            
            logger.info(f"🖼 Final image URL: {image_url}")
            
            # 5. Сохраняем
            filepath = self.save_post(title, body, image_url)
            
            # 6. Отправляем в Telegram
            self.send_telegram(title, filepath, image_url)
            
            # 7. Очистка старых постов
            self.cleanup_old_posts()
            
            logger.info("=== SUCCESS ===")
            
        except Exception as e:
            logger.error(f"=== FAILED: {e} ===")
            import traceback
            logger.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    generator = ArticleGenerator()
    generator.run()
