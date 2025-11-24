---
layout: post
title: post
title: "Лайфхак-понедельник: 7 ошибок в Google Colab, которые крадут у тебя часы (и как их убить за 30 секунд)"
date: 2025-11-24
categories: lajfhaki
tags: [colab, ошибки, лайфхаки, python, 2025]
image: /assets/images/lajfhaki/image-7.jpg
image_alt: "Грустный робот и куча ошибок в Colab"
---

# Лайфхак-понедельник  
7 ошибок в Google Colab, из-за которых ты теряешь часы (и нервы)

Только за последнюю неделю 200+ человек из курса написали:  
«У меня ничего не работает…»

99 % случаев — это одни и те же 7 ошибок.  
Разбираем их все за 5 минут, чтобы ты больше никогда не тратил на них время.

### Ошибка №1 — Запускаешь ячейки не по порядку
Получаешь `NameError`, потому что переменная объявилась позже.

Решение за 2 секунды:  
Меню → **Runtime → Restart and run all** (или горячие клавиши **Ctrl + M .**)

### Ошибка №2 — Нет GPU, и обучение идёт 40 минут вместо 40 секунд
Как включить раз и навсегда:  
**Runtime → Change runtime type → Hardware accelerator → GPU (T4 или A100) → Save**

### Ошибка №3 — Забыл установить библиотеки
    !pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    !pip install -q diffusers transformers accelerate ftfy

Делай это в самой первой ячейке — и никаких `ModuleNotFoundError`.

### Ошибка №4 — Файлы исчезли после переподключения
Colab — временная машина. Всё стирается через 12 часов.

Надёжное решение — сразу подключай Google Drive:
    from google.colab import drive
    drive.mount('/content/drive')
    # теперь сохраняй всё в /content/drive/MyDrive/...

### Ошибка №5 — Закончился бесплатный лимит GPU
Тебя перекидывает на CPU и всё тормозит.

Варианты:
- Colab Pro / Pro+ (очень рекомендую)
- Жди 24 часа (лимит обновляется)
- Хитрый способ: второй Google-аккаунт

### Ошибка №6 — Упала сессия: «RAM crashed»
Быстрое спасение:
    import gc
    import torch
    gc.collect()
    torch.cuda.empty_cache()

Или просто **Runtime → Factory reset runtime**

### Ошибка №7 — Потерял весь код, потому что не сохранил
Делай двойное сохранение:  
**File → Save a copy in Drive**  
**File → Save a copy in GitHub**

### Бонус: мой личный шаблон Colab 2025
    # ШАБЛОН COLAB 2025 — вставляй первым делом
    from google.colab import drive
    drive.mount('/content/drive')

    # Проверяем GPU
    !nvidia-smi

    # Очистка памяти
    import gc, torch
    gc.collect()
    torch.cuda.empty_cache()

    print("Готов к бою")

Сохрани этот шаблон в папку «Colab Notebooks → Templates» — и будешь начинать любой проект за 5 секунд.

### Домашка на 30 секунд
Открой любой свой (или мой перцептрон из пятницы) ноутбук прямо сейчас и:
1. Включи GPU  
2. Перезапусти и запусти все ячейки  

Напиши в комментариях или в сторис, во сколько раз быстрее стало — отмечу лучшие ответы!

В пятницу 28 ноября — самый долгожданный урок:  
**Stable Diffusion от А до Я — первое изображение за 10 минут.**

Сохрани этот пост — он спасёт тебя десятки раз.

До пятницы!
