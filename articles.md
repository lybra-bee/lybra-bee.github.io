---
layout: default
title: Статьи
---
<h1>Все статьи</h1>
{% if site.posts.size > 0 %}
  {% for post in site.posts %}
  <div class="card neural-card">
    <img src="{{ post.image | relative_url }}" alt="{{ post.title }}" loading="lazy">
    <h3><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
    <p>{{ post.date | date: "%B %d, %Y" }}</p>
    <p>{{ post.excerpt }}</p>
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
