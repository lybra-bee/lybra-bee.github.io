---
layout: default
title: Lybra AI
description: Блог о гибридном ИИ и IoT 2025 года
header_image: /assets/images/bg.png
---

<section class="welcome-section">
  <h2 class="spread-text">
    <span>Д</span><span>о</span><span>б</span><span>р</span><span>о</span>
    <span> </span><span>п</span><span>о</span><span>ж</span><span>а</span><span>л</span><span>о</span><span>в</span><span>а</span><span>т</span><span>ь</span>
    <span> </span><span>в</span>
    <span> </span><span>м</span><span>о</span><span>й</span>
    <span> </span><span>б</span><span>л</span><span>о</span><span>г</span>
  </h2>
</section>

<section class="latest-post container my-4">
  {% for post in site.posts limit:1 %}
  <div class="card glass-card">
    <div class="card-body">
      <h3 class="card-title"><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
      <p class="card-text">{{ post.excerpt | strip_html | truncate: 150 }}</p>
      <a href="{{ post.url | relative_url }}" class="btn btn-outline-light">Читать далее</a>
    </div>
  </div>
  {% endfor %}
</section>

<section class="seo-text container my-4">
  <h2>О блоге Lybra AI</h2>
  <p>Добро пожаловать в Lybra AI — блог о гибридном искусственном интеллекте и Интернете вещей (IoT) 2025 года. Здесь вы найдете статьи о локальном ИИ, машинном обучении, нейросетях, Stable Diffusion, LLM и экспериментах на слабом железе. Мы делимся практическими решениями и инновациями в области ИИ и IoT.</p>
</section>
