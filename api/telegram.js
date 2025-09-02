// api/telegram.js
export default async function handler(req, res) {
  if (req.method === 'POST') {
    try {
      const update = req.body;
      console.log('📨 Received Telegram update');
      
      // Простая обработка сообщений
      if (update.message && update.message.text) {
        const token = '8006769060:AAEGAKhjUeuAXfnsQWtdLcKpAjkJrrGQ1Fk'; // Хардкод токена
        const chatId = update.message.chat.id;
        const userText = update.message.text;
        
        console.log(`💬 Message from ${chatId}: ${userText}`);
        
        // Отправляем ответ через Telegram API
        const telegramResponse = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            chat_id: chatId,
            text: `🤖 Бот работает! Вы написали: "${userText}"\n\nГотов к генерации изображений для статей!`
          })
        });
        
        const result = await telegramResponse.json();
        console.log('📤 Telegram API response:', result);
        
        if (telegramResponse.ok) {
          console.log('✅ Ответ отправлен в Telegram');
        } else {
          console.error('❌ Ошибка отправки ответа:', result);
        }
      }
      
      res.status(200).json({ status: 'ok' });
      
    } catch (error) {
      console.error('💥 Error processing webhook:', error);
      res.status(200).json({ status: 'error', message: error.message });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
