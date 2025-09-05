---
title: "Галерея"
---

Все изображения из сгенерированных статей:

{{ range (where .Site.RegularPages "Section" "posts") }}
![{{ .Title }}]({{ .Params.image }})
{{ end }}
