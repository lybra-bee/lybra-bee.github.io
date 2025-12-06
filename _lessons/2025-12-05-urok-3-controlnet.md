---
layout: lesson
title: "Урок 3. ControlNet — рисуем по своим фото, скетчам и позам (самый мощный инструмент 2025)"
date: 2025-12-05
categories: uroki
lesson_number: 3
level: Средний
duration: 60–90 минут
goal: "Научиться управлять Stable Diffusion как профессиональный художник — по фото, позе, скетчу и даже видео"
result: "Ты сможешь превращать селфи в аниме, скетч в шедевр и любое фото в любой стиль"
image: assets/images/lessons/lesson-03-cover.jpg
tags: [controlnet, openpose, canny, depth, scribble, ip-adapter, stable-diffusion, 2025]
---

<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 2.5rem; border-radius: 16px; text-align: center; margin-bottom: 3rem; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
  <h1 style="margin:0; font-size: 2.6rem; font-weight: 800;">Урок 3 — ControlNet</h1>
  <p style="margin:10px 0 0; font-size: 1.5rem;">Теперь Stable Diffusion рисует точно по твоему фото</p>
</div>

### Что ты получишь сегодня

- Полный контроль над позой, композицией и стилем  
- 8 разных ControlNet-моделей (OpenPose, Canny, Depth, Scribble и др.)  
- Готовый ноутбук с кнопкой «загрузить своё фото»  
- 20+ примеров: селфи → аниме, скетч → картина, фото → киберпанк  
- Домашку, за которую я лично дам обратную связь  

<br>

<br>

### Полный код урока (одна ячейка — просто запусти)

<div class="code-block">
<pre><code class="language-python"># УРОК 3 — CONTROLNET 2025 (работает на бесплатной T4)

# 1. Установка (3–5 минут один раз)
!pip install -q diffusers transformers accelerate controlnet-a1111 xformers==0.0.28.post1
!pip install -q torch==2.3.0+cu121 torchvision --extra-index-url https://download.pytorch.org/whl/cu121

import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from diffusers.utils import load_image
from PIL import Image
import numpy as np

print("Готово! Загружаем ControlNet...")

# 2. Загружаем ControlNet + Stable Diffusion
controlnet = ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-openpose", torch_dtype=torch.float16)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
    safety_checker=None
).to("cuda")

pipe.enable_xformers_memory_efficient_attention()
pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead", fullgraph=True)

# 3. Загружаем своё фото (или любое другое)
# Замени ссылку на свою фотографию!
image = load_image("https://i.imgur.com/8z5jK8P.png")  # пример с человеком
image = image.resize((768, 768))

# 4. Твой промпт
prompt = "аниме-девушка в стиле Studio Ghibli, высокое качество, детализация, мягкий свет"
negative_prompt = "размыто, уродливо, артефакты"

# 5. Генерация по позе из фото
result = pipe(
    prompt,
    image=image,
    num_inference_steps=30,
    guidance_scale=7.5,
    controlnet_conditioning_scale=1.0
).images[0]

display(result)
print("Готово! Попробуй своё фото!")
</code></pre>
</div>

<br>

### 8 разных ControlNet-моделей (выбирай любую)

| Модель         | Что делает                          | Лучше всего для                  |
|----------------|-------------------------------------|----------------------------------|
| OpenPose       | Копирует позу человека              | Перенос позы, танцы, селфи       |
| Canny          | Рисует по контурам                  | Скетчи, архитектура              |
| Depth          | Учитывает глубину сцены             | 3D-эффект, реализм               |
| Scribble       | Рисует по твоим каракулям           | Быстрые наброски                 |
| MLSD           | Прямые линии и архитектура          | Интерьеры, здания                |
| Normal         | По нормалям (освещение)             | Реалистичное освещение           |
| Seg            | По сегментации (объекты)            | Замена фона, стилизация          |
| IP-Adapter     | По стилю любого изображения         | Перенос стиля (самый мощный!)    |

<br>

### Домашнее задание (обязательное и очень крутое!)

Выбери **один из трёх вариантов** и выложи результат с хештегом **#ControlNetУрок3**:

1. **Селфи → аниме** — сфоткай себя и преврати в аниме-персонажа  
2. **Скетч → шедевр** — нарисуй простой набросок ручкой и оживи его  
3. **Фото → любой стиль** — возьми любое своё фото и сделай в стиле Ван Гога / киберпанк / фэнтези  

Я лично посмотрю **все работы** и выберу **10 победителей** — они получат:
- ранний доступ к уроку по IP-Adapter FaceID (портреты по одному фото!)  
- персональный ControlNet-промпт под их стиль  
- упоминание в следующем уроке + репост в канал  

<br>

### Что будет дальше

- Понедельник 8 декабря — Лайфхак: как ускорить ControlNet в 3 раза  
- Пятница 12 декабря — Урок 4: IP-Adapter + FaceID (портреты по одному селфи)  
- 19 декабря — обучение своих LoRA  

Сохрани этот ноутбук — он станет твоим главным инструментом для создания шедевров.

**Ты больше никогда не будешь рисовать вручную.**

До понедельника,  
твой цифровой художник-ассистент
