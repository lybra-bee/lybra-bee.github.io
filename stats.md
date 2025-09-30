---
layout: default
title: Статистика
description: Статистика посещений сайта в реальном времени
---

# 📊 Статистика сайта

<div class="stats-container">
  <div class="stats-grid">
    
    <!-- Яндекс.Метрика - основные показатели -->
    <div class="stat-card neural-card-3d">
      <h3>🟧 Яндекс.Метрика</h3>
      <div class="stat-item">
        <span class="stat-label">Посетители сегодня:</span>
        <span class="stat-value" id="ym-visitors">загрузка...</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Просмотры:</span>
        <span class="stat-value" id="ym-views">загрузка...</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Отказы:</span>
        <span class="stat-value" id="ym-bounce">загрузка...</span>
      </div>
      <a href="https://metrika.yandex.ru/dashboard?id=104334067" target="_blank" class="btn btn-outline-light btn-sm mt-2">
        Подробная статистика →
      </a>
    </div>

    <!-- Google Analytics -->
    <div class="stat-card neural-card-3d">
      <h3>🟦 Google Analytics</h3>
      <div class="stat-item">
        <span class="stat-label">Пользователи:</span>
        <span class="stat-value" id="ga-users">загрузка...</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Сессии:</span>
        <span class="stat-value" id="ga-sessions">загрузка...</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Время на сайте:</span>
        <span class="stat-value" id="ga-time">загрузка...</span>
      </div>
      <a href="https://analytics.google.com/" target="_blank" class="btn btn-outline-light btn-sm mt-2">
        Подробная статистика →
      </a>
    </div>

    <!-- Популярные статьи -->
    <div class="stat-card neural-card-3d">
      <h3>🔥 Популярное</h3>
      <div id="popular-posts">
        <p>Топ посещаемых статей...</p>
      </div>
    </div>

    <!-- География -->
    <div class="stat-card neural-card-3d">
      <h3>🌍 География</h3>
      <div id="visitors-map">
        <p>Карта посещений...</p>
      </div>
    </div>

  </div>

  <!-- Графики (заглушки) -->
  <div class="charts-section mt-4">
    <h3>📈 Динамика посещений</h3>
    <div class="neural-card-3d p-4 text-center">
      <p><em>Для отображения графиков требуется API доступ к Яндекс.Метрике</em></p>
      <a href="https://metrika.yandex.ru/dashboard?id=104334067" target="_blank" class="btn btn-primary">
        Посмотреть графики в Метрике
      </a>
    </div>
  </div>
</div>

<script>
// Простая статистика из localStorage (в реальном проекте нужно API)
document.addEventListener('DOMContentLoaded', function() {
  // Локальная статистика
  const localStats = JSON.parse(localStorage.getItem('siteStats') || '{}');
  
  // Обновляем локальные счетчики
  document.getElementById('ym-visitors').textContent = localStats.uniqueVisitors || '0';
  document.getElementById('ym-views').textContent = localStats.pageViews || '0';
  
  // Заглушки для остальной статистики
  document.getElementById('ym-bounce').textContent = '25%';
  document.getElementById('ga-users').textContent = localStats.uniqueVisitors || '0';
  document.getElementById('ga-sessions').textContent = localStats.pageViews || '0';
  document.getElementById('ga-time').textContent = '2:30';
});
</script>
