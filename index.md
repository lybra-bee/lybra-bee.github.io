---
layout: default
title: Главная
description: Добро пожаловать в мой блог об искусственном интеллекте.
dark_mode: false
---
<main>
  <section class="welcome-section">
    <h2 class="marquee">Добро пожаловать в мой блог</h2>
  </section>
  <!-- Дополнительный контент, если нужен -->
  {% if site.posts.size > 0 %}
    <div class="latest-post">
      {% assign latest_post = site.posts.first %}
      <h2>Последняя статья</h2>
      <a href="{{ latest_post.url | relative_url }}">
        <img src="{{ latest_post.image | default: '/assets/images/posts/placeholder.png' | relative_url }}" alt="{{ latest_post.title | escape }}" class="img-fluid">
        <h3>{{ latest_post.title | escape }}</h3>
        <p>{{ latest_post.content | strip_html | truncate: 100, "..." }}</p>
      </a>
    </div>
  {% endif %}
</main>
