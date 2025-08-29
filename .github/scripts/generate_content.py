def generate_article_image(topic):
    """Генерация изображения через все доступные источники"""
    print("🎨 Генерация изображения...")
    
    # Попробуем Stability AI, если есть ключ
    stability_key = os.getenv('STABILITYAI_KEY')
    if stability_key:
        print("🔑 Используем Stability AI")
        image_filename = generate_image_stabilityai(topic, stability_key)
        if image_filename:
            return image_filename
    
    # Попробуем DeepAI
    deepai_key = "98c841c4"
    print("🔑 Используем DeepAI")
    image_filename = generate_image_deepai(topic, deepai_key)
    if image_filename:
        return image_filename
    
    # Бесплатные генераторы без ключа
    generators = [
        generate_image_craiyon,
        generate_image_lexica,
        generate_image_picsum
    ]
    
    for gen_func in generators:
        try:
            image_filename = gen_func(topic)
            if image_filename:
                return image_filename
        except Exception as e:
            print(f"⚠️ {gen_func.__name__} ошибка: {e}")
    
    print("⚠️ Генерация изображения не удалась, продолжаем без изображения")
    return None


def generate_image_stabilityai(topic, api_key):
    """Генерация изображения через Stability AI"""
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "text_prompts": [{"text": generate_image_prompt(topic), "weight": 1.0}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
            "style_preset": "digital-art"
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and data['artifacts']:
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                return save_article_image(image_data, topic)
    except Exception as e:
        print(f"❌ Ошибка Stability AI: {e}")
    return None


def generate_image_deepai(topic, api_key):
    """Генерация изображения через DeepAI"""
    try:
        print("🔄 Отправка запроса к DeepAI...")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={"text": generate_image_prompt(topic)},
            headers={"Api-Key": api_key},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            image_url = data.get('output_url')
            if image_url:
                # Загружаем изображение
                image_data = requests.get(image_url).content
                return save_article_image(image_data, topic)
        else:
            print(f"❌ DeepAI error: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка DeepAI: {e}")
    return None


def generate_image_craiyon(topic):
    """Бесплатный генератор Craiyon (без ключа)"""
    print("🔄 Попробуем Craiyon...")
    url = f"https://api.craiyon.com/v1/generate?prompt={urllib.parse.quote(generate_image_prompt(topic))}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if 'images' in data and data['images']:
            image_data = base64.b64decode(data['images'][0])
            return save_article_image(image_data, topic)
    return None


def generate_image_lexica(topic):
    """Бесплатный генератор Lexica (без ключа)"""
    print("🔄 Попробуем Lexica...")
    search_query = urllib.parse.quote(topic)
    url = f"https://lexica.art/api/v1/search?q={search_query}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if data.get("images"):
            image_url = data['images'][0]['src']
            image_data = requests.get(image_url).content
            return save_article_image(image_data, topic)
    return None


def generate_image_picsum(topic):
    """Случайное изображение с Picsum (заглушка, без ключа)"""
    print("🔄 Попробуем Picsum (заглушка)...")
    url = f"https://picsum.photos/1024/1024"
    image_data = requests.get(url).content
    return save_article_image(image_data, topic)
