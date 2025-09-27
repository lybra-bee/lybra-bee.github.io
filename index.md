---
layout: default
title: Главная
---
<div class="hero" style="background-image: url(/assets/images/header-banner.png);">
  <h1>Добро пожаловать в Мой AI Блог</h1>
  <p>Ежедневные статьи об ИИ и технологиях.</p>
</div>

{% if site.posts.size > 0 %}
  {% assign latest_post = site.posts | sort: 'date' | reverse | first %}
  <h2>Последняя статья</h2>
  <div class="card neural-card">
    <a href="{{ latest_post.url | relative_url }}">
      {% assign image_path = latest_post.image | default: '/assets/images/posts/placeholder.png' %}
      <img src="{{ image_path | relative_url }}" alt="{{ latest_post.title | escape }}" loading="lazy">
    </a>
    <h3><a href="{{ latest_post.url | relative_url }}">{{ latest_post.title | escape }}</a></h3>
    <p>{{ latest_post.date | date: "%B %d, %Y" }}</p>
    {{ latest_post.content | strip_html | truncate: 500 }}
    <a href="{{ latest_post.url | relative_url }}">Читать полностью</a>
  </div>
{% else %}
  <p>Пока нет статей.</p>
{% endif %}
