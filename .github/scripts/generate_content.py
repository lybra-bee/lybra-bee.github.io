#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time

def get_gigachat_token():
    """Получает Access Token для GigaChat API"""
    client_id = os.getenv('GIGACHAT_CLIENT_ID')
    client_secret = os.getenv('GIGACHAT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ GIGACHAT_CLIENT_ID или GIGACHAT_CLIENT_SECRET не найдены")
        return None
    
    auth_string = f"{client_id}:{client_secret}"
    auth_key = base64.b64encode(auth_string.encode()).decode()
    
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": f"rq-{random.randint(100000, 999999)}-{int(time.time())}",
        "Authorization": f"Basic {auth_key}"
    }
    data = {"scope": "GIGACHAT_API_PERS"}
    
    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        print(f"❌ Не удалось получить токен GigaChat: HTTP {response.status_code} {getattr(response, 'text', '')}")
        return None
    except Exception as e:
        print(f"❌ Исключение при получении токена GigaChat: {e}")
        return None

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе трендов AI 2025"""
    current_trends_2025 = [
        "Multimodal AI - интеграция текста, изображений и аудио",
        "AI агенты - автономные системы",
        "Квантовые вычисления и машинное обучение",
        "Нейроморфные вычисления - энергоэффективные архитектуры",
        "Generative AI - создание контента, кода и дизайнов",
        "Edge AI - обработка данных на устройстве",
        "AI для кибербезопасности - предиктивная защита",
        "Этичный AI - ответственное использование",
        "AI в healthcare - диагностика и персонализированная медицина",
        "Автономные системы - беспилотный транспорт",
        "AI оптимизация - сжатие моделей и ускорение inference",
        "Доверенный AI - объяснимые алгоритмы",
        "AI для климата - оптимизация энергопотребления",
        "Персональные AI ассистенты - индивидуальные помощники",
        "AI в образовании - адаптивное обучение"
    ]
    
    application_domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес-аналитике",
        "в компьютерной безопасности",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    
    return random.choice(topic_formats)

def generate_content():
    """Генерирует контент статьи через AI API"""
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    image_filename = generate_article_image(selected_topic)  # вернёт строку вида "images/posts/slug.jpg" или None
    content, model_used = generate_article_content(selected_topic)
    
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, True, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    """Генерация содержания статьи через доступные API"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    gigachat_token = get_gigachat_token()
    
    models_to_try = []
    
    if api_key:
        openrouter_models = ["anthropic/claude-3-haiku", "google/gemini-pro"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(api_key, m, topic)))
    
    if gigachat_token:
        models_to_try.append(("GigaChat-2-Max", lambda: generate_with_gigachat(gigachat_token, topic, "GigaChat-2-Max")))
    
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {e}")
            continue
    
    raise Exception("❌ Все AI API недоступны")

def generate_with_gigachat(token, topic, model_name):
    """Генерация через GigaChat"""
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    prompt = f"Напиши техническую статью на тему: '{topic}' на русском языке, 500-700 слов, Markdown с заголовками ## и ###."
    
    payload = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2000}
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    raise Exception(f"HTTP {response.status_code}: {getattr(response, 'text', '')}")

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter"""
    prompt = f"Напиши техническую статью на тему: '{topic}' на русском языке, 500-700 слов, Markdown."
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500, "temperature": 0.7},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {getattr(response, 'text', '')}")

def generate_article_image(topic):
    """Генерация изображения через DeepAI (сохранение в static/images/posts, возврат пути images/posts/slug.jpg без ведущего слэша)"""
    print("🎨 Генерация изображения через DeepAI...")
    
    image_prompt = f"Technology illustration 2025 for article about {topic}. Futuristic style, AI, neural networks, abstract."
    
    filename = try_deepai_api(image_prompt, topic)
    if filename:
        return filename  # например "images/posts/slug.jpg"
    print("⚠️ DeepAI не дал изображение, статья будет без image (шаблон покажет плейсхолдер).")
    return None

def try_deepai_api(prompt, topic):
    """Используем тестовый ключ DeepAI"""
    try:
        headers = {"api-key": "quickstart-QUdJIGlzIGNvbWluZy4uLi4K"}
        data = {"text": prompt, "grid_size": "1", "width": "800", "height": "400"}
        response = requests.post("https://api.deepai.org/api/text2img", headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'output_url' in data and data['output_url']:
                img_response = requests.get(data['output_url'], timeout=30)
                if img_response.status_code == 200:
                    return save_article_image(img_response.content, topic)
                else:
                    print(f"❌ Ошибка загрузки изображения DeepAI: HTTP {img_response.status_code}")
        else:
            print(f"❌ DeepAI ответ: HTTP {response.status_code} {getattr(response, 'text', '')}")
    except Exception as e:
        print(f"❌ Ошибка DeepAI API: {e}")
    return None

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение и возвращает относительный путь 'images/posts/slug.jpg' (без ведущего слэша)"""
    try:
        os.makedirs("static/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        relative_path = f"images/posts/{slug}.jpg"   # <-- без ведущего слэша
        full_path = os.path.join("static", relative_path)
        with open(full_path, 'wb') as f:
            f.write(image_data)
        print(f"💾 Изображение сохранено: {relative_path}")
        return relative_path
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def clean_old_articles(keep_last=3):
    """Удаляет старые статьи, оставляя последние N"""
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime)
    for article_path in articles[:-keep_last]:
        try:
            os.remove(article_path)
            print(f"🧹 Удалена старая статья: {os.path.basename(article_path)}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить {article_path}: {e}")

def generate_slug(topic):
    slug = topic.lower()
    replacements = {' ': '-', ':': '', '(': '', ')': '', '/': '-', '\\': '-', '.': '', ',': '', '--': '-'}
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug[:50]

def generate_frontmatter(topic, content, model_used, api_success, image_filename=None):
    current_time = datetime.now()
    tags = ["искусственный-интеллект", "технологии", "инновации", "2025"]
    # Записываем относительный путь (без ведущего слэша), либо пустую строку
    image_line = f'image: "{image_filename}"' if image_filename else 'image: ""'
    frontmatter = (
        "---\n"
        f'title: "{topic}"\n'
        f"date: {current_time.isoformat()}\n"
        f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
        'author: "AI Content Generator"\n'
        f'model_used: "{model_used}"\n'
        f"{image_line}\n"
        "draft: false\n"
        "---\n\n"
        f"{content}"
    )
    return frontmatter

if __name__ == "__main__":
    generate_content()
