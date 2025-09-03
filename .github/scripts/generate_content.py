# .github/scripts/generate_content.py
import requests
import os
import time
import argparse
from PIL import Image
import io

def generate_with_huggingface(prompt):
    """
    Генерация изображения через Hugging Face API
    Бесплатно: 30k токенов в месяц (~100+ изображений)
    """
    try:
        HF_TOKEN = os.getenv('HF_API_TOKEN')
        if not HF_TOKEN:
            raise ValueError("HF_API_TOKEN not found")
        
        # 🔧 Улучшаем промпт
        enhanced_prompt = f"{prompt}, digital art, futuristic, professional, 4k, ultra detailed, high quality"
        
        print(f"🎨 Генерирую через Hugging Face: {enhanced_prompt}")
        
        API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        payload = {
            "inputs": enhanced_prompt,
            "parameters": {
                "width": 1024,
                "height": 512,
                "num_inference_steps": 25,
                "guidance_scale": 7.5
            }
        }
        
        # Отправляем запрос
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Сохраняем изображение
        filename = f"hf_{int(time.time())}.png"
        filepath = f"static/images/posts/{filename}"
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Изображение сохранено: {filepath}")
        return filepath
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            print("⏳ Модель загружается, жду 30 секунд...")
            time.sleep(30)
            return generate_with_huggingface(prompt)  # Retry
        else:
            print(f"❌ HTTP Error: {e}")
            return None
    except Exception as e:
        print(f"❌ Hugging Face error: {e}")
        return None

def generate_with_replicate(prompt):
    """Fallback: Replicate.com (~$0.01 за изображение)"""
    try:
        print("🔄 Пробую Replicate как fallback...")
        
        # Replicate API (нужен REPLICATE_API_TOKEN)
        API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
        if not API_TOKEN:
            return None
            
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": "ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
                "input": {
                    "prompt": f"{prompt}, digital art, professional",
                    "width": 1024,
                    "height": 512
                }
            }
        )
        
        # ... (код для обработки ответа Replicate)
        
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description='AI Content Generator')
    parser.add_argument('--count', type=int, default=1, help='Number of articles')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    print("🔄 Starting content generation...")
    print(f"📊 Articles to generate: {args.count}")
    
    # Пример генерации изображения
    test_prompt = "AI technology futuristic background"
    image_path = generate_with_huggingface(test_prompt)
    
    if image_path:
        print(f"✅ Success! Image: {image_path}")
    else:
        print("❌ Image generation failed")
    
    # Здесь ваша основная логика генерации статей
    print("✅ Content generation completed!")

if __name__ == "__main__":
    main()
