import os
for i in range(8):
bbox = [random.randint(-200, w), random.randint(-200, h), random.randint(0, w+200), random.randint(0, h+200)]
color = tuple(random.randint(60, 230) for _ in range(3))
draw.ellipse(bbox, fill=color, outline=None)
img = img.filter(ImageFilter.GaussianBlur(radius=6))
try:
font = ImageFont.truetype('DejaVuSans-Bold.ttf', 36)
except Exception:
font = ImageFont.load_default()
draw.text((40, h-120), text_prompt[:80], font=font, fill=(255, 255, 255))
out_path = IMAGES_DIR / filename
img.save(out_path, 'PNG')
return out_path




def git_commit_and_push(filepaths, message):
try:
subprocess.run(['git', 'add'] + [str(p) for p in filepaths], check=True)
subprocess.run(['git', 'commit', '-m', message], check=True)
subprocess.run(['git', 'push'], check=True)
print('Коммит и пуш успешны.')
except subprocess.CalledProcessError as e:
print('Ошибка git:', e)




if __name__ == '__main__':
topic = random.choice(TOPICS)
post_type = random.choice(TYPES)


# 1) Текст: пробуем Groq → OpenRouter → fallback
try:
if GROQ_API_KEY:
title, text = generate_text_groq(topic, post_type)
elif OPENROUTER_API_KEY:
title, text = generate_text_openrouter(topic, post_type)
else:
title, text = generate_text_fallback(topic, post_type)
except Exception as e:
print("Ошибка API:", e)
title, text = generate_text_fallback(topic, post_type)


# 2) Markdown
date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
slug = title.lower().replace(' ', '-').replace(':', '').replace(',', '')
filename_md = f"{datetime.utcnow().strftime('%Y-%m-%d')}-{slug}.md"
md_path = CONTENT_DIR / filename_md
content = f"---\ntitle: \"{title}\"\ndate: {date}\ntags: [\"{topic}\"]\nfeatured_image: /assets/images/posts/{slug}.png\n---\n\n{text}\n"
with open(md_path, 'w', encoding='utf-8') as f:
f.write(content)


# 3) Картинка
img_filename = f"{slug}.png"
img_path = generate_image_fallback(title, img_filename)


# 4) Git push
git_commit_and_push([md_path, img_path], f"📄 Автогенерация: {title}")
print('Готово. Файл:', md_path, 'Изображение:', img_path)
