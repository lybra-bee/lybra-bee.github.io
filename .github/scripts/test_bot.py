import os
import requests

# Ваши данные
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def test_bot():
    # Отправка тестового сообщения
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🤖 Бот успешно настроен! Готов к генерации контента."
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Бот работает корректно!")
    else:
        print("❌ Ошибка настройки бота:", response.text)

if __name__ == "__main__":
    test_bot()
