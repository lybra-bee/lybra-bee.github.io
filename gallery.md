---
layout: default
title: Галерея
---
<h1>Галерея изображений</h1>
<div class="gallery-grid">
  {% for i in (1..10) %}
  <img src="/assets/images/posts/post-{{ i }}.jpg" alt="Изображение {{ i }}" loading="lazy" class="gallery-item">
  {% endfor %}
</div>
<p>Добавляйте изображения в assets/images/posts/ для новых статей.</p>
