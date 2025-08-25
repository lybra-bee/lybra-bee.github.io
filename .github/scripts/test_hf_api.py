import requests
import os

def test_hugging_face():
    HF_API_KEY = os.getenv('HF_API_KEY')
    if not HF_API_KEY:
        print("❌ HF_API_KEY не найден")
        return False
    
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Тестовый промт
    payload = {
        "inputs": "Напиши одно предложение о программировании.",
        "parameters": {
            "max_new_tokens": 50,
            "temperature": 0.7
        }
    }
    
    try:
        print("🔌 Тестируем подключение к Hugging Face API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API подключено успешно!")
            print("Ответ:", result[0]['generated_text'])
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print("Ответ:", response.text)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    test_hugging_face()
