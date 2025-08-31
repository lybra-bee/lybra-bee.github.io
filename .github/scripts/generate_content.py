#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======== Генерация темы ========
def generate_ai_trend_topic():
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
        "Автономные системы беспилотный транспорт и робототехника",
        "AI оптимизация сжатие моделей и ускорение inference",
        "Доверенный AI объяснимые и прозрачные алгоритмы",
        "AI для климата оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты индивидуализированные цифровые помощники",
        "AI в образовании адаптивное обучение и персонализированные учебные планы"
    ]
    application_domains = [
        "в веб разработке и cloud native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес аналитике",
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
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025 {trend} для {domain}",
        f"{trend} будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    return random.choice(topic_formats)

# ======== Очистка старых статей ========
def clean_old_articles(keep_last=3):
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    content_dir = "content"
    if os.path.exists(content_dir):
        shutil.rmtree(content_dir)
    os.makedirs("content/posts", exist_ok=True)
    with open("content/_index.md", "w", encoding="utf-8") as f:
        f.write("---\ntitle: \"Главная\"\n---")
    with open("content/posts/_index.md", "w", encoding="utf-8") as f:
        f.write("---\ntitle: \"Статьи\"\n---")
    logger.info("✅ Создана чистая структура content")

# ======== Генерация статьи ========
def generate_content():
    logger.info("🚀 Запуск генерации контента...")
    clean_old_articles()
    
    topic = generate_ai_trend_topic()
    logger.info(f"📝 Тема статьи: {topic}")
    
    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)
    
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    logger.info(f"✅ Статья создана: {filename}")
    return filename

