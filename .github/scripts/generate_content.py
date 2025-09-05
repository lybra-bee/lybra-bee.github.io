#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time

# ===== Получение токена GigaChat =====
def get_gigachat_token():
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
            return response.json().get("access_token")
        return None
    except Exception as e:
        print(f"❌ Исключение при получении токена GigaChat: {e}")
        return None

# ===== Генерация темы статьи =====
def generate_ai_trend_topic():
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
    domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных",
        "в компьютерной безопасности",
        "в медицине и биотехнологиях",
        "в финансовых технологиях",
        "в автономных транспортных системах",
        "в smart city",
        "в образовании"
    ]
    return f"{random.choice(current_trends_2025)} {random.choice(domains)} в 2025 году"

# ===== Основная генерация =====
def generate_content():
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)

    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")

    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)

    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"

    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)

    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")
    return filename

# ===== Генерация статьи =====
def generate_article_content(topic):
    api_key = os.getenv('OPENROUTER_API_KEY')
    gigachat_token = get_gigachat_token()
    models_to_try = []

    if api_key:
        for model in ["anthropic/claude-3-haiku", "google/gemini-pro"]:
            models_to_try.append((model, lambda m=model: generate_with_openrouter(api_key, m, topic)))

    if gigachat_token:
        models_to_try.append(("GigaChat-2-Max", lambda: generate_with_gigachat(gigachat_token, topic, "GigaChat-2-Max")))

    for model_name, func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = func()
            if result:
                return result, model_name
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {e}")
    raise Exception("❌ Все API недоступны")

def generate_with_gigachat(token, topic, model):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    prompt = f"Напиши техническую статью на тему: '{topic}' на русском языке, 500-700 слов, Markdown."
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2000}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code == 200:
        return r.json()['choices'][0]['message']['content']
    raise Exception(f"HTTP {r.status_code}: {r.text}")

def generate_with_openrouter(api_key, model, topic):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": f"Напиши статью на тему '{topic}' на русском языке, 500-700 слов, Markdown."}], "max_tokens": 1500}
    )
    if r.status_code == 200 and r.json().get("choices"):
        return r.json()["choices"][0]["message"]["content"].strip()
    raise Exception(f"HTTP {r.status_code}: {r.text}")

# ===== Генерация изображения =====
def generate_article_image(topic):
    prompt = f"Futuristic AI illustration for article: {topic}, digital art, neon, cyberpunk."
    try:
        headers = {"api-key": "quickstart-QUdJIGlzIGNvbWluZy4uLi4uK"}  # тестовый ключ
        data = {"text": prompt}
        r = requests.post("https://api.deepai.org/api/text2img", headers=headers, data=data, timeout=30)
        if r.status_code == 200 and "output_url" in r.json():
            img = requests.get(r.json()["output_url"], timeout=30)
            if img.status_code == 200:
                return save_article_image(img.content, topic)
    except Exception as e:
        print(f"❌ Ошибка изображения: {e}")
    return None

def save_article_image(image_data, topic):
    os.makedirs("static/images/posts", exist_ok=True)
    slug = generate_slug(topic)
    filename = f"images/posts/{slug}.jpg"
    with open(f"static/{filename}", "wb") as f:
        f.write(image_data)
    print(f"💾 Изображение сохранено: {filename}")
    return filename

# ===== Служебные =====
def clean_old_articles(keep=3):
    files = sorted(glob.glob("content/posts/*.md"), key=os.path.getmtime)
    for old in files[:-keep]:
        os.remove(old)

def generate_slug(topic):
    slug = topic.lower()
    for old, new in {' ': '-', ':': '', ',': '', '.': '', '/': '-', '\\': '-', '(': '', ')': ''}.items():
        slug = slug.replace(old, new)
    return ''.join(c for c in slug if c.isalnum() or c == '-').strip('-')[:50]

def generate_frontmatter(topic, content, model_used, image_filename):
    now = datetime.now().isoformat()
    tags = ["ai", "технологии", "2025"]
    return (
        "---\n"
        f"title: \"{topic}\"\n"
        f"date: {now}\n"
        f"tags: {tags}\n"
        f"author: \"AI Generator\"\n"
        f"model_used: \"{model_used}\"\n"
        f"image: \"{image_filename or ''}\"\n"
        "---\n\n"
        f"{content}"
    )

if __name__ == "__main__":
    generate_content()
