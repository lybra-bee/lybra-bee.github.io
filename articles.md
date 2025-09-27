---
layout: default
title: Статьи
---
<h1>Все статьи</h1>

{% if site.posts.size > 0 %}
<!-- Карусель статей -->
<div id="articlesCarousel" class="carousel slide mb-5" data-bs-ride="carousel">
  <div class="carousel-inner">
    {% for post in site.posts %}
    <div class="carousel-item {% if forloop.first %}active{% endif %}">
      <div class="neural-card">
        <a href="{{ post.url | relative_url }}">
          <img src="{{ post.image | relative_url | default: '/assets/images/posts/placeholder.png' }}" class="carousel-image" alt="{{ post.title | escape }}" loading="lazy">
        </a>
        <div class="carousel-caption d-block">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
          <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
          <p>{{ post.excerpt | strip_html | truncate: 100, "..." }}</p>
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

<!-- Список всех статей -->
{% if paginator.posts.size > 0 %}
  {% for post in paginator.posts %}
  <div class="card neural-card">
    <a href="{{ post.url | relative_url }}">
      <img src="{{ post.image | relative_url | default: '/assets/images/posts/placeholder.png' }}" alt="{{ post.title | escape }}" loading="lazy">
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
