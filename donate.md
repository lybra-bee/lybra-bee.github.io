---
layout: default
title: Поддержать проект
description: Поддержите развитие проекта и помогите собрать на новое железо для AI
---

# 💝 Поддержать проект

<div class="donate-container">
  <div class="row justify-content-center">
    <div class="col-md-8">
      <div class="neural-card-3d text-center">
        <h2>Поддержите развитие проекта</h2>
        <p class="lead">Ваша поддержка поможет ускорить разработку и собрать на мощную видеокарту для локальной работы с нейросетями</p>
        
        <div class="progress-section mb-4">
          <h4>Цель: RTX 4090 (2000$)</h4>
          <div class="progress" style="height: 25px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                 style="width: 5%;">5%</div>
          </div>
          <p class="mt-2"><small>Собрано: 100$ из 2000$</small></p>
        </div>

        <div class="payment-methods">
          <h3>💳 Перевод на банковскую карту</h3>
          <p class="text-muted">Выберите любую карту для перевода</p>
          
          <div class="row mt-4">
            <div class="col-md-4 mb-4">
              <div class="payment-method neural-card-3d">
                <h4>🔷 Карта 1</h4>
                <p>Основная карта для переводов</p>
                <div class="card-info">
                  <p><strong>Номер карты:</strong></p>
                  <code class="card-number">2204 3201 5374 0651</code>
                  <button onclick="copyToClipboard('2204320153740651')" class="btn btn-outline-light btn-sm mt-2">
                    📋 Копировать номер
                  </button>
                </div>
              </div>
            </div>
            
            <div class="col-md-4 mb-4">
              <div class="payment-method neural-card-3d">
                <h4>🔷 Карта 2</h4>
                <p>Дополнительная карта</p>
                <div class="card-info">
                  <p><strong>Номер карты:</strong></p>
                  <code class="card-number">2204 3201 6279 6777</code>
                  <button onclick="copyToClipboard('2204320162796777')" class="btn btn-outline-light btn-sm mt-2">
                    📋 Копировать номер
                  </button>
                </div>
              </div>
            </div>
            
            <div class="col-md-4 mb-4">
              <div class="payment-method neural-card-3d">
                <h4>🔷 Карта 3</h4>
                <p>Резервная карта</p>
                <div class="card-info">
                  <p><strong>Номер карты:</strong></p>
                  <code class="card-number">2204 3101 9359 0521</code>
                  <button onclick="copyToClipboard('2204310193590521')" class="btn btn-outline-light btn-sm mt-2">
                    📋 Копировать номер
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="instructions mt-4">
            <div class="neural-card-3d p-4">
              <h4>📋 Как перевести:</h4>
              <ol class="text-start">
                <li>Скопируйте номер карты (кнопка "Копировать номер")</li>
                <li>В приложении вашего банка выберите "Перевод по номеру карты"</li>
                <li>Вставьте скопированный номер карты</li>
                <li>Укажите сумму перевода</li>
                <li>Подтвердите операцию</li>
              </ol>
              <p class="text-muted mt-3"><small>Переводы между картами разных банков обычно бесплатны и приходят мгновенно</small></p>
            </div>
          </div>
        </div>

        <div class="benefits-section mt-5">
          <h3>🎯 На что пойдут средства:</h3>
          <ul class="list-unstyled">
            <li>✅ Мощная видеокарта для локального AI (RTX 4090)</li>
            <li>✅ Более быстрая генерация контента</li>
            <li>✅ Эксперименты с большими моделями нейросетей</li>
            <li>✅ Видео-туториалы и стримы</li>
            <li>✅ Открытый исходный код инструментов</li>
          </ul>
        </div>

        <div class="thank-you mt-4">
          <p class="text-muted">Спасибо за вашу поддержку! Каждый рубль приближает нас к цели 🚀</p>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function() {
    // Показываем уведомление об успешном копировании
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '✅ Скопировано!';
    button.classList.add('btn-success');
    button.classList.remove('btn-outline-light');
    
    setTimeout(function() {
      button.textContent = originalText;
      button.classList.remove('btn-success');
      button.classList.add('btn-outline-light');
    }, 2000);
  }).catch(function(err) {
    console.error('Ошибка копирования: ', err);
    alert('Не удалось скопировать номер карты. Скопируйте вручную: ' + text);
  });
}
</script>
