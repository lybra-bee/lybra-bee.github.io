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

  <!-- ДОБАВЬТЕ БЛОК ПРО ЛАБОРАТОРИЮ ЗДЕСЬ - после welcome-section и перед latest-post -->
  <div class="lab-promo neural-card-3d" style="background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #2196f3;">
    <h3>🔬 Моя AI-лаборатория</h3>
    <p>Пока блог работает автоматически, в лаборатории я вручную ставлю эксперименты с нейросетями на бюджетном железе:</p>
    <ul>
      <li>✅ Установка и настройка AI-моделей</li>
      <li>🖼️ Генерация изображений на P102-100</li>
      <li>🎥 Скоро: генерация видео (в разработке)</li>
      <li>📊 Реальные тесты производительности</li>
    </ul>
    <a href="https://lybra-bee.github.io/lybra-ai-lab/" class="btn btn-primary">Посмотреть эксперименты</a>
  </div>

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
