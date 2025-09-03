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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = "8006769060:AAEGAKhjUeuAXfnsQWtdLcKpAjkJrrGQ1Fk"
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')

# ======== Генерация темы ========
def generate_ai_trend_topic():
    """Генерация случайной темы про AI тренды"""
    current_trends_2025 = [
        "Multimodal AI интеграция текста изображений и аудио",
        "AI агенты автономные системы",
        "Квантовые вычисления и машинное обучение", 
        "Нейроморфные вычисления энергоэффективные архитектуры",
        "Generative AI создание контента",
        "Edge AI обработка данных на устройстве",
        "AI для кибербезопасности",
        "Этичный AI ответственное развитие",
        "AI в healthcare диагностика",
        "Автономные системы робототехника"
    ]
    
    application_domains = [
        "в веб разработке",
        "в мобильных приложениях", 
        "в облачных сервисах",
        "в анализе больших данных",
        "в компьютерной безопасности",
        "в медицинской диагностике",
        "в финансовых технологиях",
        "в автономных системах",
        "в smart city",
        "в образовательных технологиях"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    return f"{trend} {domain} в 2025 году"

# ======== Генерация текста статьи ========
def generate_article_content(topic):
    """Генерация текста статьи"""
    try:
        # Пробуем Groq API
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and groq_key not in ['', 'your_groq_api_key_here']:
            try:
                logger.info("🔄 Пробуем Groq API...")
                return generate_with_groq(groq_key, topic)
            except Exception as e:
                logger.error(f"❌ Ошибка Groq: {e}")
        
        # Пробуем OpenRouter API
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key and openrouter_key not in ['', 'your_openrouter_api_key_here']:
            try:
                logger.info("🔄 Пробуем OpenRouter API...")
                return generate_with_openrouter(openrouter_key, topic)
            except Exception as e:
                logger.error(f"❌ Ошибка OpenRouter: {e}")
                
    except Exception as e:
        logger.error(f"❌ Общая ошибка генерации: {e}")
    
    # Fallback
    logger.info("🔄 Используем fallback контент")
    return generate_fallback_content(topic)

def generate_with_groq(api_key, topic):
    """Генерация через Groq API"""
    prompt = f"""Напиши статью на тему: '{topic}' на русском.

Требования:
- Формат Markdown
- 300-500 слов
- Структура: введение, основные разделы, заключение
- Профессиональный стиль
- Конкретные примеры
- Актуальная информация на 2025 год
"""
    
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",  # Обновленная модель
            "messages": [{"role": "user", "content": prompt}], 
            "max_tokens": 1500,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"HTTP error {resp.status_code}: {resp.text}")

def generate_with_openrouter(api_key, topic):
    """Генерация через OpenRouter API"""
    prompt = f"""Напиши статью на тему: '{topic}' на русском.

Требования:
- Формат Markdown  
- 300-500 слов
- Структурированный контент с заголовками
- Практические примеры
- Профессиональный тон
"""
    
    # Пробуем несколько раз из-за возможных DNS проблем
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}", 
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://lybra-bee.github.io"
                },
                json={
                    "model": "anthropic/claude-3-sonnet", 
                    "messages": [{"role": "user", "content": prompt}], 
                    "max_tokens": 1500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                raise Exception(f"HTTP error {resp.status_code}: {resp.text}")
                
        except Exception as e:
            if attempt == 2:  # Последняя попытка
                raise e
            time.sleep(2)  # Ждем перед повторной попыткой
            logger.warning(f"🔄 Повторная попытка {attempt + 1}/3 для OpenRouter")

def generate_fallback_content(topic):
    """Fallback контент"""
    return f"""# {topic}

## Введение
{topic} - это одна из ключевых технологий 2025 года. Искусственный интеллект продолжает трансформировать различные отрасли.

## Основные тенденции
- Автоматизация процессов
- Улучшение качества данных  
- Персонализация пользовательского опыта
- Интеграция с существующими системами

## Практическое применение
Компании внедряют AI решения для оптимизации бизнес-процессов. Современные алгоритмы машинного обучения позволяют решать сложные задачи, которые ранее были недоступны для автоматизации.

## Технические аспекты
Реализация AI систем требует тщательного проектирования архитектуры, качественных данных для обучения и грамотной интеграции с существующей IT-инфраструктурой.

## Заключение
Будущее выглядит многообещающим с развитием AI технологий. Мы можем ожидать появления еще более инновационных решений в ближайшие годы.

*Статья сгенерирована автоматически*
"""

# ======== Генерация изображений ========
def generate_article_image(topic):
    """Генерация изображения через Telegram бота"""
    try:
        prompt = f"{topic}, digital art, futuristic, 4k, high quality"
        
        logger.info(f"🎨 Запрос генерации изображения: {prompt}")
        
        # Отправляем запрос боту
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"/generate {prompt}",
                "parse_mode": "Markdown"
            },
            timeout=15
        )
        
        logger.info(f"📤 Ответ Telegram: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Запрос отправлен боту")
            
            # Даем время на генерацию + ответ бота
            logger.info("⏳ Ожидаем генерацию изображения (40 секунд)...")
            time.sleep(40)
            
            logger.info("✅ Предполагаем, что изображение сгенерировано")
            return f"/images/posts/{generate_slug(topic)}.jpg"
        else:
            logger.error(f"❌ Ошибка отправки запроса: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка генерации изображения: {e}")
    
    # Fallback - возвращаем путь к default изображению
    return "/images/default.jpg"

def generate_slug(text):
    """Генерация slug"""
    text = text.lower().replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return re.sub(r'-+', '-', text)[:50]

def clean_old_articles(keep_last=3):
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
    parser.add_argument('--keep', type=int, default=3, help='Сколько статей оставлять')
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    args = parser.parse_args()
    
    # Включение debug режима
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🔧 Режим отладки включен")
    
    # Проверка переменных окружения
    logger.info("🔍 Проверка переменных окружения:")
    for var in ['OPENROUTER_API_KEY', 'GROQ_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']:
        value = os.getenv(var)
        status = "установлен" if value and value not in ['', f'your_{var.lower()}_here'] else "не установлен"
        logger.info(f"   {var}: {status}")
    
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
date: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
image: "{image_path}"
draft: false
tags: ["ai", "технологии", "2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о тенденциях AI"
---

{content}
""")
        
        logger.info(f"✅ Статья сохранена: {filename}")
        
        if i < args.count - 1:
            time.sleep(2)

if __name__ == "__main__":
    main()
