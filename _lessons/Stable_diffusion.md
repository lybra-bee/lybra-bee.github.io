---
layout: post
title: "Урок 2. Stable Diffusion от А до Я — первое изображение за 10 минут"
date: 2025-11-28
categories: uroki
lesson_number: 2
level: Новичок
duration: 35–45 минут
goal: "Запустить Stable Diffusion в браузере и сгенерировать свои первые ИИ-картинки по любому промпту"
result: "Работающий Colab + 15+ твоих первых шедевров"
image: /assets/images/lessons/lesson-02-cover.jpg
image_alt: "Твоё первое изображение, созданное Stable Diffusion прямо сейчас"
tags: [stable-diffusion, генерация изображений, colab, diffusers, flux]
---

{% include lesson-header.html %}

# Урок 2. Stable Diffusion от А до Я  
Первое изображение за 10 минут (даже если ты никогда не ставил ничего сложнее Telegram)

Сегодня ты сделаешь то, о чём мечтал весь 2023–2024 год:  
запустить самую мощную открытую модель генерации изображений **прямо в браузере**, бесплатно и без установки.

### Что мы будем использовать
- Google Colab (бесплатный GPU T4 16 ГБ)  
- Hugging Face Diffusers (самая удобная библиотека 2025 года)  
- Модели: Stable Diffusion 1.5 → SDXL → Flux.1 (новейшая и самая красивая)

### Запускаем всё одной кнопкой (10 секунд)

**Кликни и сразу начни** → вечная ссылка:  
[Открыть готовый ноутбук в Google Colab](https://colab.research.google.com/drive/1T5f5iN7d2rK8v9mXz1pQb3cR4sT6uV7w?usp=sharing)

(или скопируй код ниже в новый Colab)
### Полный код урока (всё в одной ячейке — просто запусти)

```python
# ╔══════════════════════════════════════════════════════════╗
# ║   STABLE DIFFUSION В COLAB — УРОК 2 (2025)               ║
# ╚══════════════════════════════════════════════════════════╝

# 1. Установка (один раз, ~2 минуты)
!pip install -q diffusers transformers accelerate ftfy bitsandbytes==0.43.3
!pip install -q torch==2.3.0+cu121 torchvision --extra-index-url https://download.pytorch.org/whl/cu121

import torch
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, FluxPipeline
from IPython.display import display
import time

# 2. Выбирай модель (раскомментируй нужную)
# Вариант А — классика (быстро и красиво)
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None
)

    # Вариант Б — SDXL (ещё красивее, но чуть медленнее)
    # pipe = StableDiffusionXLPipeline.from_pretrained(
    #     "stabilityai/stable-diffusion-xl-base-1.0",
    #     torch_dtype=torch.float16,
    #     variant="fp16"
    # )

    # Вариант В — Flux.1-dev (самая новая и крутая на ноябрь 2025)
    # pipe = FluxPipeline.from_pretrained(
    #     "black-forest-labs/FLUX.1-dev",
    #     torch_dtype=torch.bfloat16
    # )

    pipe = pipe.to("cuda")

    # 3. Генерация (меняй промпт сколько угодно!)
    prompt = "красивая русская девушка в киберпанк-городе ночью, неон, высокое качество, кинематографично"

    image = pipe(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]
    display(image)

    print("Готово! Теперь просто меняй строку prompt и запускай ячейку снова")

### Что происходит под капотом (по-человечески)

1. Мы берём готовую обученную модель (миллиарды параметров)  
2. Загружаем её на видеокарту в Colab (16 ГБ VRAM)  
3. Модель начинает с чистого шума  
4. За 20–50 шагов «вычитает» шум, пока не получится картинка по твоему описанию

### Домашнее задание (обязательное и очень приятное)

1. Сгенерируй 5 изображений по своим промптам  
2. Одно из них сделай максимально безумным (например: «кот в костюме космонавта едет на единороге по Марсу»)  
3. Сохрани лучшие 3 картинки  
4. Выложи их в сторис/пост с хештегом #МойПервыйStableDiffusion  
   → я лично посмотрю и выберу 5 самых крутых — авторы получат доступ к закрытому уроку по LoRA-обучению раньше всех!

### Промпты для вдохновения (просто копируй)

- «аниме-девушка с голубыми волосами в библиотеке древних книг, мягкий свет»  
- «киберпанк-Москва 2077 ночью, дождь, неон, отражение в луже»  
- «милый пушистый дракон пьёт кофе в кофейне, утро»  
- «фотография енота в деловом костюме за ноутбуком, реалистично»

### Что дальше?

- Понедельник 1 декабря — Лайфхак-понедельник: как ускорить генерацию в 5 раз и сэкономить GPU  
- Пятница 5 декабря — Урок 3: ControlNet — рисуем по своим скетчам и фотографиям  

Сохрани этот ноутбук себе в Google Drive → он будет твоим личным генератором картинок навсегда.

До понедельника, будущий цифровой художник!
