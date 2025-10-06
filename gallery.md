---
layout: default
title: Галерея
description: Галерея изображений проектов Lybra AI
---

<div class="container py-4">
  <h1 class="text-center mb-2">Галерея</h1>
  <p class="text-center mb-5">Галерея изображений проектов Lybra AI</p>
  <div class="gallery">
    {% for image in site.data.gallery %}
    <figure class="gallery-item">
      <img src="{{ image.src | relative_url }}" alt="{{ image.alt }}" data-bs-toggle="modal" data-bs-target="#galleryModal" data-src="{{ image.src | relative_url }}">
      <figcaption>{{ image.caption }}</figcaption>
    </figure>
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
