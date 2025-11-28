---
layout: post
title: "Урок 2. Stable Diffusion от А до Я — первое изображение за 10 минут"
date: 2025-11-28 11:00:00 +0300
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
Первое изображение за 10 минут (даже если ты никогда ничего не устанавливал)

Сегодня ты сделаешь то, что ещё два года назад казалось фантастикой:  
запустить самую мощную открытую модель генерации изображений **прямо в браузере**, бесплатно и без единой установки на компьютер.

### Что мы будем использовать
- Google Colab (бесплатный GPU T4 16 ГБ)  
- Библиотека Hugging Face Diffusers (самая удобная в 2025 году)  
- Три модели на выбор: Stable Diffusion 1.5 → SDXL → Flux.1 (новейшая)

### Готовый ноутбук — открой одной кнопкой

[Запустить Stable Diffusion в Google Colab прямо сейчас](https://colab.research.google.com/drive/1T5f5iN7d2rK8v9mXz1pQb3cR4sT6uV7w?usp=sharing)

(или скопируй код ниже в новый Colab)

### Полный код урока (всё в одной ячейке — просто нажми ▶️)

```python
# ╔══════════════════════════════════════════════════════════╗
# ║   STABLE DIFFUSION В COLAB — УРОК 2 (2025)               ║
# ╚══════════════════════════════════════════════════════════╝

# 1. Установка (один раз, 2–3 минуты)
!pip install -q diffusers transformers accelerate ftfy bitsandbytes==0.43.3 --extra-index-url https://pypi.org/simple
!pip install -q torch==2.3.0+cu121 torchvision --extra-index-url https://download.pytorch.org/whl/cu121

import torch
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, FluxPipeline
from IPython.display import display

print("Установка завершена! Запускаем модель...")

# ──────────────────────────────
# Вариант А — классический Stable Diffusion 1.5 (самый быстрый и надёжный)
# ──────────────────────────────
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None,
    requires_safety_checker=False
)
pipe = pipe.to("cuda")

# ──────────────────────────────
# Вариант Б — SDXL (максимум качества)
# Раскомментируй эти строки и закомментируй блок выше
# ──────────────────────────────
# pipe = StableDiffusionXLPipeline.from_pretrained(
#     "stabilityai/stable-diffusion-xl-base-1.0",
#     torch_dtype=torch.float16,
#     variant="fp16"
# )
# pipe = pipe.to("cuda")

# ──────────────────────────────
# Вариант В — Flux.1-dev (самая новая на ноябрь 2025)
# Раскомментируй, если хочешь ультра-качество
# ──────────────────────────────
# pipe = FluxPipeline.from_pretrained(
#     "black-forest-labs/FLUX.1-dev",
#     torch_dtype=torch.bfloat16
# )
# pipe.enable_model_cpu_offload()

# ──────────────────────────────
# Твой промпт — меняй сколько угодно!
# ──────────────────────────────
prompt = "красивая русская девушка в киберпанк-городе ночью, неоновые огни, дождь, высокое качество, кинематографично, 8k"

image = pipe(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]
display(image)

print("Готово! Меняй строку prompt и запускай снова — без ограничений")
---
Как это работает (по-человечески)
Модель загружает миллиарды параметров на видеокарту
Начинает с чистого шума
За 30 шагов «вычитает» шум, пока не получится твоя картинка
Всё происходит прямо в облаке Google — твой ноутбук может быть выключен
Домашнее задание (обязательное и очень приятное)
Сгенерируй минимум 5 своих изображений
Одно из них сделай максимально безумным (например: «кот в костюме космонавта пьёт кофе на Луне»)
Сохрани лучшие 3
Выложи в сторис или пост с хештегом #МойПервыйStableDiffusion
→ я лично посмотрю и выберу 5 самых крутых — авторы получат доступ к закрытому уроку по LoRA раньше всех!
Идеи промптов для старта
аниме-девушка с голубыми волосами в древней библиотеке
киберпанк-Москва 2077, дождь, отражение в луже
милый пушистый дракон пьёт кофе в кофейне утром
фотография енота в деловом костюме за ноутбуком, реалистично
Что дальше?
Понедельник 1 декабря — Лайфхак: как ускорить генерацию в 5 раз
Пятница 5 декабря — Урок 3: ControlNet — рисуем по своим скетчам и фото
Сохрани этот ноутбук себе в Google Drive — он навсегда останется твоим личным генератором картинок.
До понедельника, будущий цифровой художник!
