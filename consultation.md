---
layout: default
title: Консультации
description: Профессиональные консультации по настройке нейросетей и оптимизации железа
---

# 🎯 Консультации

<div class="consultation-container">
  <div class="row justify-content-center">
    <div class="col-md-8">
      <div class="neural-card-3d">
        <h2 class="text-center">Профессиональные консультации</h2>
        <p class="lead text-center">Помогу вам настроить нейросети, оптимизировать железо или решить конкретные задачи с AI</p>

        <div class="services-grid">
          <div class="service-item">
            <h4>🛠️ Настройка AI-инфраструктуры</h4>
            <ul>
              <li>Установка и настройка Stable Diffusion</li>
              <li>Оптимизация под ваше железо</li>
              <li>Настройка локальных LLM</li>
              <li>Развертывание AI-инструментов</li>
            </ul>
          </div>

          <div class="service-item">
            <h4>⚡ Оптимизация железа</h4>
            <ul>
              <li>Анализ текущей конфигурации</li>
              <li>Рекомендации по апгрейду</li>
              <li>Настройка для максимальной производительности</li>
              <li>Оптимизация под нейросети</li>
            </ul>
          </div>

          <div class="service-item">
            <h4>🎨 Индивидуальное обучение</h4>
            <ul>
              <li>Основы работы с нейросетями</li>
              <li>Продвинутые техники генерации</li>
              <li>Решение конкретных задач</li>
              <li>Работа с промптами и настройками</li>
            </ul>
          </div>

          <div class="service-item">
            <h4>🔧 Экстренная помощь</h4>
            <ul>
              <li>Срочное решение проблем</li>
              <li>Настройка "здесь и сейчас"</li>
              <li>Помощь с ошибками и багами</li>
              <li>Оптимизация рабочих процессов</li>
            </ul>
          </div>
        </div>

        <div class="contact-info text-center mt-5">
          <h3>📞 Свяжитесь со мной</h3>
          <p>Обсудим вашу задачу и найдём оптимальное решение</p>
          
          <div class="contact-methods">
            <div class="contact-method">
              <h5>📧 Email</h5>
              <code class="contact-detail">Lybra7@yandex.ru</code>
              <button onclick="copyToClipboard('Lybra7@yandex.ru')" class="btn btn-outline-light btn-sm mt-1">
                📋 Копировать
              </button>
              <a href="mailto:Lybra7@yandex.ru?subject=Консультация по AI" class="btn btn-primary btn-sm mt-1">
                Написать письмо
              </a>
            </div>
            
            <div class="contact-method">
              <h5>📱 Telegram</h5>
              <code class="contact-detail">@Lybra777</code>
              <button onclick="copyToClipboard('@Lybra777')" class="btn btn-outline-light btn-sm mt-1">
                📋 Копировать
              </button>
              <a href="https://t.me/Lybra777" target="_blank" class="btn btn-outline-primary btn-sm mt-1">
                Написать в Telegram
              </a>
            </div>
          </div>
        </div>

        <div class="process-section mt-5">
          <h3>🔄 Как проходит консультация</h3>
          <div class="process-steps">
            <div class="process-step">
              <h5>1. Обсуждение задачи</h5>
              <p>Вы описываете свою проблему или задачу</p>
            </div>
            <div class="process-step">
              <h5>2. Анализ ситуации</h5>
              <p>Я изучаю вашу конфигурацию и требования</p>
            </div>
            <div class="process-step">
              <h5>3. Предложение решения</h5>
              <p>Предлагаю оптимальный способ решения</p>
            </div>
            <div class="process-step">
              <h5>4. Реализация</h5>
              <p>Помогаю реализовать решение на практике</p>
            </div>
          </div>
        </div>

        <div class="reviews-section mt-5">
          <h3>💬 Отзывы клиентов</h3>
          <div class="review-item">
            <p>"Помог настроить Stable Diffusion на моём старом GTX 1060. Теперь всё летает!"</p>
            <small>- Алексей, г. Москва</small>
          </div>
          <div class="review-item">
            <p>"Консультация по выбору железа сэкономила мне 15 тысяч рублей. Спасибо!"</p>
            <small>- Дмитрий, г. Санкт-Петербург</small>
          </div>
          <div class="review-item">
            <p>"Объяснил сложные вещи простым языком. Теперь уверенно работаю с нейросетями."</p>
            <small>- Мария, г. Новосибирск</small>
          </div>
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
    alert('Не удалось скопировать. Скопируйте вручную: ' + text);
  });
}
</script>
