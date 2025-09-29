---
layout: default
title: Статьи
description: Последние статьи по искусственному интеллекту.
---

<h1>Все статьи</h1>

<div id="articlesCarousel" class="carousel slide mb-5" data-bs-ride="carousel">
  <div class="carousel-inner">
    {% assign posts_array = site.posts | reverse %}
    {% assign total_posts = posts_array | size %}

    {% assign i = 0 %}
    {% while i < total_posts %}
      <div class="carousel-item {% if i == 0 %}active{% endif %}">
        <div class="carousel-slide d-flex justify-content-center gap-4">
          {% assign j = 0 %}
          {% while j < 3 %}
            {% assign post = posts_array[i | plus: j] %}
            {% if post %}
              <div class="neural-card-3d text-center">
                <a href="{{ post.url | relative_url }}">
                  {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
                  <img src="{{ image_path | relative_url }}" class="carousel-image img-fluid" alt="{{ post.title }}" loading="lazy">
                </a>
                <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
                <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
                <p>{{ post.content | strip_html | truncate: 100, "..." }}</p>
              </div>
            {% endif %}
            {% assign j = j | plus: 1 %}
          {% endwhile %}
        </div>
      </div>
      {% assign i = i | plus: 3 %}
    {% endwhile %}
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
