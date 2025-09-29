---
layout: default
title: Статьи
description: Последние статьи по искусственному интеллекту.
---

<h1>Все статьи</h1>

<div id="articlesCarousel" class="carousel slide" data-bs-ride="carousel" data-bs-interval="5000">
  <div class="carousel-inner">
    {% for post in site.posts %}
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
