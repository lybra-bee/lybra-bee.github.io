---
layout: default
title: Статьи
---
<h1>Все статьи</h1>
{% for post in paginator.posts %}
<div class="card neural-card">
  <img src="{{ post.image }}" alt="{{ post.title }}" loading="lazy">
  <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
  <p>{{ post.date | date: "%B %d, %Y" }}</p>
  <p>{{ post.excerpt }}</p>
</div>
{% endfor %}

{% if paginator.total_pages > 1 %}
<ul class="pagination">
  {% if paginator.previous_page %}
  <li><a href="{{ paginator.previous_page_path }}">Предыдущая</a></li>
  {% endif %}
  {% for page in (1..paginator.total_pages) %}
  <li {% if page == paginator.page %}class="active"{% endif %}>
    <a href="{{ '/articles/page' | append: page }}">{{ page }}</a>
  </li>
  {% endfor %}
  {% if paginator.next_page %}
  <li><a href="{{ paginator.next_page_path }}">Следующая</a></li>
  {% endif %}
</ul>
{% endif %}
