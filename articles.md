<h1>Все статьи</h1>

<div class="carousel-3d">
  <div class="carousel-3d-track">
    {% for post in site.posts limit: 10 %}
    <div class="carousel-3d-item">
      <a href="{{ post.url | relative_url }}">
        {% assign image_path = post.image | default: '/assets/images/posts/placeholder.png' %}
        <img src="{{ image_path | relative_url }}" alt="{{ post.title | escape }}" loading="lazy">
      </a>
      <div class="carousel-caption mt-auto text-center">
        <h3><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h3>
        <p class="post-date">{{ post.date | date: "%B %d, %Y" }}</p>
        <p>{{ post.content | strip_html | truncate: 100, "..." }}</p>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="carousel-3d-controls">
    <button class="prev">&lt;</button>
    <button class="next">&gt;</button>
  </div>
</div>
{% if site.posts.size == 0 %}
<p>Пока нет статей.</p>
{% endif %}
