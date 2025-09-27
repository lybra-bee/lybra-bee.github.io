---
layout: default
title: Статьи
---
<h1>Все статьи</h1>

{% if site.posts.size > 0 %}
<!-- Карусель статей (динамическая, привязана к постам) -->
<div id="articlesCarousel" class="carousel slide mb-5" data-bs-ride="carousel">
  <div class="carousel-inner">
    {% for post in site.posts limit: 10 %}
    <div class="carousel-item {% if forloop.first %}active{% endif %}">
      <div class="neural-card">
        <a href="{{ post.url | relative_url }}">
          <!-- Отладка пути изображения -->
          {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
          {% if image_path contains '.png' or image_path contains '.jpg' %}
            {% if site.static_files | where: "path", image_path | size > 0 %}
              <img src="{{ image_path | relative_url }}" class="carousel-image" alt="{{ post.title | escape }}" loading="lazy">
            {% else %}
              <img src="/assets/images/posts/placeholder.png" class="carousel-image" alt="Изображение не найдено для {{ post.title | escape }}" loading="lazy">
            {% endif %}
          {% else %}
            <img src="/assets/images/posts/placeholder.png" class="carousel-image" alt="Неверный формат пути для {{ post.title | escape }}" loading="lazy">
          {% endif %}
        </a>
        <div class="carousel-caption d-block">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
          <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
          <p>{{ post.content | strip_html | truncate: 100, "..." }}</p>
        </div>
      </div>
    </div>
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
{% else %}
<p>Пока нет статей.</p>
{% endif %}

<!-- Список всех статей (с пагинацией) -->
{% if paginator.posts.size > 0 %}
  {% for post in paginator.posts %}
  <div class="card neural-card">
    <a href="{{ post.url | relative_url }}">
      <!-- Отладка пути изображения -->
      {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
      {% if image_path contains '.png' or image_path contains '.jpg' %}
        {% if site.static_files | where: "path", image_path | size > 0 %}
          <img src="{{ image_path | relative_url }}" alt="{{ post.title | escape }}" loading="lazy">
        {% else %}
          <img src="/assets/images/posts/placeholder.png" alt="Изображение не найдено для {{ post.title | escape }}" loading="lazy">
        {% endif %}
      {% else %}
        <img src="/assets/images/posts/placeholder.png" alt="Неверный формат пути для {{ post.title | escape }}" loading="lazy">
      {% endif %}
    </a>
    <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
    <p>{{ post.date | date: "%B %d, %Y" }}</p>
    <p>{{ post.excerpt | strip_html | truncate: 150, "..." }}</p>
  </div>
  {% endfor %}
{% else %}
  <p>Пока нет статей.</p>
{% endif %}

{% if paginator.total_pages > 1 %}
<ul class="pagination">
  {% if paginator.previous_page %}
  <li><a href="{{ paginator.previous_page_path | relative_url }}">Предыдущая</a></li>
  {% endif %}
  {% for page in (1..paginator.total_pages) %}
  <li {% if page == paginator.page %}class="active"{% endif %}>
    <a href="{{ '/articles/page' | append: page | relative_url }}">{{ page }}</a>
  </li>
  {% endfor %}
  {% if paginator.next_page %}
  <li><a href="{{ paginator.next_page_path | relative_url }}">Следующая</a></li>
  {% endif %}
</ul>
{% endif %}
