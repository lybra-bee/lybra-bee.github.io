---
layout: default
title: Галерея
description: Галерея изображений проектов Lybra AI
---

<div class="container py-4">
  <h1 class="text-center mb-2">Галерея</h1>
  <p class="text-center mb-5">Изображения проектов Lybra AI из статей</p>
  <div class="gallery">
    {% for post in site.posts %}
      {% if post.image %}
      <figure class="gallery-item">
        <img src="{{ post.image | relative_url }}" alt="{{ post.title | escape }}" data-bs-toggle="modal" data-bs-target="#galleryModal" data-large-src="{{ post.image | relative_url }}">
      </figure>
      {% endif %}
    {% endfor %}
  </div>
</div>

<!-- Модальное окно -->
<div class="modal fade" id="galleryModal" tabindex="-1" aria-labelledby="galleryModalLabel">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Закрыть"></button>
      </div>
      <div class="modal-body">
        <img src="" class="img-fluid" id="modalImage" alt="Увеличенное изображение">
      </div>
    </div>
  </div>
</div>
