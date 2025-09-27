---
layout: default
title: Галерея
---
<h1>Галерея изображений</h1>
<div class="gallery-grid">
  {% for file in site.static_files %}
    {% if file.path contains 'assets/images/posts' and file.extname == '.png' or file.extname == '.jpg' %}
      <div class="gallery-item">
        <a href="{{ file.path | relative_url }}" target="_blank">
          <img src="{{ file.path | relative_url }}" alt="Галерея изображение: {{ file.name | remove: file.extname }}" loading="lazy" width="200" height="200">
        </a>
      </div>
    {% endif %}
  {% endfor %}
  {% if site.static_files | where: "path", "assets/images/posts" | size == 0 %}
    <p>Пока нет изображений в галерее. Добавьте файлы в assets/images/posts/.</p>
  {% endif %}
</div>
<p>Галерея показывает все изображения из assets/images/posts/ (.png и .jpg). Нажмите на миниатюру для просмотра в полном размере.</p>
