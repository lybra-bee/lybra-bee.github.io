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
        <img src="{{ post.image | relative_url }}" alt="{{ post.title | escape }}" data-bs-toggle="modal" data-bs-target="#galleryModal" data-src="{{ post.image | relative_url }}">
        <figcaption>{{ post.title | escape }}</figcaption>
      </figure>
      {% endif %}
    {% endfor %}
  </div>
</div>

<!-- Модальное окно -->
<div class="modal fade" id="galleryModal" tabindex="-1" aria-labelledby="galleryModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-body">
        <img src="" class="img-fluid" id="modalImage">
      </div>
    </div>
  </div>
</div>
