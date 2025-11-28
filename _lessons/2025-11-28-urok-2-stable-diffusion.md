---
layout: post
title: "Урок 2. Stable Diffusion от А до Я — первое изображение за 10 минут"
date: 2025-11-28 
categories: uroki
lesson_number: 2
level: Новичок
duration: 60–90 минут
goal: "Запустить Stable Diffusion в браузере и создать свои первые ИИ-картинки"
result: "Вечный генератор изображений в твоём Google Drive"
image: /assets/images/lessons/image-8.jpg
image_alt: "Первое изображение, созданное тобой"
tags: [stable-diffusion, colab, генерация, искусство]
---

{% include lesson-header.html %}

# Урок 2. Stable Diffusion от А до Я  
Первое изображение за 10 минут — даже если ты никогда ничего не устанавливал

Сегодня ты получишь в руки настоящую магию 2025 года.

<br>

### Готовый ноутбук — одна кнопка

<a href="https://colab.research.google.com/drive/1T5f5iN7d2rK8v9mXz1pQb3cR4sT6uV7w?usp=sharing" target="_blank" class="btn btn-success btn-lg">
  Запустить Stable Diffusion прямо сейчас
</a>

<br><br>

### Полный код урока (одна ячейка)

```python
# STABLE DIFFUSION В COLAB — УРОК 2 (ноябрь 2025)

# Установка (2–4 минуты один раз)
!pip install -q diffusers transformers accelerate ftfy bitsandbytes==0.43.3
!pip install -q torch==2.3.0+cu121 torchvision --extra-index-url https://download.pytorch.org/whl/cu121

import torch
from diffusers import StableDiffusionPipeline
from IPython.display import display

print("Установка завершена. Загружаем модель...")

# Самая быстрая и надёжная модель 2025 года
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None,
    requires_safety_checker=False
).to("cuda")

# Твой первый промпт — меняй сколько угодно
prompt = "красивая русская девушка в киберпанк-городе ночью, неоновые вывески на кириллице, дождь, отражения в лужах, кинематографично, 8k, ультра детализация"
negative_prompt = "размыто, уродливо, артефакты, лишние пальцы, плохая анатомия"

image = pipe(
    prompt,
    negative_prompt=negative_prompt,
    num_inference_steps=30,
    guidance_scale=7.5
).images[0]

display(image)
print("Готово! Меняй prompt и жми ▶️ снова — без ограничений")

```markdown
<br>

### 10 лайфхаков для идеальных промптов

- Пиши на русском — модель понимает отлично  
- Добавляй стиль: «в стиле Ван Гога», «аниме», «фотография на плёнку»  
- Указывай качество: «8k», «masterpiece», «highly detailed»  
- Используй negative_prompt (что НЕ должно быть)  
- Управляй светом: «золотой час», «неон ночью»  
- Добавляй эмоции: «грустная», «мечтательная»  
- Указывай ракурс: «портрет крупным планом», «вид сзади»  
- Добавляй окружение: «в древней библиотеке», «на Марсе»  
- Сохраняй лучшие промпты в отдельный файл  

<br>

### Домашнее задание (обязательное!

- Сгенерируй минимум 10 картинок  
- Одну сделай максимально безумной (кот-космонавт приветствуется)  
- Три лучшие выложи с хештегом #МойПервыйStableDiffusion  
- Я лично посмотрю все работы и выберу 5 победителей → они получат ранний доступ к уроку по обучению своих LoRA

<br>

### Что дальше

Понедельник 1 декабря — как ускорить генерацию в 5–10 раз  
Пятница 5 декабря — Урок 3: ControlNet (рисуем по своим фото и скетчам)

<br>

Сохрани этот ноутбук в свой Google Drive — он будет работать вечно.  
Через год ты откроешь его и скажешь:  
«Вот с этого всё началось».

До понедельника,  
твой будущий цифровой соавтор
