#!/usr/bin/env python3
"""
Вспомогательные функции для генератора контента Hugo
"""

import re
import os
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import textwrap
import logging

logger = logging.getLogger(__name__)

def generate_slug(text):
    """Генерация SEO-friendly slug из текста"""
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    """Генерация frontmatter для Hugo"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', "'")
    
    frontmatter = f"""---
title: "{escaped_title}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
tags: ["ai", "технологии", "2025", "нейросети"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о тенденциях AI в 2025 году"
---

{content}
"""
    return frontmatter

def generate_enhanced_placeholder(topic):
    """Создание улучшенного placeholder изображения для Hugo"""
    try:
        os.makedirs("static/images/posts", exist_ok=True)
        filename = f"static/images/posts/{generate_slug(topic)}.jpg"
        width, height = 800, 400
        
        # Создаем футуристический фон
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        # Градиентный фон
        for i in range(height):
            r = int(15 + (i/height)*40)
            g = int(23 + (i/height)*60)
            b = int(42 + (i/height)*100)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Сетка (tech grid effect)
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 25))
        for i in range(0, height, 40):
            draw.line([(0, i), (width, i)], fill=(255, 255, 255, 25))
        
        # Текст
        wrapped_text = textwrap.fill(topic, width=35)
        
        # Шрифт
        try:
            font = ImageFont.truetype("Arial.ttf", 22)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
        
        # Позиция текста
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        # Тень текста
        draw.text((x+3, y+3), wrapped_text, font=font, fill="#000000")
        # Основной текст
        draw.text((x, y), wrapped_text, font=font, fill="#ffffff")
        
        # AI badge
        draw.rectangle([(10, height-35), (120, height-10)], fill="#6366f1")
        draw.text((15, height-30), "AI GENERATED", font=ImageFont.load_default(), fill="#ffffff")
        
        img.save(filename, "JPEG", quality=90)
        logger.info(f"🎨 Улучшенный placeholder создан: {filename}")
        return f"/images/posts/{os.path.basename(filename)}"
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания placeholder: {e}")
        return "/images/default.jpg"
