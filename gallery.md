---
layout: default
title: Галерея
---
<h1>Галерея изображений</h1>
<div class="gallery-grid">
  {% assign images = site.static_files | where: "relative_path", "assets/images/posts" | where_exp: "item", "item.path | contains: '.png' or item.path | contains: '.jpg'" %}
  {% for image in images %}
    <div class="gallery-item">
      <img src="{{ image.path | relative_url }}" alt="Галерея изображение: {{ image.name | remove: image.extname }}" loading="lazy">
    </div>
  {% endfor %}
  {% if images.size == 0 %}
    <p>Пока нет изображений в галерее. Добавьте файлы в assets/images/posts/.</p>
  {% endif %}
</div>
<p>Галерея показывает все изображения из assets/images/posts/ (.png и .jpg). Добавляйте новые по мере создания постов.</p>
