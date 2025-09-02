// api/telegram.js - работает без telegraf!
export default async function handler(req, res) {
  if (req.method === 'POST') {
    try {
      const update = req.body;
      console.log('📨 Received Telegram update');
      
      // Простая обработка сообщений
      if (update.message && update.message.text) {
        const token = process.env.TELEGRAM_BOT_TOKEN;
        const chatId = update.message.chat.id;
        const userText = update.message.text;
        
        console.log(`💬 Message from ${chatId}: ${userText}`);
        
        // Отправляем ответ через Telegram API
        const telegramResponse = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'User-Agent': 'Telegram-Bot/1.0'
          },
          body: JSON.stringify({
            chat_id: chatId,
            text: `🤖 Бот работает! Вы написали: "${userText}"\n\nГотов к генерации изображений для статей!`,
            parse_mode: 'HTML'
          })
        });
        
        if (telegramResponse.ok) {
          console.log('✅ Ответ отправлен в Telegram');
        } else {
          console.error('❌ Ошибка отправки ответа:', await telegramResponse.text());
        }
      }
      
      // Всегда возвращаем 200 OK для Telegram
      res.status(200).json({ status: 'ok' });
      
    } catch (error) {
      console.error('💥 Error processing webhook:', error);
      res.status(200).json({ status: 'error', message: error.message });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
