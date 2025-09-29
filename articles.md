---
layout: default
title: Статьи
description: Последние обзоры и уроки по искусственному интеллекту.
---

<h1>Все статьи</h1>

<div id="articlesCarousel" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-inner">
    {% assign posts_per_slide = 3 %}
    {% for i in (0..site.posts.size-1) %}
      {% if forloop.index0 modulo posts_per_slide == 0 %}
      <div class="carousel-item {% if forloop.first %}active{% endif %}">
        <div class="d-flex justify-content-center gap-3">
      {% endif %}

      <div class="neural-card-3d d-flex flex-column align-items-center text-center">
        <a href="{{ site.posts[i].url | relative_url }}">
          {% assign image_path = site.posts[i].image | default: '/assets/images/posts/placeholder.png' %}
          <img src="{{ image_path | relative_url }}" class="carousel-image img-fluid" alt="{{ site.posts[i].title | escape }}">
        </a>
        <div class="carousel-caption mt-auto w-100">
          <h3><a href="{{ site.posts[i].url | relative_url }}">{{ site.posts[i].title | escape }}</a></h3>
          <p class="post-date">{{ site.posts[i].date | date: "%B %d, %Y" }}</p>
          <p>{{ site.posts[i].content | strip_html | truncate: 100, "..." }}</p>
        </div>
      </div>

      {% if forloop.index0 modulo posts_per_slide == posts_per_slide-1 or forloop.last %}
        </div>
      </div>
      {% endif %}
    {% endfor %}
  </div>

  <button class="carousel-control-prev" type="button" data-bs-target="#articlesCarousel" data-bs-slide="prev">
    <span class="carousel-control-prev-icon"></span>
    <span class="visually-hidden">Предыдущий</span>
  </button>
  <button class="carousel-control-next" type="button" data-bs-target="#articlesCarousel" data-bs-slide="next">
    <span class="carousel-control-next-icon"></span>
    <span class="visually-hidden">Следующий</span>
  </button>
</div>

{% if site.posts.size == 0 %}
<p>Пока нет статей.</p>
{% endif %}
