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
import argparse
import base64

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Популярные бесплатные модели Replicate
REPLICATE_MODELS = [
    {
        "name": "Stable Diffusion XL",
        "id": "stability-ai/sdxl",
        "prompt_template": "{topic}, digital art, futuristic, professional, 4k quality"
    },
    {
        "name": "FLUX.1 Schnell", 
        "id": "black-forest-labs/flux-1-schnell",
        "prompt_template": "{topic}, AI art, technology, innovation, high quality"
    },
    {
        "name": "Karlo",
        "id": "kakaobrain/karlo", 
        "prompt_template": "{topic}, creative, digital art, modern design"
    },
    {
        "name": "OpenJourney",
        "id": "prompthero/openjourney",
        "prompt_template": "{topic}, artistic, creative, vibrant colors"
    }
]

# ======== [ОСТАЛЬНОЙ КОД ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ ДО ФУНКЦИИ try_replicate_free_models] ========

def try_replicate_free_models(topic):
    """Используем бесплатные модели Replicate с автоматическим получением версий"""
    REPLICATE_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    if not REPLICATE_TOKEN:
        logger.warning("⚠️ Replicate токен не найден")
        return None
    
    # Перемешиваем модели для разнообразия
    random.shuffle(REPLICATE_MODELS)
    
    for model_info in REPLICATE_MODELS:
        try:
            logger.info(f"🔄 Пробуем модель: {model_info['name']}")
            
            # Получаем актуальную версию модели
            version = get_latest_model_version(REPLICATE_TOKEN, model_info["id"])
            if not version:
                logger.warning(f"⚠️ Не удалось получить версию для {model_info['name']}")
                continue
            
            prompt = model_info['prompt_template'].format(topic=topic)
            
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Bearer {REPLICATE_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": version,
                    "input": {
                        "prompt": prompt,
                        "width": 512,
                        "height": 512,
                        "num_outputs": 1,
                        "num_inference_steps": 20
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                prediction_id = response.json()['id']
                logger.info(f"✅ Предсказание создано: {prediction_id}")
                
                # Ждем завершения генерации
                for attempt in range(8):
                    time.sleep(3)
                    status_response = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Bearer {REPLICATE_TOKEN}"},
                        timeout=20
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', '')
                        
                        if status == 'succeeded':
                            image_url = status_data['output'][0]
                            logger.info(f"✅ Изображение готово: {image_url}")
                            img_data = requests.get(image_url, timeout=30).content
                            return save_image_bytes(img_data, topic)
                        elif status == 'failed':
                            error_msg = status_data.get('error', 'Unknown error')
                            logger.warning(f"⚠️ Генерация не удалась: {error_msg}")
                            break
                        else:
                            logger.info(f"⏳ Статус: {status} (попытка {attempt + 1})")
                    else:
                        logger.warning(f"⚠️ Ошибка статуса: {status_response.status_code}")
                        break
            else:
                logger.warning(f"⚠️ Ошибка API: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка модели {model_info['name']}: {e}")
            continue
    
    return None

def get_latest_model_version(replicate_token, model_id):
    """Получаем актуальную версию модели"""
    try:
        response = requests.get(
            f"https://api.replicate.com/v1/models/{model_id}/versions",
            headers={"Authorization": f"Bearer {replicate_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            versions = response.json().get('results', [])
            if versions:
                # Берем последнюю версию
                latest_version = versions[0]['id']
                logger.info(f"📦 Актуальная версия {model_id}: {latest_version}")
                return latest_version
            else:
                logger.warning(f"⚠️ Нет доступных версий для {model_id}")
        else:
            logger.warning(f"⚠️ Ошибка получения версий для {model_id}: {response.status_code}")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения версии для {model_id}: {e}")
        return None

# ======== [ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ] ========
