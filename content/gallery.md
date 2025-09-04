---
title: "Галерея"
date: 2024-01-01
draft: false
---

## 🎨 Галерея AI-генераций

Изображения, созданные искусственным интеллектом для статей:

<div class="gallery">
{{ range where .Site.RegularPages "Type" "posts" }}
    {{ if .Params.image }}
    <div class="gallery-item">
        <a href="{{ .Permalink }}">
            <img src="{{ .Params.image }}" alt="{{ .Title }}">
            <p>{{ .Title }}</p>
        </a>
    </div>
    {{ end }}
{{ end }}
</div>
