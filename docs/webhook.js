// docs/webhook.js - Обработчик вебхуков для GitHub Pages
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  if (request.method === 'POST') {
    try {
      const update = await request.json()
      return await processUpdate(update)
    } catch (error) {
      return new Response('Error processing request', { status: 500 })
    }
  }
  
  return new Response('Method not allowed', { status: 405 })
}

async function processUpdate(update) {
  // Здесь будет логика обработки сообщений
  console.log('Received update:', JSON.stringify(update))
  
  // Простой ответ
  return new Response('OK', { status: 200 })
}
