---
title: "Галерея"
date: 2024-01-01
draft: false
---

## 🎨 Галерея AI-изображений

Изображения, сгенерированные искусственным интеллектом:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin: 2rem 0;">
{{ range where .Site.RegularPages "Type" "posts" }}
    {{ if .Params.image }}
    <div style="background: rgba(15,23,42,0.6); padding: 1rem; border-radius: 12px; text-align: center;">
        <img src="{{ .Params.image }}" alt="{{ .Title }}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 8px;">
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">{{ .Title }}</p>
    </div>
    {{ end }}
{{ end }}
</div>
