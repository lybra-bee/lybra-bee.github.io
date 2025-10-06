---
layout: default
title: Статьи об ИИ и IoT
description: Все статьи о гибридном ИИ, IoT и edge-вычислениях 2025 года. Читайте обзоры и эксперименты из Lybra AI Lab.
---

<div class="container py-4">
    <h1 class="text-center mb-2">Статьи об ИИ и IoT</h1>
    <p class="text-center mb-5">Последние обзоры, уроки и эксперименты по искусственному интеллекту и IoT. Смотрите мои исследования в <a href="https://lybra-bee.github.io/lybra-ai-lab/">Lybra AI Lab</a>.</p>

    {% if site.posts.size > 0 %}
    <!-- Карусель -->
    <div id="articlesCarousel" class="carousel slide mb-5" data-bs-ride="carousel" data-bs-interval="5000">
        <div class="carousel-indicators">
            {% for post in site.posts limit: 5 %}
            <button type="button" data-bs-target="#articlesCarousel" data-bs-slide-to="{{ forloop.index0 }}" 
                    class="{% if forloop.first %}active{% endif %}" 
                    aria-label="Слайд {{ forloop.index }}"></button>
            {% endfor %}
        </div>
        <div class="carousel-inner rounded-3">
            {% for post in site.posts limit: 5 %}
            <div class="carousel-item {% if forloop.first %}active{% endif %}">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-md-10 col-lg-8">
                            <div class="neural-card-3d p-4">
                                <div class="row align-items-center">
                                    {% if post.image %}
                                    <div class="col-md-5 mb-3 mb-md-0">
                                        <a href="{{ post.url | relative_url }}">
                                            <img src="{{ post.image | relative_url }}" class="img-fluid rounded carousel-image" 
                                                 alt="{{ post.image_alt | default: post.title | escape }}" loading="lazy">
                                        </a>
                                    </div>
                                    {% endif %}
                                    <div class="{% if post.image %}col-md-7{% else %}col-12{% endif %}">
                                        <div class="carousel-caption-content text-start">
                                            <h3 class="h4"><a href="{{ post.url | relative_url }}" class="text-decoration-none text-light">{{ post.title | escape }}</a></h3>
                                            <p class="post-date text-muted mb-2">{{ post.date | date: "%d.%m.%Y" }}</p>
                                            <p class="excerpt mb-3">{{ post.excerpt | default: post.content | strip_html | truncate: 150 }}</p>
                                            <a href="{{ post.url | relative_url }}" class="btn btn-outline-light btn-sm">Читать далее</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
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

    <!-- Полный список статей -->
    <div class="all-posts">
        <h2>Все статьи</h2>
        <ul class="post-list">
            {% for post in site.posts %}
            <li>
                <a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a> — {{ post.date | date: "%d.%m.%Y" }}
            </li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
</div>
