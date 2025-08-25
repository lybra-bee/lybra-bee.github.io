import requests
import os
import json
from datetime import datetime

def generate_with_huggingface(prompt):
    """Генерация текста через Hugging Face"""
    HF_API_KEY = os.getenv('HF_API_KEY')
    if not HF_API_KEY:
        return "Ошибка: HF_API_KEY не настроен"
    
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.8,
            "do_sample": True,
            "return_full_text": False
        }
    }
    
    try:
        print(f"🧠 Генерация текста для: {prompt[:50]}...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]['generated_text'].strip()
            else:
                return "Не удалось обработать ответ API"
        else:
            return f"Ошибка API: {response.status_code}"
            
    except Exception as e:
        return f"Ошибка генерации: {str(e)}"

def create_ai_blog_post():
    """Создание AI-статьи"""
    topics = [
        "Современные тенденции веб-дизайна в 2024 году",
        "Как начать изучать JavaScript: практические советы",
        "CSS Grid и Flexbox: лучшее применение",
        "Автоматизация разработки с помощью GitHub Actions",
        "Нейросети в веб-разработке: практическое применение",
        "Оптимизация производительности веб-сайтов",
        "PWA против нативных приложений: что выбрать",
        "Веб-безопасность: лучшие практики для разработчиков"
    ]
    
    # Выбираем случайную тему
    import random
    topic = random.choice(topics)
    
    # Создаем промт для нейросети
    prompt = f"""Напиши подробную статью на тему "{topic}" для технического блога.

Требования:
- Используй профессиональный но доступный язык
- Структурируй статью с подзаголовками
- Приведи практические примеры кода если уместно
- Сделай заключение с выводами
- Верни ответ в формате Markdown

Статья:"""
    
    print(f"📝 Тема статьи: {topic}")
    content = generate_with_huggingface(prompt)
    
    # Создаем файл
    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = topic.lower().replace(' ', '-').replace(':', '').replace(',', '')
    filename = f"content/posts/{date_str}-{slug[:50]}.md"
    
    front_matter = f"""---
title: "{topic}"
date: {datetime.now().isoformat()}
draft: false
description: "Статья сгенерирована с помощью Hugging Face AI"
tags: ["ai", "автоматизация", "технологии"]
---

{content}
"""
    
    # Создаем директорию если нет
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    
    print(f"✅ Статья создана: {filename}")
    return True

if __name__ == "__main__":
    create_ai_blog_post()
