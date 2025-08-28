def generate_article_image(topic):
    """Генерация изображения через AI API"""
    print("🎨 Генерация изображения через AI API...")
    
    image_prompt = f"Technology illustration 2025 for article about {topic}. Modern, futuristic, professional style. Abstract technology concept with AI, neural networks, data visualization. Blue and purple color scheme. No text."
    
    apis_to_try = [
        {"name": "DeepAI Text2Img", "function": try_deepai_api},
        {"name": "HuggingFace Free", "function": try_huggingface_free},
        {"name": "Stability AI", "function": try_stability_ai},
        {"name": "Replicate API", "function": try_replicate_api},
        {"name": "Dummy Image", "function": try_dummy_image},  # Бесплатный fallback
    ]
    
    for api in apis_to_try:
        try:
            print(f"🔄 Пробуем {api['name']}")
            result = api['function'](image_prompt, topic)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка в {api['name']}: {e}")
            continue
    
    print("❌ Все AI API для изображений недоступны, продолжаем без изображения")
    return None

def try_deepai_api(prompt, topic):
    """Пробуем DeepAI API с правильным форматом"""
    try:
        print("🔑 Используем DeepAI API")
        
        # Правильный формат headers для DeepAI
        headers = {
            "Api-Key": "6d27650a"  # Ваш токен
        }
        
        data = {
            "text": prompt,
            "grid_size": "1",
            "width": "800", 
            "height": "400"
        }
        
        print("📡 Отправляем запрос к DeepAI...")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            headers=headers,
            data=data,
            timeout=30
        )
        
        print(f"📊 DeepAI status: {response.status_code}")
        print(f"📊 DeepAI response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ DeepAI response: {data}")
            
            if 'output_url' in data and data['output_url']:
                print("📥 Загружаем изображение...")
                image_response = requests.get(data['output_url'], timeout=30)
                
                if image_response.status_code == 200:
                    filename = save_article_image(image_response.content, topic)
                    if filename:
                        print("✅ Изображение создано через DeepAI")
                        return filename
                else:
                    print(f"❌ Ошибка загрузки изображения: {image_response.status_code}")
            else:
                print("❌ Нет output_url в ответе DeepAI")
        else:
            print(f"❌ Ошибка DeepAI API: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение в DeepAI API: {e}")
    
    return None

def try_huggingface_free(prompt, topic):
    """Бесплатный Hugging Face через неофициальный API"""
    try:
        print("🔑 Используем бесплатный Hugging Face API")
        
        # Попробуем несколько публичных моделей
        models = [
            "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            "https://api-inference.huggingface.co/models/prompthero/openjourney"
        ]
        
        for model_url in models:
            try:
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "width": 800,
                        "height": 400,
                        "num_inference_steps": 20,
                        "guidance_scale": 7.5
                    }
                }
                
                response = requests.post(
                    model_url,
                    json=payload,
                    timeout=45,
                    headers={"User-Agent": "AI-Blog-Generator/1.0"}
                )
                
                if response.status_code == 200:
                    filename = save_article_image(response.content, topic)
                    if filename:
                        print(f"✅ Изображение создано через {model_url.split('/')[-1]}")
                        return filename
                elif response.status_code == 503:
                    print(f"⏳ Модель загружается, пробуем следующую...")
                    continue
                else:
                    print(f"⚠️ Ошибка {response.status_code} для {model_url}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка с моделью: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Исключение в Hugging Face API: {e}")
    
    return None

def try_dummy_image(prompt, topic):
    """Создает простое изображение через внешние сервисы"""
    try:
        print("🎨 Создаем изображение через внешний сервис")
        
        # Используем placeholder сервисы
        placeholder_services = [
            f"https://placehold.co/800x400/0f172a/ffffff/png?text={topic[:30]}",
            f"https://dummyimage.com/800x400/0f172a/ffffff&text={topic[:30]}",
        ]
        
        for service_url in placeholder_services:
            try:
                response = requests.get(service_url, timeout=30)
                if response.status_code == 200:
                    filename = save_article_image(response.content, topic)
                    if filename:
                        print("✅ Изображение-заглушка создано")
                        return filename
            except:
                continue
                
    except Exception as e:
        print(f"❌ Ошибка создания заглушки: {e}")
    
    return None

def try_stability_ai(prompt, topic):
    """Пробуем Stability AI только если есть ключ"""
    try:
        stability_key = os.getenv('STABILITYAI_KEY')
        if not stability_key:
            print("ℹ️ STABILITYAI_KEY не найден, пропускаем")
            return None
        
        print("🔑 Используем Stability AI")
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": 7,
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 20,
            "style_preset": "digital-art"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and data['artifacts']:
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                filename = save_article_image(image_data, topic)
                if filename:
                    print("✅ Изображение создано через Stability AI")
                    return filename
        else:
            print(f"❌ Stability AI error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка Stability AI: {e}")
    
    return None

def try_replicate_api(prompt, topic):
    """Пробуем Replicate API только если есть токен"""
    try:
        replicate_token = os.getenv('REPLICATE_API_TOKEN')
        if not replicate_token:
            print("ℹ️ REPLICATE_API_TOKEN не найден, пропускаем")
            return None
            
        print("🔑 Используем Replicate API")
        
        headers = {
            "Authorization": f"Token {replicate_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "version": "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
            "input": {
                "prompt": prompt,
                "width": 800,
                "height": 400
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 201:
            prediction_id = response.json()["id"]
            print(f"⏳ Ожидаем генерации изображения: {prediction_id}")
            
            # Ожидаем завершения генерации
            for _ in range(5):
                time.sleep(5)
                status_response = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] == "succeeded":
                        image_url = status_data["output"]
                        image_response = requests.get(image_url, timeout=30)
                        if image_response.status_code == 200:
                            filename = save_article_image(image_response.content, topic)
                            if filename:
                                print("✅ Изображение создано через Replicate")
                                return filename
                        break
                    elif status_data["status"] == "failed":
                        print("❌ Генерация через Replicate не удалась")
                        break
            else:
                print("⏰ Таймаут ожидания Replicate")
                
    except Exception as e:
        print(f"❌ Исключение в Replicate API: {e}")
    
    return None