# ======== Генерация текста через OpenRouter/Groq ========
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview", "llama-3.1-70b-versatile"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku", "anthropic/claude-3-sonnet", "google/gemini-pro-1.5"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    for model_name, generate_func in models_to_try:
        try:
            logger.info(f"🔄 Пробуем генерацию текста: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                logger.info(f"✅ Успешно через {model_name}")
                return result, model_name
            else:
                logger.warning(f"⚠️ Пустой ответ от {model_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка {model_name}: {e}")
            continue

    fallback = f"# {topic}\n\nСтатья по теме {topic} создана автоматически."
    return fallback, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском, Markdown, 400-600 слов"
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500, "temperature":0.7}
    )
    logger.debug(f"Groq API статус: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"Groq API error {resp.status_code}: {resp.text}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском, Markdown, 400-600 слов"
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-site.com",
            "X-Title": "AI Content Generator"
        },
        json={
            "model": model_name, 
            "messages":[{"role":"user","content":prompt}], 
            "max_tokens":1500,
            "temperature":0.7
        }
    )
    logger.debug(f"OpenRouter API статус: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"OpenRouter API error {resp.status_code}: {resp.text}")

# ======== Eden AI генерация изображения ========
EDENAI_KEY = os.getenv('EDENAI_API_KEY')

# Расширенный список провайдеров
FREE_PROVIDERS = [
    "openjourney", 
    "stable_diffusion", 
    "dalle-mini",
    "deepai",
    "nightcafe",
    "huggingface"
]

PAID_PROVIDERS = [
    "openai",
    "stability",
    "leonardo",
    "midjourney"
]

def generate_article_image(topic):
    logger.info(f"🎨 Генерация изображения по промпту: {topic}")
    prompt = topic[:200]  # укоротим слишком длинные промпты
    
    if not EDENAI_KEY:
        logger.error("❌ EDENAI_API_KEY не установлен в переменных окружения")
        return generate_placeholder_image(topic)
    
    logger.info(f"🔑 Токен Eden AI: {EDENAI_KEY[:8]}...{EDENAI_KEY[-4:]}")
    
    # Сначала пробуем бесплатные провайдеры
    all_providers = FREE_PROVIDERS + PAID_PROVIDERS
    
    for provider in all_providers:
        try:
            logger.info(f"🔄 Пробуем провайдер: {provider}")
            
            # Настройки для разных провайдеров
            resolution = "512x512"  # Уменьшаем для тестирования
            if provider in ["openai", "leonardo", "midjourney"]:
                resolution = "1024x1024"
            
            payload = {
                "providers": [provider], 
                "text": prompt, 
                "resolution": resolution,
                "num_images": 1
            }
            
            # Специфичные настройки для некоторых провайдеров
            if provider == "leonardo":
                payload["settings"] = {provider: {"model": "leonardo-creative"}}
            elif provider == "stability":
                payload["settings"] = {provider: {"style_preset": "digital-art"}}
            
            start_time = time.time()
            
            resp = requests.post(
                "https://api.edenai.run/v2/image/generation",
                headers={
                    "Authorization": f"Bearer {EDENAI_KEY}", 
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            response_time = time.time() - start_time
            logger.info(f"⏱️ Время ответа {provider}: {response_time:.2f} сек")
            logger.info(f"📊 Статус код: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                logger.debug(f"📋 Полный ответ от {provider}: {json.dumps(data, ensure_ascii=False)[:500]}...")
                
                if "result" in data and data["result"]:
                    provider_result = data["result"][0]
                    
                    if "status" in provider_result and provider_result["status"] == "fail":
                        error_msg = provider_result.get("error", {}).get("message", "Unknown error")
                        logger.error(f"❌ {provider} failed: {error_msg}")
                        continue
                    
                    image_url = provider_result.get("url")
                    if image_url:
                        logger.info(f"✅ Получен URL изображения от {provider}")
                        filename = save_image_from_url(image_url, topic)
                        logger.info(f"✅ Изображение сохранено: {filename}")
                        return filename
                    else:
                        logger.warning(f"⚠️ Нет URL в ответе от {provider}")
                        if "error" in provider_result:
                            logger.error(f"❌ Ошибка {provider}: {provider_result['error']}")
                else:
                    logger.warning(f"⚠️ Нет результата от {provider}")
                    if "error" in data:
                        logger.error(f"❌ Общая ошибка: {data['error']}")
            
            elif resp.status_code == 402:
                logger.error(f"❌ {provider}: Недостаточно средств на счете")
            elif resp.status_code == 401:
                logger.error(f"❌ {provider}: Неверный API ключ")
            elif resp.status_code == 403:
                logger.error(f"❌ {provider}: Доступ запрещен")
            elif resp.status_code == 429:
                logger.error(f"❌ {provider}: Слишком много запросов")
            else:
                logger.error(f"❌ {provider}: Неожиданный статус код {resp.status_code}")
                logger.debug(f"📋 Ответ: {resp.text[:500]}...")
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ {provider}: Таймаут запроса")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ {provider}: Ошибка соединения")
        except Exception as e:
            logger.error(f"❌ Исключение с {provider}: {str(e)}")
            import traceback
            logger.debug(f"📋 Трейсбэк: {traceback.format_exc()}")
        
        # Пауза между запросами
        time.sleep(1)
    
    logger.warning("✅ Все провайдеры не сработали, используем placeholder")
    return generate_placeholder_image(topic)

def save_image_from_url(url, topic):
    try:
        logger.info(f"📥 Загрузка изображения из: {url[:100]}...")
        resp = requests.get(url, timeout=20)
        
        if resp.status_code == 200:
            os.makedirs("assets/images/posts", exist_ok=True)
            filename = f"assets/images/posts/{generate_slug(topic)}.png"
            
            with open(filename, "wb") as f:
                f.write(resp.content)
            
            logger.info(f"✅ Изображение сохранено: {filename}")
            return filename
        else:
            logger.error(f"❌ Ошибка загрузки изображения: статус {resp.status_code}")
            return generate_placeholder_image(topic)
            
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении изображения: {e}")
        return generate_placeholder_image(topic)

def generate_placeholder_image(topic):
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        width, height = 800, 400
        
        # Создаем градиентный фон
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        for i in range(height):
            r = int(15 + (i/height)*30)
            g = int(23 + (i/height)*42)
            b = int(42 + (i/height)*74)
            draw.line([(0,i),(width,i)], fill=(r,g,b))
        
        # Добавляем текст
        wrapped_text = textwrap.fill(topic, width=30)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0,0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        # Тень текста
        draw.text((x+2, y+2), wrapped_text, font=font, fill="#000000")
        # Основной текст
        draw.text((x, y), wrapped_text, font=font, fill="#6366f1")
        
        img.save(filename)
        logger.info(f"✅ Placeholder изображение создано: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания placeholder: {e}")
        return "assets/images/default.png"

# ======== Вспомогательные функции ========
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', "'")
    frontmatter = f"""---
title: "{escaped_title}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
---

{content}
"""
    return frontmatter

# ======== Запуск ========
if __name__ == "__main__":
    # Установите уровень логирования DEBUG для подробной информации
    # logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Запуск генератора контента...")
    print("📝 Проверка переменных окружения:")
    print(f"   EDENAI_API_KEY: {'✅ установлен' if os.getenv('EDENAI_API_KEY') else '❌ отсутствует'}")
    print(f"   OPENROUTER_API_KEY: {'✅ установлен' if os.getenv('OPENROUTER_API_KEY') else '❌ отсутствует'}")
    print(f"   GROQ_API_KEY: {'✅ установлен' if os.getenv('GROQ_API_KEY') else '❌ отсутствует'}")
    
    try:
        filename = generate_content()
        print(f"🎉 Генерация завершена! Файл: {filename}")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
