---
layout: default
title: Статьи
description: Последние обзоры и уроки по искусственному интеллекту.
---

<h1>Все статьи</h1>

<div class="articles-wrapper">
  <div class="carousel-container">
    {% assign posts_per_slide = 3 %}
    {% assign slide_index = 0 %}
    {% assign total_posts = site.posts | size %}

    {% for post in site.posts %}
      {% assign remainder = forloop.index0 | modulo: posts_per_slide %}
      
      {% if remainder == 0 %}
        {% if forloop.index0 != 0 %}
          </div>
        {% endif %}
        <div class="carousel-slide">
      {% endif %}
      
      <div class="neural-card-3d text-center">
        <a href="{{ post.url | relative_url }}">
          {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
          <img src="{{ image_path | relative_url }}" class="carousel-image img-fluid" alt="{{ post.title | escape }}" loading="lazy">
        </a>
        <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
        <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
        <p>{{ post.content | strip_html | truncate: 100, "..." }}</p>
      </div>

      {% if forloop.last %}
        </div>
      {% endif %}
    {% endfor %}
  </div>

  <div class="carousel-controls">
    <button class="carousel-prev">Предыдущий</button>
    <button class="carousel-next">Следующий</button>
  </div>
</div>

{% if site.posts.size == 0 %}
<p>Пока нет статей.</p>
{% endif %}

<script>
document.addEventListener('DOMContentLoaded', function() {
  const slides = document.querySelectorAll('.carousel-slide');
  const prevBtn = document.querySelector('.carousel-prev');
  const nextBtn = document.querySelector('.carousel-next');
  let currentSlide = 0;

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.style.display = i === index ? 'flex' : 'none';
    });
  }

  prevBtn.addEventListener('click', function() {
    currentSlide = (currentSlide - 1 + slides.length) % slides.length;
    showSlide(currentSlide);
  });

  nextBtn.addEventListener('click', function() {
    currentSlide = (currentSlide + 1) % slides.length;
    showSlide(currentSlide);
  });

  showSlide(currentSlide);
});
</script>
