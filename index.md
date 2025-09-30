---
layout: default
title: Главная
description: Добро пожаловать в мой блог об искусственном интеллекте.
dark_mode: false
---
<main>
  <section class="welcome-section">
    <h2 class="spread-text">
      <span>Д</span><span>о</span><span>б</span><span>р</span><span>о</span>
      <span> </span><span>п</span><span>о</span><span>ж</span><span>а</span><span>л</span><span>о</span><span>в</span><span>а</span><span>т</span><span>ь</span>
      <span> </span><span>в</span><span> </span><span>м</span><span>о</span><span>й</span>
      <span> </span><span>б</span><span>л</span><span>о</span><span>г</span>
    </h2>
  </section>
  {% if site.posts.size > 0 %}
    <div class="latest-post">
      {% assign latest_post = site.posts.first %}
     
      <div class="neural-card-3d main-page-card">
        <div class="card-image-container">
          <a href="{{ latest_post.url | relative_url }}">
            <img src="{{ latest_post.image | default: '/assets/images/posts/placeholder.png' | relative_url }}" alt="{{ latest_post.title | escape }}" class="main-page-image">
          </a>
        </div>
        <div class="card-content-container">
          <h3><a href="{{ latest_post.url | relative_url }}">{{ latest_post.title | escape }}</a></h3>
          <p class="post-date">{{ latest_post.date | date: "%B %d, %Y" }}</p>
          <p class="card-excerpt">{{ latest_post.content | strip_html | truncate: 100, "..." }}</p>
          <a href="{{ latest_post.url | relative_url }}" class="btn btn-outline-light">Читать далее</a>
        </div>
      </div>
    </div>
  {% endif %}
</main>
