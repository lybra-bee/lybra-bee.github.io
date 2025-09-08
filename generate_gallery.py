#!/usr/bin/env python3
import os
import yaml
from datetime import datetime

# Путь к папке с изображениями
images_dir = "static/images/posts"
# Путь к файлу gallery.yaml
output_file = "data/gallery.yaml"

# Получаем список всех изображений
images = sorted(os.listdir(images_dir))

gallery_list = []

for img in images:
    if img.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
        gallery_list.append({
            "src": f"/images/posts/{img}",
            "alt": img.replace("-", " ").replace("_", " ").split(".")[0],
            "title": img.replace("-", " ").replace("_", " ").split(".")[0],
            "date": datetime.now().strftime("%Y-%m-%d")
        })

# Создаем папку data, если её нет
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Сохраняем в YAML
with open(output_file, "w", encoding="utf-8") as f:
    yaml.dump(gallery_list, f, allow_unicode=True)

print(f"✅ Файл {output_file} успешно создан с {len(gallery_list)} изображениями.")
