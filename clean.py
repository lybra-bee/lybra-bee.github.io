import os
import shutil

# Путь к корню репозитория
repo_path = "/home/user/lybra-bee.github.io"  # <-- замени на свой путь

# Список явных лишних файлов/папок (относительно repo_path)
remove_paths = [
    "static/css/style.css",
    "static/images/gallery.html",
    "data/gallery.json",
    "content/articles.md"
]

# Проверка и удаление лишних файлов
for rel_path in remove_paths:
    full_path = os.path.join(repo_path, rel_path)
    if os.path.exists(full_path):
        if os.path.isfile(full_path):
            os.remove(full_path)
            print(f"Удален файл: {rel_path}")
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
            print(f"Удалена папка: {rel_path}")
    else:
        print(f"Файл/папка не найдены: {rel_path}")

# Дополнительно проверим дубли CSS
css_assets = os.path.join(repo_path, "assets/css/main.css")
css_static = os.path.join(repo_path, "static/css/main.css")

if os.path.exists(css_assets) and os.path.exists(css_static):
    print("Найдены два main.css: оставляем только assets/css/main.css")
    os.remove(css_static)
    print("Удален файл: static/css/main.css")

print("Очистка завершена!")
