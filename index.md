---
layout: default
title: Главная
description: Добро пожаловать в мой блог об искусственном интеллекте.
dark_mode: false
---
<main>
  <section class="welcome-section">
    <h2 class="spread-text">Добро пожаловать в мой блог</h2>
  </section>
  {% if site.posts.size > 0 %}
    <div class="latest-post">
      {% assign latest_post = site.posts.first %}
      <h2>Последняя статья</h2>
      <div class="neural-card-3d d-flex flex-column align-items-center text-center">
        <a href="{{ latest_post.url | relative_url }}">
          <img src="{{ latest_post.image | default: '/assets/images/posts/placeholder.png' | relative_url }}" alt="{{ latest_post.title | escape }}" class="carousel-image img-fluid">
        </a>
        <div class="carousel-caption mt-auto w-100">
          <h3><a href="{{ latest_post.url | relative_url }}" style="color: #e0f7fa;">{{ latest_post.title | escape }}</a></h3>
          <p class="post-date">{{ latest_post.date | date: "%B %d, %Y" }}</p>
          <p>{{ latest_post.content | strip_html | truncate: 100, "..." }}</p>
        </div>
      </div>
    </div>
  {% endif %}
</main>
