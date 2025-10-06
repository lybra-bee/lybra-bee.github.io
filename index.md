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
      <p class="card-excerpt">{{ latest_post.content | strip_html | truncate: 150, "..." }}</p>
      <a href="{{ latest_post.url | relative_url }}" class="btn btn-outline-light">Читать далее</a>
    </div>
  </div>
</div>

<section class="seo-text">
  <h2>О блоге Lybra AI</h2>
  <p>Добро пожаловать в Lybra AI — блог о гибридном искусственном интеллекте и Интернете вещей (IoT) 2025 года. Здесь вы найдете статьи о локальном ИИ, машинном обучении, нейросетях, Stable Diffusion, LLM и экспериментах на слабом железе. Мы делимся практическими решениями и инновациями в области ИИ и IoT.</p>
  <p>В 2025 году гибридный ИИ становится ключевым трендом, сочетающим локальные и облачные вычисления для повышения эффективности. Edge-вычисления позволяют обрабатывать данные ближе к источнику, снижая задержки и энергозатраты. Мои эксперименты в <a href="https://lybra-bee.github.io/lybra-ai-lab/">Lybra AI Lab</a> показывают, как запускать Stable Diffusion на P102-100 за 12 секунд, делая ИИ доступным для всех. Читайте наши статьи, чтобы узнать, как ИИ меняет мир IoT, от умных городов до автономных систем.</p>
  <p>Мы анализируем тренды 2025, такие как Agentic AI, RAG и Sovereign AI, и предоставляем практические уроки для их применения. Подписывайтесь, чтобы быть в курсе!</p>
</section>
