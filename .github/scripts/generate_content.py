#!/usr/bin/env python3
"""
Генератор контента для Hugo блога с AI-статьями и изображениями
"""

import os
import requests
import random
from datetime import datetime, timezone
import re
import logging
import argparse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = "8006769060:AAEGAKhjUeuAXfnsQWtdLcKpAjkJrrGQ1Fk"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # Замените на ваш chat_id

def generate_ai_trend_topic():
    """Генерация темы статьи"""
    trends = [
        "Искусственный интеллект в веб-разработке 2025",
        "Машинное обучение для мобильных приложений",
        "Нейросети для анализа больших данных",
        "Компьютерное зрение в медицинской диагностике",
        "Generative AI для создания контента",
        "Автономные системы и робототехника",
        "Квантовые вычисления и AI",
        "Этичный искусственный интеллект",
        "Edge AI и IoT устройства",
        "Персональные AI ассистенты"
    ]
    return random.choice(trends)

def generate_article_content(topic):
    """Генерация текста статьи"""
    # Заглушка - в реальности используйте Groq/OpenRouter API
    return f"""# {topic}

## Введение
{topic} - это одна из самых перспективных технологий 2025 года.

## Основные преимущества
- Автоматизация процессов
- Улучшение качества данных
- Персонализация пользовательского опыта

## Заключение
Будущее выглядит promising с развитием AI технологий.

*Статья сгенерирована автоматически*
"""

def generate_article_image(topic):
    """Генерация изображения через Telegram бота"""
    try:
        prompt = f"{topic}, digital art, futuristic, 4k, high quality"
        
        # Отправляем запрос боту на генерацию
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"/generate {prompt}"
            }
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Запрос на генерацию отправлен: {topic}")
            return f"/images/posts/{generate_slug(topic)}.jpg"
        else:
            logger.error(f"❌ Ошибка отправки запроса: {response.text}")
            return "/images/default.jpg"
            
    except Exception as e:
        logger.error(f"❌ Ошибка генерации изображения: {e}")
        return "/images/default.jpg"

def generate_slug(text):
    """Генерация slug"""
    text = text.lower().replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return re.sub(r'-+', '-', text)[:50]

def main():
    parser = argparse.ArgumentParser(description='Генератор AI контента')
    parser.add_argument('--count', type=int, default=1, help='Количество статей')
    args = parser.parse_args()
    
    for i in range(args.count):
        topic = generate_ai_trend_topic()
        logger.info(f"📝 Генерация статьи {i+1}: {topic}")
        
        # Генерация контента
        content = generate_article_content(topic)
        image_path = generate_article_image(topic)
        
        # Сохранение статьи
        slug = generate_slug(topic)
        filename = f"content/posts/{slug}.md"
        
        os.makedirs("content/posts", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"""---
title: "{topic}"
date: {datetime.now().strftime('%Y-%m-%d')}
image: "{image_path}"
draft: false
tags: ["ai", "технологии"]
categories: ["Искусственный интеллект"]
---

{content}
""")
        
        logger.info(f"✅ Статья сохранена: {filename}")

if __name__ == "__main__":
    main()
