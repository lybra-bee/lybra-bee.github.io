---
layout: default
title: Главная
---
<div class="hero" style="background-image: url(/assets/images/header-banner.jpg);">
  <h1>Добро пожаловать в Мой AI Блог</h1>
  <p>Ежедневные статьи об ИИ и технологиях.</p>
</div>

<h2>Последняя статья</h2>
{% assign latest = site.posts | first %}
<div class="card neural-card">
  <img src="{{ latest.image }}" alt="{{ latest.title }}" loading="lazy">
  <h3>{{ latest.title }}</h3>
  <p>{{ latest.date | date: "%B %d, %Y" }}</p>
  {{ latest.content | truncate: 500 }}
  <a href="{{ latest.url }}">Читать полностью</a>
</div>
