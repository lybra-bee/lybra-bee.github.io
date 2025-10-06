---
layout: default
title: Статьи
description: Статьи о гибридном ИИ и IoT
---

<section class="articles-carousel container my-4">
  <div id="articlesCarousel" class="carousel slide" data-bs-ride="carousel">
    <div class="carousel-inner">
      {% for post in site.posts limit:5 %}
      <div class="carousel-item {% if forloop.first %}active{% endif %}">
        <div class="card">
          <div class="card-body">
            <h3 class="card-title"><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
            <p class="card-text">{{ post.excerpt | strip_html | truncate: 100 }}</p>
            <a href="{{ post.url | relative_url }}" class="btn btn-outline-light">Читать далее</a>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    <button class="carousel-control-prev" type="button" data-bs-target="#articlesCarousel" data-bs-slide="prev">
      <span class="carousel-control-prev-icon" aria-hidden="true"></span>
      <span class="visually-hidden">Предыдущий</span>
    </button>
    <button class="carousel-control-next" type="button" data-bs-target="#articlesCarousel" data-bs-slide="next">
      <span class="carousel-control-next-icon" aria-hidden="true"></span>
      <span class="visually-hidden">Следующий</span>
    </button>
  </div>
</section>
