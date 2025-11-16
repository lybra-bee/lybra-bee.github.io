---
title: "Все уроки"
layout: default
---
<h1>Список уроков</h1>
<ul>
  {% assign sorted_lessons = site.lessons | sort: 'title' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url }}">{{ lesson.title }}</a>
    </li>
  {% endfor %}
</ul>
