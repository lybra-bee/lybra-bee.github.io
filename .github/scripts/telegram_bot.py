#!/usr/bin/env python3
"""
Telegram бот для генерации изображений через Stable Diffusion
Для использования на сервере с GPU
"""

import os
import logging
import telebot
from telebot.types import InputFile
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import io
import time
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ImageGeneratorBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.setup_handlers()
        self.device = self.setup_device()
        self.pipe = self.load_model()
        
    def setup_device(self):
        """Определение устройства для вычислений"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"✅ GPU доступен: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.warning("⚠️ GPU не доступен, используем CPU (медленно)")
        return device
    
    def load_model(self):
        """Загрузка модели Stable Diffusion"""
        logger.info("🔄 Загрузка модели Stable Diffusion...")
        
        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            pipe = pipe.to(self.device)
            
            # Оптимизация для GPU
            if self.device == "cuda":
                pipe.enable_attention_slicing()
            
            logger.info("✅ Модель загружена и оптимизирована")
            return pipe
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    def setup_handlers(self):
        """Настройка обработчиков команд Telegram"""
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = """
🤖 *AI Image Generator Bot*

Я могу сгенерировать изображение по вашему описанию!

*Команды:*
/generate [описание] - Сгенерировать изображение
/status - Статус системы
/help - Эта справка

*Примеры:*
• `/generate футуристический город с небоскребами`
• `/generate робот в стиле киберпанк`
• `/generate пейзаж космической станции`

*Советы:*
• Добавляйте детали: "4k, high quality, digital art"
• Указывайте стиль: "в стиле Ван Гога", "пиксель-арт"
"""
            self.bot.reply_to(message, welcome_text, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['status'])
        def send_status(message):
            status_text = f"""
*Статус системы:*
• Устройство: `{self.device.upper()}`
• Модель: `Stable Diffusion v1.5`
• Время работы: `{time.strftime('%H:%M:%S', time.gmtime(time.time() - self.start_time))}`
"""
            self.bot.reply_to(message, status_text, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['generate'])
        def handle_generate(message):
            try:
                if len(message.text.split()) > 1:
                    prompt = ' '.join(message.text.split()[1:])
                    self.process_generation(message, prompt)
                else:
                    self.bot.reply_to(message, "❌ Укажите описание изображения после команды /generate")
            except Exception as e:
                self.bot.reply_to(message, f"❌ Ошибка: {str(e)}")
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            if not message.text.startswith('/'):
                self.process_generation(message, message.text)
    
    def process_generation(self, message, prompt):
        """Обработка запроса на генерацию изображения"""
        chat_id = message.chat.id
        
        try:
            if len(prompt) > 500:
                self.bot.reply_to(message, "❌ Слишком длинное описание. Максимум 500 символов.")
                return
            
            status_msg = self.bot.send_message(
                chat_id, 
                f"🎨 *Генерация:* {prompt[:100]}...\n⏳ *Время:* 20-30 секунд",
                parse_mode='Markdown'
            )
            
            # Генерация изображения
            start_time = time.time()
            image = self.generate_image(prompt)
            generation_time = time.time() - start_time
            
            # Конвертируем в bytes для отправки
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)
            
            # Отправляем изображение
            self.bot.send_photo(
                chat_id, 
                InputFile(img_buffer, filename=f"generated_{int(time.time())}.png"),
                caption=f"✅ *Сгенерировано:* {prompt}\n⏱️ *Время:* {generation_time:.1f}с",
                parse_mode='Markdown'
            )
            
            # Удаляем статус сообщение
            try:
                self.bot.delete_message(chat_id, status_msg.message_id)
            except:
                pass
            
            logger.info(f"✅ Изображение отправлено для: {prompt}")
            
        except Exception as e:
            error_msg = f"❌ Ошибка генерации: {str(e)}"
            self.bot.send_message(chat_id, error_msg)
            logger.error(f"Ошибка генерации: {e}")
    
    def generate_image(self, prompt):
        """Генерация изображения через Stable Diffusion"""
        enhanced_prompt = f"{prompt}, high quality, 4k, professional, detailed, digital art"
        negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy, text, watermark"
        
        # Генерация
        with torch.autocast(self.device):
            result = self.pipe(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
                width=512,
                height=512,
                generator=torch.Generator(device=self.device).manual_seed(int(time.time()))
            )
        
        return result.images[0]
    
    def run(self):
        """Запуск бота"""
        self.start_time = time.time()
        logger.info("🤖 Запуск Telegram
