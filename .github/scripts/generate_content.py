import os
import json
import requests
import time
from slugify import slugify
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ====== Генерация статьи через Groq ======
def generate_article():
    GROQ_KEY = os.getenv("GROQ_API_KEY")
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }

    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."

    data = {
        "model": "groq-3.0-mini",
        "messages": [
            {"role": "system", "content": "Ты — эксперт в AI и высоких технологиях."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post("https://api.groq.com/v1/chat/completions", headers=headers, json=data)
        r.raise_for_status()
        response = r.json()
        text = response["choices"][0]["message"]["content"]
        model_used = response.get("model", "groq-3.0-mini")
        logging.info("✅ Статья получена через Groq")
        return text, model_used
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None

# ====== Генерация изображения через FusionBrain Kandinsky ======
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = "https://api-key.fusionbrain.ai/"
        self.AUTH_HEADERS = {
            "X-Key": f"Key {api_key}",
            "X-Secret": f"Secret {secret_key}",
        }

    def get_pipeline(self):
        r = requests.get(self.URL + "key/api/v1/pipelines", headers=self.AUTH_HEADERS)
        r.raise_for_status()
        return r.json()[0]["id"]

    def generate(self, prompt, pipeline_id, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        data = {
            "pipeline_id": (None, pipeline_id),
            "params": (None, json.dumps(params), "application/json")
        }
        r = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=data)
        r.raise_for_status()
        return r.json()["uuid"]

    def check_generation(self, request_id, attempts=10, delay=10):
        for _ in range(attempts):
            r = requests.get(self.URL + f"key/api/v1/pipeline/status/{request_id}", headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "DONE":
                return data["result"]["files"]
            time.sleep(delay)
        raise Exception("Генерация изображения не завершилась за отведённое время")

def generate_image(title, slug):
    FB_KEY = os.getenv("FUSIONBRAIN_KEY")
    FB_SECRET = os.getenv("FUSIONBRAIN_SECRET")
    fb = FusionBrainAPI(FB_KEY, FB_SECRET)
    pipeline_id = fb.get_pipeline()
    uuid = fb.generate(title, pipeline_id)
    files = fb.check_generation(uuid)
    if not files:
        raise Exception("Не удалось получить изображение")
    # сохраняем изображение локально
    img_data = requests.get(files[0]).content
    img_path = f"content/images/{slug}.png"
    with open(img_path, "wb") as f:
        f.write(img_data)
    return img_path

# ====== Пример сохранения статьи ======
def save_article(title, text, model):
    slug = slugify(title)
    filename = f"content/posts/{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{title}\"\ndate: {time.strftime('%Y-%m-%d')}\nmodel: {model}\nimage: /images/{slug}.png\n---\n\n{text}")
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug
