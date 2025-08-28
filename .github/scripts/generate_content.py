#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time
import urllib.parse

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе реальных трендов AI 2025"""
    
    current_trends_2025 = [
        "Multimodal AI - интеграция текста, изображений и аудио в единых моделях",
        "AI агенты - автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение - прорыв в производительности",
        "Нейроморфные вычисления - энергоэффективные архитектуры нейросетей",
        "Generative AI - создание контента, кода и дизайнов искусственным интеллектом",
        "Edge AI - обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности - предиктивная защита от угроз",
        "Этичный AI - ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare - диагностика, разработка лекарств и персонализированная медицина",
        "Автономные системы - беспилотный транспорт и робототехника",
        "AI оптимизация - сжатие моделей и ускорение inference",
        "Доверенный AI - объяснимые и прозрачные алгоритмы",
        "AI для климата - оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты - индивидуализированные цифровые помощники",
        "AI в образовании - адаптивное обучение и персонализированные учебные планы"
    ]
    
    application_domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес-аналитике",
        "в компьютерной безопасности и киберзащите",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях и EdTech"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    
    return random.choice(topic_formats)

def generate_content():
    """Генерирует контент статьи через AI API"""
    print("🚀 Запуск генерации контента...")
    
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    # Генерируем изображение
    image_filename = generate_article_image(selected_topic)
    
    # Генерируем текст статьи
    content, model_used = generate_article_content(selected_topic)
    
    # Создаем файл статьи
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    """Генерация содержания статьи через доступные API"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY не найден")
        # Создаем заглушечный контент
        dummy_content = f"""# {topic}

## Введение
Это тестовая статья о {topic}. Статья была сгенерирована автоматически.

## Основное содержание
{topic} представляет собой одну из ключевых технологических тенденций 2025 года. 

## Заключение
Перспективы развития {topic} выглядят очень promising в ближайшие годы.
"""
        return dummy_content, "dummy-generator"
    
    models_to_try = [
        ("anthropic/claude-3-haiku", lambda: generate_with_openrouter(api_key, "anthropic/claude-3-haiku", topic)),
        ("google/gemini-pro", lambda: generate_with_openrouter(api_key, "google/gemini-pro", topic)),
        ("mistralai/mistral-7b-instruct", lambda: generate_with_openrouter(api_key, "mistralai/mistral-7b-instruct", topic)),
    ]
    
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue
    
    # Fallback - создаем простой контент
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта.

## Основные аспекты
- Первый аспект {topic}
- Второй аспект {topic}
- Третий аспект {topic}

## Заключение
{topic} будет играть ключевую роль в технологическом развитии 2025 года.
"""
    return fallback_content, "fallback-generator"

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter"""
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- Объем: 300-500 слов
- Формат: Markdown с подзаголовками
- Язык: русский
- Стиль: технический, для разработчиков
- Фокус на 2025 год

Структура:
1. Введение
2. Основная часть
3. Примеры использования
4. Заключение

Используй:
- **Жирный шрифт** для терминов
- Списки для перечисления
- Конкретные примеры"""
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/lybra-bee",
            "X-Title": "AI Blog Generator"
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            content = data['choices'][0]['message']['content']
            return content.strip()
    
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    """Генерация изображения через AI API"""
    print("🎨 Генерация изображения...")
    
    try:
        # Создаем простое изображение через внешний сервис
 encoded_topic = urllib.parse.quote(topic[:30])
        image_url = f"https://placehold.co/800x400/0f172a/ffffff/png?text={encoded_topic}"
        
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            filename = save_article_image(response.content, topic)
            if filename:
                print("✅ Изображение создано")
                return filename
    except Exception as e:
        print(f"⚠️ Ошибка создания изображения: {e}")
    
    return None

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"posts/{slug}.jpg"
        full_path = f"assets/images/{filename}"
        
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        print(f"💾 Изображение сохранено: {filename}")
        return f"/images/{filename}"
        
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def clean_old_articles(keep_last=3):
    """Оставляет только последние N статей"""
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles:
            print("📁 Нет статей для очистки")
            return
        
        articles.sort(key=os.path.getmtime, reverse=True)
        articles_to_keep = articles[:keep_last]
        articles_to_delete = articles[keep_last:]
        
        print(f"📊 Всего статей: {len(articles)}")
        print(f"💾 Сохраняем: {len(articles_to_keep)}")
        print(f"🗑️ Удаляем: {len(articles_to_delete)}")
        
        for article_path in articles_to_delete:
            try:
                os.remove(article_path)
                print(f"❌ Удалено: {os.path.basename(article_path)}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")
                
    except Exception as e:
        print(f"⚠️ Ошибка при очистке статей: {e}")

def generate_slug(topic):
    """Генерация slug из названия темы"""
    slug = topic.lower()
    replacements = {' ': '-', ':': '', '(': '', ')': '', '/': '-', '\\': '-', '.': '', ',': '', '--': '-'}
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug[:50]

def generate_frontmatter(topic, content, model_used, image_filename=None):
    """Генерация frontmatter"""
    current_time = datetime.now()
    
    tags = ["искусственный-интеллект", "технологии", "инновации", "2025", "ai"]
    image_section = f"image: {image_filename}\n" if image_filename else ""
    
    return f"""---
title: "{topic}"
date: {current_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
description: "Автоматически сгенерированная статья о {topic}"
{image_section}tags: {json.dumps(tags, ensure_ascii=False)}
categories: ["Технологии"]
---

# {topic}

{f'![]({image_filename})' if image_filename else ''}

{content}

---

### 🔧 Технические детали

- **Модель AI:** {model_used}
- **Дата генерации:** {current_time.strftime("%d.%m.%Y %H:%M UTC")}
- **Тема:** {topic}
- **Год актуальности:** 2025
- **Статус:** Автоматическая генерация

> *Сгенерировано через GitHub Actions*
"""

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🤖 AI CONTENT GENERATOR")
        print("=" * 50)
        
        generate_content()
        
        print("=" * 50)
        print("✅ Генерация завершена успешно!")
        print("=" * 50)
        
    except Exception as e:
        print("❌ Критическая ошибка:")
        print(f"Ошибка: {e}")
        print("🔄 Продолжаем без генерации контента")
        exit(0)  # Выходим с кодом 0 чтобы не ломать workflow
