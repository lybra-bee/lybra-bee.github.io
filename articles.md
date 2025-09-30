---
layout: default
title: Статьи
description: Последние обзоры и уроки по искусственному интеллекту.
---
<div class="container">
  <h1 class="text-center mb-4">Все статьи</h1>
  
  {% if site.posts.size > 0 %}
  <!-- Карусель статей -->
  <div class="row justify-content-center mb-5">
    <div class="col-12">
      <div id="articlesCarousel" class="carousel slide" data-bs-ride="carousel" data-bs-interval="5000">
        <!-- Индикаторы -->
        <div class="carousel-indicators">
          {% for post in site.posts limit: 5 %}
          <button type="button" data-bs-target="#articlesCarousel" data-bs-slide-to="{{ forloop.index0 }}" 
                  class="{% if forloop.first %}active{% endif %}" 
                  aria-label="Слайд {{ forloop.index }}"></button>
          {% endfor %}
        </div>
        
        <!-- Слайды -->
        <div class="carousel-inner">
          {% for post in site.posts limit: 5 %}
          <div class="carousel-item {% if forloop.first %}active{% endif %}">
            <div class="neural-card-3d">
              {% if post.image %}
                <a href="{{ post.url | relative_url }}">
                  <img src="{{ post.image | relative_url }}" class="carousel-image" 
                       alt="{{ post.title | escape }}" loading="lazy">
                </a>
              {% else %}
                <a href="{{ post.url | relative_url }}">
                  <img src="/assets/images/posts/placeholder.png" class="carousel-image" 
                       alt="{{ post.title | escape }}" loading="lazy">
                </a>
              {% endif %}
              <div class="carousel-caption">
                <h3><a href="{{ post.url | relative_url }}" class="text-decoration-none">{{ post.title | escape }}</a></h3>
                <p class="post-date">{{ post.date | date: "%d.%m.%Y" }}</p>
                <p class="excerpt">{{ post.excerpt | default: post.content | strip_html | truncate: 120 }}</p>
                <a href="{{ post.url | relative_url }}" class="btn btn-outline-light btn-sm mt-2">Читать далее</a>
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
        
        <!-- Кнопки управления -->
        <button class="carousel-control-prev" type="button" data-bs-target="#articlesCarousel" data-bs-slide="prev">
          <span class="carousel-control-prev-icon" aria-hidden="true"></span>
          <span class="visually-hidden">Предыдущий</span>
        </button>
        <button class="carousel-control-next" type="button" data-bs-target="#articlesCarousel" data-bs-slide="next">
          <span class="carousel-control-next-icon" aria-hidden="true"></span>
          <span class="visually-hidden">Следующий</span>
        </button>
      </div>
    </div>
  </div>
  
  <!-- Список всех статей -->
  <div class="all-articles mt-5">
    <h2 class="text-center mb-4">Все статьи</h2>
    <div class="row">
      {% for post in site.posts %}
      <div class="col-md-6 col-lg-4 mb-4">
        <div class="neural-card-3d h-100 d-flex flex-column">
          {% if post.image %}
            <a href="{{ post.url | relative_url }}" class="mb-3">
              <img src="{{ post.image | relative_url }}" class="img-fluid rounded article-thumbnail" 
                   alt="{{ post.title | escape }}" loading="lazy">
            </a>
          {% else %}
            <a href="{{ post.url | relative_url }}" class="mb-3">
              <img src="/assets/images/posts/placeholder.png" class="img-fluid rounded article-thumbnail" 
                   alt="{{ post.title | escape }}" loading="lazy">
            </a>
          {% endif %}
          <div class="card-content flex-grow-1 d-flex flex-column">
            <h4 class="h5"><a href="{{ post.url | relative_url }}" class="text-decoration-none article-title">{{ post.title | escape }}</a></h4>
            <p class="post-date small text-muted mb-2">{{ post.date | date: "%d.%m.%Y" }}</p>
            <p class="excerpt flex-grow-1">{{ post.excerpt | default: post.content | strip_html | truncate: 100 }}</p>
            <div class="mt-auto">
              <a href="{{ post.url | relative_url }}" class="btn btn-outline-light btn-sm">Читать статью</a>
            </div>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
  
  {% else %}
  <!-- Сообщение, если статей нет -->
  <div class="row justify-content-center">
    <div class="col-md-8">
      <div class="neural-card-3d text-center">
        <h3>Пока нет статей</h3>
        <p>Скоро здесь появятся интересные материалы об искусственном интеллекте и технологиях!</p>
        <div class="mt-4">
          <span style="font-size: 3rem;">🐝</span>
        </div>
      </div>
    </div>
  </div>
  {% endif %}
</div>
