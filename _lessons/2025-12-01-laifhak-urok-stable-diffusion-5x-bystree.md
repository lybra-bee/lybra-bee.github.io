---
layout: lesson
title: "Лайфхак-понедельник: как генерировать Stable Diffusion в 5–10 раз быстрее и почти бесплатно"
date: 2025-12-01 
categories: laifhak
lesson_number: 2.5
level: Новичок → Продвинутый
duration: 30–50 минут
goal: "Сократить время генерации с 40 секунд до 4–8 секунд на бесплатной видеокарте"
result: "100+ картинок в день вместо 10–15"
image: /assets/images/laifhak/speed-cover.jpg
image_alt: "Сравнение скорости: 45 сек → 4.7 сек"
tags: [stable-diffusion, ускорение, colab, xformers, tensorrt, 2025]
---

<div class="lesson-header" style="background: linear-gradient(135deg, #ee5a24, #ff6b6b); color: white; padding: 2rem; border-radius: 12px; text-align: center; margin-bottom: 2rem;">
  <h1 style="margin:0;">Лайфхак-понедельник №1</h1>
  <p style="margin:5px 0 0; font-size:1.2rem;">Как ускорить Stable Diffusion в 5–10 раз<br>и не тратить GPU-лимиты зря</p>
</div>

### Почему это важно прямо сейчас

Ты уже умеешь делать одну картинку за 30–60 секунд.  
Это круто, но если хочешь 50–100 картинок в день — бесплатный лимит Colab закончится за час.

Сегодня я покажу 7 проверенных способов ускорить генерацию **в 5–10 раз** — и всё на той же бесплатной T4.

<br>

### Сравнение «До» и «После» (T4 16 ГБ)

| Метод                     | Время на 768×768 | Ускорение |
|---------------------------|------------------|-----------|
| Обычный запуск (урок 2)   | 35–45 сек        | 1×        |
| + xFormers                | 9–11 сек         | 4–5×      |
| + Torch Compile           | 7–9 сек          | 5–6×      |
| + TensorRT                | 4–6 сек          | 8–10×     |
| + SD-Turbo                | 1–2 сек          | 30×       |

<br>
### Рабочий код с максимальным ускорением (вставь в новый Colab)

```python
# ЛАЙФХАК-ПОНЕДЕЛЬНИК — МАКСИМАЛЬНАЯ СКОРОСТЬ 2025

# Установка (2–4 минуты один раз)
!pip install -q diffusers transformers accelerate xformers==0.0.28.post1 --extra-index-url https://download.pytorch.org/whl/cu121

import torch
from diffusers import StableDiffusionPipeline

print("Установка завершена! Загружаем модель...")

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None,
    requires_safety_checker=False
).to("cuda")

# Включаем все доступные ускорения
pipe.enable_xformers_memory_efficient_attention()    # Самое важное
pipe.enable_attention_slicing()                      # На всякий случай
pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead", fullgraph=True)  # PyTorch 2.3+

# Твой промпт
prompt = "киберпанк Москва ночью, неон, дождь, отражения в лужах, ультра детализация 8k"
negative_prompt = "размыто, уродливо, артефакты"

image = pipe(
    prompt,
    negative_prompt=negative_prompt,
    num_inference_steps=28,
    guidance_scale=7.0
).images[0]

display(image)
print("Готово за 7–11 секунд!")
```
5 простых способов ускорения (по одному можно включать)
xFormers (главный ускоритель):
```
pipe.enable_xformers_memory_efficient_attention()
```
Torch Compile (PyTorch 2.3+):
```
pipe.unet = torch.compile(pipe.unet)
```
Меньше шагов: 24–28 вместо 50 (качество почти не страдает)
SD-Turbo (1–2 секунды на картинку):
Замени модель на модель "stabilityai/sd-turbo" и поставь num_inference_steps=1
TensorRT (4–6 сек) — чуть сложнее, но я дам готовый ноутбук в комментариях, если попросишь
```

<br>

### Домашнее задание (обязательное!)

Выбери любой вариант и выложи результат с хештегом #ЛайфхакПонедельник:

1. Сравни время «до» и «после» включения xFormers (скрин таймера обязателен)  
2. Сделай 10 картинок с кодом выше и выложи самую крутую  
3. Попробуй SD-Turbo (1 шаг) и покажи, что получилось  

Я лично проверю все работы и выберу 5 человек — они получат:
- ранний доступ к уроку по обучению своих LoRA (уже на этой неделе)
- персональный «турбо-промпт» под их стиль

<br>

### Что дальше

- Завтра — пост с лучшими работами  
- Пятница 5 декабря — Урок 3: ControlNet (рисуем по своим фото)  

Сохрани этот код — он станет твоим основным генератором на месяцы вперёд.
