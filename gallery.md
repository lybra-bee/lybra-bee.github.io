---
layout: default
title: Галерея
---
<h1>Галерея изображений</h1>
<div class="gallery-grid">
  {% for post in site.posts %}
    <div class="gallery-item">
      <!-- Поддержка .png и .jpg -->
      {% assign image_base = post.image | split: '.' | first %}
      {% assign image_png = image_base | append: '.png' %}
      {% assign image_jpg = image_base | append: '.jpg' %}
      {% if site.static_files contains image_png %}
        <img src="{{ image_png | relative_url }}" alt="{{ post.title | escape }}" loading="lazy">
      {% elsif site.static_files contains image_jpg %}
        <img src="{{ image_jpg | relative_url }}" alt="{{ post.title | escape }}" loading="lazy">
      {% else %}
        <img src="/assets/images/placeholder.png" alt="Нет изображения для {{ post.title | escape }}" loading="lazy">
      {% endif %}
    </div>
  {% endfor %}
</div>
<p>Галерея привязана к постам. Добавляйте изображения в assets/images/posts/.</p>
