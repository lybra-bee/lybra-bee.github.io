---
layout: default
title: Статьи
description: Последние обзоры и уроки по искусственному интеллекту.
---
<h1 class="text-center mb-4">Все статьи</h1>

<div id="articlesCarousel" class="carousel slide carousel-multi d-flex" data-bs-ride="carousel">
  <div class="carousel-inner d-flex">
    {% for post in site.posts limit: 10 %}
    <div class="carousel-item {% if forloop.first %}active{% endif %}">
      <div class="neural-card-3d d-flex flex-column align-items-center text-center">
        <a href="{{ post.url | relative_url }}">
          {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
          <img src="{{ image_path | relative_url }}" class="carousel-image img-fluid" alt="{{ post.title | escape }}" loading="lazy">
        </a>
        <div class="carousel-caption mt-auto w-100">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
          <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
          <p>{{ post.content | strip_html | truncate: 100, "..." }}</p>
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

{% if site.posts.size == 0 %}
<p>Пока нет статей.</p>
{% endif %}

<script>
document.addEventListener("DOMContentLoaded", () => {
  const carouselEl = document.querySelector("#articlesCarousel");
  if (!carouselEl) return;

  const carousel = new bootstrap.Carousel(carouselEl, {
    interval: 4000,
    ride: 'carousel',
    wrap: true,
  });

  // Делаем карусель мульти-карточной
  const items = carouselEl.querySelectorAll(".carousel-item");
  items.forEach((el) => {
    const next = el.nextElementSibling || items[0];
    const cloneChild = next.querySelector(".neural-card-3d").cloneNode(true);
    el.appendChild(cloneChild);
  });
});
</script>
