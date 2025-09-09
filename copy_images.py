#!/usr/bin/env python3
import os
import shutil

# Пути
static_dir = "static/images/posts"
assets_dir = "assets/images/posts"

# Создаём папку, если её нет
os.makedirs(assets_dir, exist_ok=True)

# Копируем файлы
count = 0
for filename in os.listdir(static_dir):
    if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".svg")):
        src = os.path.join(static_dir, filename)
        dst = os.path.join(assets_dir, filename)
        shutil.copy2(src, dst)
        count += 1

print(f"✅ Скопировано {count} изображений из {static_dir} в {assets_dir}")
