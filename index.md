---
layout: default
title: Главная
---

<h1>Последняя статья</h1>

{% if site.posts.size > 0 %}
  {% assign latest_post = site.posts | sort: 'date' | reverse | first %}
  <div class="latest-post">
    <h2><a href="{{ latest_post.url | relative_url }}">{{ latest_post.title | escape }}</a></h2>
    <p class="post-date">{{ latest_post.date | date: "%B %d, %Y" }}</p>
    <!-- Изображение -->
    {% assign image_path = latest_post.image | default: '/assets/images/posts/placeholder.png' %}
    {% if image_path contains '.png' or image_path contains '.jpg' %}
      {% if site.static_files | where: "path", image_path | size > 0 %}
        <img src="{{ image_path | relative_url }}" alt="{{ latest_post.title | escape }}" loading="lazy">
      {% else %}
        <img src="/assets/images/posts/placeholder.png" alt="Изображение не найдено для {{ latest_post.title | escape }}" loading="lazy">
      {% endif %}
    {% else %}
      <img src="/assets/images/posts/placeholder.png" alt="Неверный формат пути для {{ latest_post.title | escape }}" loading="lazy">
    {% endif %}
    <p>{{ latest_post.content | strip_html | truncate: 150, "..." }}</p>
    <a href="{{ latest_post.url | relative_url }}">Читать полностью</a>
{% else %}
  <p>Пока нет статей.</p>
{% endif %}

<h2>Все статьи</h2>
<a href="/articles">Перейти к списку статей</a>
