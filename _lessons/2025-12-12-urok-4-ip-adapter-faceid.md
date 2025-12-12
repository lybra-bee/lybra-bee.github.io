---
layout: lesson
title: "Урок 4. IP-Adapter + FaceID — делаем идеальные портреты по одному селфи (лучшее в 2025)"
date: 2025-12-12
categories: uroki
lesson_number: 4
level: Средний → Продвинутый
duration: 70–120 минут
goal: "Научиться создавать идеальные портреты любого человека по одному фото — в любом стиле, возрасте и образе"
result: "Твой личный «голливудский гримёр» + 50+ портретов себя и друзей"
image: /assets/images/lessons/grok_image_x8rafoe.jpg
image_alt: "Одно селфи → 1000 идеальных портретов"
tags: [ip-adapter, faceid, portrait, lora, stable-diffusion, 2025]
---

<div style="background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); color: white; padding: 3rem; border-radius: 20px; text-align: center; margin-bottom: 3rem; box-shadow: 0 15px 40px rgba(0,0,0,0.3);">
  <h1 style="margin:0; font-size: 2.8rem; font-weight: 900;">Урок 4 — IP-Adapter + FaceID</h1>
  <p style="margin:15px 0 0; font-size: 1.7rem;">Одно селфи = миллион идеальных портретов<br>в любом стиле, возрасте и образе</p>
</div>

### Что ты получишь сегодня

- Понимание, как работают самые мощные модели портретов 2025 года  
- Готовый ноутбук с FaceID v2 + IP-Adapter Plus  
- 30+ примеров: ты → аниме, ты → супергерой, ты → в 80 лет  
- Домашку, за которую я лично дам обратную связь и подарки  

<br>

### Готовый ноутбук — одна кнопка (уже с FaceID)

<a href="https://colab.research.google.com/drive/1B2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7?usp=sharing" target="_blank" class="btn btn-success btn-lg mb-4">
  Запустить IP-Adapter + FaceID прямо сейчас
</a>

<br>

### Полный код урока (одна ячейка)

<div class="code-block">
<pre><code class="language-python"># УРОК 4 — IP-ADAPTER + FACEID V2 (декабрь 2025)

# 1. Установка (5–7 минут один раз)
!pip install -q diffusers transformers accelerate insightface onnxruntime-gpu
!pip install -q torch==2.3.0+cu121 torchvision --extra-index-url https://download.pytorch.org/whl/cu121

import torch
from diffusers import StableDiffusionXLPipeline
from diffusers.utils import load_image
from insightface.app import FaceAnalysis
import cv2
import numpy as np
from IPython.display import display

print("Готовим FaceID...")

# 2. Загружаем модели
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
).to("cuda")

# IP-Adapter + FaceID
pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors")
pipe.load_ip_adapter("h94/IP-Adapter-FaceID", subfolder="sdxl_models", weight_name="ip-adapter-faceid-plusv2_sdxl.bin")

app = FaceAnalysis(name="buffalo_l", providers=['CUDAExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

print("Готово! Загрузи своё селфи")

# 3. Загрузи своё селфи (замени ссылку!)
face_image = load_image("https://i.imgur.com/your-selfie.jpg")  # ←←← СЮДА СВОЁ ФОТО!
face_image = face_image.convert("RGB")

# 4. Извлекаем FaceID
faces = app.get(cv2.cvtColor(np.array(face_image), cv2.COLOR_RGB2BGR))
faceid_embeds = torch.from_numpy(faces[0].normed_embedding).unsqueeze(0)

# 5. Твой промпт
prompt = "портрет той же девушки в стиле Studio Ghibli, аниме, высокое качество, детализация"
negative_prompt = "размыто, уродливо, деформированное лицо"

# 6. Генерация
image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    ip_adapter_image=face_image,
    faceid_embeds=faceid_embeds,
    num_inference_steps=30,
    guidance_scale=5.0,
    controlnet_conditioning_scale=0.8
).images[0]

display(image)
print("Готово! Меняй промпт и запускай снова")
</code></pre>
</div>

<br>

### 30+ идей промптов (просто меняй и запускай)

| Стиль                    | Промпт                                                                 |
|--------------------------|-------------------------------------------------------------------------|
| Аниме                    | "портрет той же девушки в стиле аниме, Studio Ghibli, мягкий свет"     |
| Киберпанк                | "портрет той же девушки в киберпанк-городе, неон, дождь, 8k"           |
| Дисней                   | "Disney princess style portrait of the same girl, castle background"      |
| Ван Гог                  | "portrait of the same girl in Van Gogh style, starry night background"   |
| Супергерой              | "the same girl as Marvel superhero, dramatic lighting, epic pose"         |
| 80 лет                   | "the same girl at 80 years old, wise, detailed skin, soft lighting"     |
| Мужчина                  | "the same person as handsome man, short hair, business suit"             |

<br>

### Домашнее задание (обязательное и очень крутое!)

Сделай **один из трёх вариантов** и выложи с хештегом **#FaceIDУрок4**:

1. **Себя в 10 стилях** — одно селфи → 10 разных образов  
2. **Сериал из 5 фото** — ты в 10, 20, 40, 60, 80 лет  
3. **Друзья и семья** — сделай портреты близких (с их разрешения!)  

Я лично посмотрю **все работы** и выберу **10 победителей** — они получат:
- ранний доступ к уроку по обучению своих LoRA (уже 19 декабря!)
- персональный FaceID-ноутбук под их лицо
- упоминание в следующем уроке + репост в канал

<br>

### Что дальше

- Понедельник 15 декабря — Лайфхак: как ускорить FaceID в 5 раз  
- Пятница 19 декабря — Урок 5: обучение своих LoRA (свой стиль за 15 минут)  

Сохрани этот ноутбук — он будет делать идеальные портреты вечно.

**Теперь ты можешь стать кем угодно.**

До понедельника,  
твой цифровой двойник
