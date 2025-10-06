---
layout: default
title: "Lybra AI: Блог об ИИ и IoT"
description: "Блог о гибридном ИИ, IoT и edge-вычислениях 2025 года. Читайте статьи и эксперименты в Lybra AI Lab."
dark_mode: false
---

<main>
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

<!-- Остальной контент главной страницы -->
    <p>Добро пожаловать в мой блог! Здесь я делюсь трендами гибридного ИИ и IoT 2025 года. Мои статьи и эксперименты раскрывают, как искусственный интеллект трансформирует технологии: от edge-вычислений до применения ИИ на бюджетном оборудовании, таком как P102-100. Читайте мои исследования, следите за экспериментами в <a href="https://lybra-bee.github.io/lybra-ai-lab/">Lybra AI Lab</a> и узнавайте, как ИИ меняет мир.</p>
    <p>В 2025 году гибридный ИИ в IoT становится ключевым трендом. Edge-вычисления позволяют обрабатывать данные локально, снижая задержки и повышая безопасность. Моя лаборатория тестирует Stable Diffusion, LLaMA и другие модели на доступном оборудовании, чтобы показать, как ИИ доступен каждому. Подписывайтесь, чтобы не пропустить новые статьи и эксперименты!</p>
  </section>

  {% if site.posts.size > 0 %}
  <div class="latest-post">
    {% assign latest_post = site.posts.first %}
    <div class="neural-card-3d main-page-card">
      <div class="card-image-container">
        <a href="{{ latest_post.url | relative_url }}">
          <img src="{{ latest_post.image | default: '/assets/images/posts/placeholder.png' | relative_url }}" alt="Гибридный ИИ 2025: {{ latest_post.title | escape }}" class="main-page-image" loading="lazy">
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
  {% endif %}

  <section class="about-section">
    <h2>О блоге</h2>
    <p>Lybra AI — это пространство для энтузиастов ИИ и IoT. Я анализирую тренды 2025 года, провожу эксперименты в <a href="https://lybra-bee.github.io/lybra-ai-lab/">Lybra AI Lab</a> и делюсь практическими кейсами. Хотите узнать, как запустить Stable Diffusion на P102-100 за 12 секунд? Или как edge AI меняет IoT? Читайте мои статьи и подписывайтесь!</p>
    <a href="/articles" class="btn btn-outline-light">Все статьи</a>
  </section>
</main>
