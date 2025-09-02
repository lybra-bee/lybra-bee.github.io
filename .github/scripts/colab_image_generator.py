#!/usr/bin/env python3
"""
Скрипт для Google Colab - Генератор изображений через Telegram-бота
Запустите этот скрипт в Colab с GPU
"""

import os
import telebot
from diffusers import StableDiffusionPipeline
import torch
import io
import time
from PIL import Image
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGeneratorBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.setup_handlers()
        self.setup_model()
        
    def setup_model(self):
        """Загрузка модели Stable Diffusion"""
        logger.info("🔄 Загрузка модели Stable Diffusion...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16,
            safety_checker=None
        ).to(self.device)
        logger.info("✅ Модель загружена")
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message, 
                "🤖 Привет! Я AI-художник. Пришли мне описание картинки, и я сгенерирую её.\n\n"
                "Примеры:\n"
                "• 'футуристический город с небоскребами'\n"
                "• 'робот в стиле киберпанк'\n"
                "• 'пейзаж космической станции'"
            )
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            self.process_request(message)
    
    def process_request(self, message):
        """Обработка запроса на генерацию"""
        prompt = message.text
        chat_id = message.chat.id
        
        try:
            # Отправляем статус
            self.bot.send_message(chat_id, f"🎨 Генерирую: '{prompt}'...\n⏳ Это займет 20-30 секунд")
            
            # Генерация изображения
            image = self.pipe(
                prompt=prompt,
                num_inference_steps=30,
                guidance_scale=7.5
            ).images[0]
            
            # Конвертируем в bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Отправляем изображение
            self.bot.send_photo(chat_id, img_buffer, 
                               caption=f"✅ Сгенерировано: '{prompt}'")
            
            logger.info(f"✅ Изображение отправлено для: {prompt}")
            
        except Exception as e:
            error_msg = f"❌ Ошибка генерации: {str(e)}"
            self.bot.send_message(chat_id, error_msg)
            logger.error(error_msg)
    
    def run(self):
        """Запуск бота"""
        logger.info("🤖 Бот запущен...")
        self.bot.polling()

def main():
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
    
    # Запускаем бота
    bot = ImageGeneratorBot(token)
    bot.run()

if __name__ == "__main__":
    main()
