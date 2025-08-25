#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime

def generate_content():
    # Конфигурация
    topics = [
        "Веб-фреймворки 2024: React, Vue, Svelte",
        "Serverless архитектура для веб-приложений", 
        "Искусственный интеллект в веб-разработке",
        "Прогрессивные веб-приложения (PWA)",
        "Кибербезопасность веб-приложений"
    ]
    
    selected_topic = random.choice(topics)
    print(f"📝 Тема: {selected_topic}")
    
    # Попытка генерации через OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    content = ""
    
    if api_key:
        try:
            print("🔄 Пытаемся подключиться к OpenRouter API...")
            
            # Актуальные бесплатные модели
            free_models = [
                "mistralai/mistral-7b-instruct",
                "google/gemini-pro",
                "huggingfaceh4/zephyr-7b-beta"
            ]
            
            selected_model = random.choice(free_models)
            print(f"🎯 Модель: {selected_model}")
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://github.com",
                    "X-Title": "AI Blog Generator"
                },
                json={
                    "model": selected_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Напиши короткий технический абзац (100-150 слов) на тему: {selected_topic}. Используй Markdown форматирование. Ответ на русском языке."
                        }
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7
                },
                timeout=15
            )
            
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    print("✅ Успешная генерация через API")
                else:
                    raise Exception("Нет choices в ответе API")
            else:
                error_msg = response.text[:200] if response.text else "No error message"
                raise Exception(f"API error {response.status_code}: {error_msg}")
                
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            # Fallback контент
            content = f"""## {selected_topic}

В 2024 году **{selected_topic.split(':')[0]}** продолжает активно развиваться. 

### Основные тенденции

- **Инновационные подходы** к разработке
- **Улучшенная производительность** систем
- **Интеграция с современными технологиями**
- **Повышенная безопасность** и надежность

Технологический ландшафт постоянно меняется, предлагая разработчикам новые возможности для создания эффективных и масштабируемых решений."""
    else:
        print("⚠️ API ключ не найден, используем локальную генерацию")
        content = f"""## {selected_topic}

Автоматически сгенерированная статья о современных тенденциях в области {selected_topic.lower()}.

**Ключевые аспекты:**
- Современные методики разработки
- Оптимизация производительности  
- Безопасность и надежность
- Интеграция с облачными технологиями"""
    
    # Создаем файл
    date = datetime.now().strftime("%Y-%m-%d")
    slug = selected_topic.lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '')[:30]
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = f"""---
title: "{selected_topic}"
date: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
tags: ["веб-разработка", "технологии"]
categories: ["Разработка"]
---

# {selected_topic}

{content}

---

### 🔧 Технические детали

- **Дата генерации:** {datetime.now().strftime("%d.%m.%Y %H:%M")}
- **Тема:** {selected_topic}
- **Статус:** {'✅ API генерация' if api_key and 'API' in content else '⚠️ Локальная генерация'}

> *Сгенерировано автоматически через GitHub Actions*
"""
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Файл создан: {filename}")
    
    # Покажем начало файла для проверки
    with open(filename, 'r', encoding='utf-8') as f:
        preview = f.read(500)
    print(f"📄 Предпросмотр:\n{preview}...")
    
    return filename

if __name__ == "__main__":
    generate_content()
