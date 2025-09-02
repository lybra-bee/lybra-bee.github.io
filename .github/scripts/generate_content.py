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
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = "8006769060:AAEGAKhjUeuAXfnsQWtdLcKpAjkJrrGQ1Fk"
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')

# ======== Генерация темы ========
def generate_ai_trend_topic():
    """Генерация случайной темы про AI тренды"""
    current_trends_2025 = [
        "Multimodal AI интеграция текста изображений и аудио в единых моделях",
        "AI агенты автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение прорыв в производительности",
        "Нейроморфные вычисления энергоэффективные архитектуры нейросетей",
        "Generative AI создание контента кода и дизайнов искусственным интеллектом",
        "Edge AI обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности предиктивная защита от угроз",
        "Этичный AI ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare диагностика разработка лекарств и персонализированная медицина",
        "Автономные системы беспилотный транспорт и робототехника"
    ]
    
    application_domains = [
        "в веб разработке и cloud native приложениях",
        "в мобильных приложениях и IoT экосистемах", 
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес аналитике",
        "в компьютерной безопасности и киберзащите"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году"
    ]
    
    return random.choice(topic_formats)

# ======== Генерация текста статьи ========
def generate_article_content(topic):
    """Генерация текста статьи через AI API"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    # Пробуем разные API
    if groq_key:
        try:
            return generate_with_groq(groq_key, "llama-3.1-70b-versatile", topic)
        except Exception as e:
            logger.error(f"❌ Groq error: {e}")
    
    if openrouter_key:
        try:
            return generate_with_openrouter(openrouter_key, "anthropic/claude-3-sonnet", topic)
        except Exception as e:
            logger.error(f"❌ OpenRouter error: {e}")
    
    # Fallback
    return generate_fallback_content(topic)

def generate_with_groq(api_key, model_name, topic):
    """Генерация через Groq API"""
    prompt = f"""Напиши развернутую статью на тему: '{topic}' на русском языке.

Требования:
- Формат Markdown
- 400-600 слов
- Структура: введение, основные разделы, заключение
- Профессиональный стиль написания
- Конкретные примеры и кейсы использования
- Актуальная информация на 2025 год
"""
    
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_name, 
            "messages": [{"role": "user", "content": prompt}], 
            "max_tokens": 2000,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"Groq API error {resp.status_code}")

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter API"""
    prompt = f"""Напиши развернутую статью на тему: '{topic}' на русском языке.

Требования:
- Формат Markdown
- 400-600 слов
- Структурированный контент с заголовками
- Практические примеры
- Профессиональный тон
"""
    
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-content-generator.com",
            "X-Title": "AI Content Generator"
        },
        json={
            "model": model_name, 
            "messages": [{"role": "user", "content": prompt}], 
            "max_tokens": 2000,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"OpenRouter API error {resp.status_code}")

def generate_fallback_content(topic):
    """Fallback контент"""
    return f"""# {topic}

## Введение
Тема "{topic}" становится increasingly important в 2025 году. Искусственный интеллект продолжает трансформировать различные отрасли, предлагая инновационные решения для сложных задач.

## Основные тенденции
- Автоматизация процессов разработки и тестирования
- Интеграция AI в существующие workflow и системы  
- Улучшение качества и скорости разработки программного обеспечения
- Персонализация пользовательского опыта с помощью машинного обучения

## Практическое применение
Компании по всему миру активно внедряют AI решения для оптимизации своих бизнес-процессов. От автоматизации рутинных задач до сложного анализа данных - искусственный интеллект находит применение в самых разных областях.

## Заключение
Будущее выглядит promising с развитием AI технологий. По мере того как алгоритмы становятся более sophisticated, мы можем ожидать появления еще более инновационных решений.

*Статья сгенерирована автоматически*
"""

# ======== Генерация изображений ========
def generate_article_image(topic):
    """Генерация изображения через Telegram бота"""
    try:
        prompt = f"{topic}, digital art, futuristic, professional, 4k, high quality"
        
        logger.info(f"🎨 Запрос генерации изображения: {prompt}")
        
        # Отправляем запрос боту на генерацию
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"/generate {prompt}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Запрос на генерацию отправлен боту")
            # Даем время на генерацию
            time.sleep(35)
            return f"/images/posts/{generate_slug(topic)}.jpg"
        else:
            logger.error(f"❌ Ошибка отправки запроса: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка генерации изображения: {e}")
    
    return "/images/default.jpg"

def generate_slug(text):
    """Генерация SEO-friendly slug"""
    text = text.lower().replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return re.sub(r'-+', '-', text)[:50]

def clean_old_articles(keep_last=5):
    """Очистка старых статей"""
    content_dir = "content/posts"
    if os.path.exists(content_dir):
        posts = sorted([f for f in os.listdir(content_dir) if f.endswith('.md')], reverse=True)
        for post in posts[keep_last:]:
            os.remove(os.path.join(content_dir, post))
            logger.info(f"🗑️ Удален старый пост: {post}")

def main():
    parser = argparse.ArgumentParser(description='Генератор AI контента')
    parser.add_argument('--count', type=int, default=1, help='Количество статей')
    parser.add_argument('--keep', type=int, default=5, help='Сколько статей оставлять')
    args = parser.parse_args()
    
    # Очистка старых статей
    clean_old_articles(args.keep)
    
    for i in range(args.count):
        topic = generate_ai_trend_topic()
        logger.info(f"📝 Генерация статьи {i+1}/{args.count}: {topic}")
        
        # Генерация контента
        content = generate_article_content(topic)
        image_path = generate_article_image(topic)
        
        # Сохранение статьи
        slug = generate_slug(topic)
        filename = f"content/posts/{slug}.md"
        
        os.makedirs("content/posts", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"""---
title: "{topic.replace('"', "'")}"
date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}
image: "{image_path}"
draft: false
tags: ["ai", "технологии", "2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о тенденциях AI в 2025 году"
---

{content}
""")
        
        logger.info(f"✅ Статья сохранена: {filename}")
        
        if i < args.count - 1:
            time.sleep(2)

if __name__ == "__main__":
    main()
