---
layout: default
title: Статьи
description: Последние статьи по искусственному интеллекту.
---

<h1>Все статьи</h1>

<div id="articlesCarousel" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-inner">
    {% assign posts_array = site.posts | reverse %}
    {% assign slide_index = 0 %}

    {% for post in posts_array %}
      {% if forloop.index0 == 0 or forloop.index0 modulo 3 == 0 %}
        <div class="carousel-item {% if forloop.index0 == 0 %}active{% endif %}">
          <div class="carousel-slide d-flex justify-content-center gap-4">
      {% endif %}

      <div class="neural-card-3d text-center">
        <a href="{{ post.url | relative_url }}">
          {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
          <img src="{{ image_path | relative_url }}" class="carousel-image img-fluid" alt="{{ post.title }}" loading="lazy">
        </a>
        <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
        <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
        <p>{{ post.content | strip_html | truncate: 100, "..." }}</p>
      </div>

      {% if forloop.index0 != 0 and forloop.index0 modulo 3 == 2 or forloop.last %}
          </div>
        </div>
      {% endif %}
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
