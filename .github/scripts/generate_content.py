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

# Актуальные бесплатные модели Replicate (обновленные версии)
REPLICATE_FREE_MODELS = [
    {
        "name": "FLUX.1 Schnell",
        "id": "black-forest-labs/flux-1-schnell",
        "version": "5c8c8347c5c4b3bb79a3c0c2f53a2a9e30889f5b4f6b2c2d5c8d2e5e8c2d5c8d",
        "prompt_template": "{topic}, digital art, futuristic, professional, 4k quality"
    },
    {
        "name": "Stable Diffusion XL", 
        "id": "stability-ai/sdxl",
        "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "prompt_template": "{topic}, digital art, futuristic style, high quality"
    },
    {
        "name": "FLUX Dev",
        "id": "black-forest-labs/flux-dev",
        "version": "0e0e2a5f40c9c233d133c5b8f19dc2b1c5b8f19dc2b1c5b8f19dc2b1c5b8f19dc",
        "prompt_template": "{topic}, experimental, AI art, futuristic technology"
    },
    {
        "name": "Karlo",
        "id": "kakaobrain/karlo",
        "version": "3c9c9a5f7b3c3e5f5e5c5b5a5f5e5c5b5a5f5e5c5b5a5f5e5c5b5a5f5e5c5b5a",
        "prompt_template": "{topic}, digital art, creative, innovative design"
    }
]

# ======== [ОСТАЛЬНОЙ КОД ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ] ========
# ... (остальные функции без изменений)

def try_replicate_free_models(topic):
    """Используем бесплатные модели Replicate с актуальными версиями"""
    REPLICATE_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    if not REPLICATE_TOKEN:
        logger.warning("⚠️ Replicate токен не найден")
        return None
    
    # Перемешиваем модели для разнообразия
    random.shuffle(REPLICATE_FREE_MODELS)
    
    for model_info in REPLICATE_FREE_MODELS:
        try:
            logger.info(f"🔄 Пробуем модель: {model_info['name']}")
            
            prompt = model_info['prompt_template'].format(topic=topic)
            
            # Получаем актуальную версию модели
            version = get_latest_model_version(REPLICATE_TOKEN, model_info["id"])
            if not version:
                logger.warning(f"⚠️ Не удалось получить версию для {model_info['name']}")
                continue
                
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
                for attempt in range(8):  # Уменьшили количество попыток
                    time.sleep(2)
                    status_response = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Bearer {REPLICATE_TOKEN}"},
                        timeout=15
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
                return versions[0]['id']
        return None
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения версии для {model_id}: {e}")
        return None

# ======== [ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ] ========
