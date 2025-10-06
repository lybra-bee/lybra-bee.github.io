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

<aside class="container my-4">
  <h3>Последние статьи</h3>
  {% for post in site.posts limit:3 %}
    <article>
      <h4><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h4>
      <p>{{ post.excerpt | strip_html | truncate: 100 }}</p>
    </article>
  {% endfor %}
</aside>
