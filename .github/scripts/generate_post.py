import requests
import os
import json
from datetime import datetime

# Конфигурация
HF_API_KEY = os.getenv('HF_API_KEY')
REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')

def generate_with_huggingface(prompt):
    """Генерация текста через Hugging Face"""
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("API Response:", json.dumps(result, ensure_ascii=False, indent=2))
        
        # Обрабатываем разные форматы ответа
        if isinstance(result, list):
            return result[0].get('generated_text', 'Не удалось сгенерировать текст')
        elif isinstance(result, dict):
            return result.get('generated_text', 'Не удалось сгенерировать текст')
        else:
            return str(result)
            
    except Exception as e:
        print(f"Ошибка при генерации: {e}")
        return "Автоматически сгенерированная статья. Ошибка при создании контента."

def create_blog_post():
    """Создание нового поста"""
    topics = [
        "Основы веб-дизайна",
        "JavaScript для начинающих", 
        "CSS современные возможности",
        "Автоматизация разработки",
        "Нейросети в программировании"
    ]
    
    # Выбираем случайную тему
    topic = "Тестовая статья"
    
    # Генерируем контент
    prompt = f"Напиши короткую статью на тему '{topic}' для технического блога. 2-3 абзаца."
    content = generate_with_huggingface(prompt)
    
    # Создаем файл
    filename = f"content/posts/test-article.md"
    
    front_matter = f"""---
title: "{topic}"
date: {datetime.now().isoformat()}
draft: false
description: "Тестовая автоматически сгенерированная статья"
tags: ["тест", "автоматизация"]
---

## {topic}

{content}

*Статья сгенерирована автоматически с помощью Hugging Face API*
"""
    
    os.makedirs(os.path.join(REPO_PATH, 'content/posts'), exist_ok=True)
    
    with open(os.path.join(REPO_PATH, filename), 'w', encoding='utf-8') as f:
        f.write(front_matter)
    
    print(f"Создан тестовый пост: {filename}")
    return True

if __name__ == "__main__":
    success = create_blog_post()
    exit(0 if success else 1)
