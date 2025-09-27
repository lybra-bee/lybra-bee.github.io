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
</div>
