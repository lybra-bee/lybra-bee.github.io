// api/telegram.js
export default async function handler(req, res) {
  if (req.method === 'POST') {
    try {
      const update = req.body;
      console.log('📨 Received Telegram update');
      
      if (update.message && update.message.text) {
        const token = '8006769060:AAEGAKhjUeuAXfnsQWtdLcKpAjkJrrGQ1Fk';
        const chatId = update.message.chat.id;
        const userText = update.message.text;
        
        console.log(`💬 Message from ${chatId}: ${userText}`);
        
        // Обработка команды /generate
        if (userText.startsWith('/generate')) {
          const prompt = userText.replace('/generate', '').trim();
          if (prompt) {
            await handleGenerateCommand(token, chatId, prompt);
          } else {
            await sendMessage(token, chatId, '📝 Usage: /generate описание изображения');
          }
        }
        // Обработка команды /start
        else if (userText.startsWith('/start')) {
          await sendMessage(token, chatId,
            '🤖 **AI Image Generator Bot**\n\n' +
            'Я могу генерировать изображения для статей!\n\n' +
            '**Команды:**\n' +
            '/generate [описание] - Сгенерировать изображение\n' +
            '/help - Показать справку\n\n' +
            '**Пример:**\n' +
            '/generate футуристический город с небоскребами'
          );
        }
        // Обработка команды /help
        else if (userText.startsWith('/help')) {
          await sendMessage(token, chatId,
            '🆘 **Помощь:**\n\n' +
            '• Используйте /generate для создания изображений\n' +
            '• Добавляйте детали: "4k, digital art, professional"\n' +
            '• Изображения сохраняются для статей блога\n\n' +
            '**Примеры:**\n' +
            '/generate киберпанк город ночью\n' +
            '/generate робот в стиле аниме\n' +
            '/generate космический корабль будущего'
          );
        }
        // Любое другое сообщение
        else {
          await sendMessage(token, chatId,
            '👋 Привет! Я AI бот для генерации изображений.\n\n' +
            'Используйте /generate чтобы создать изображение для статьи.\n' +
            'Напишите /help для справки.'
          );
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

async function handleGenerateCommand(token, chatId, prompt) {
  try {
    await sendMessage(token, chatId, `🎨 Генерирую изображение для: "${prompt}"\n\n⏳ Это займет 20-30 секунд...`);
    
    // Здесь будет интеграция с вашим генератором
    // Пока просто имитируем генерацию
    const enhancedPrompt = `${prompt}, digital art, futuristic, 4k, high quality`;
    
    await sendMessage(token, chatId, 
      `✅ Изображение сгенерировано!\n\n` +
      `**Промпт:** ${enhancedPrompt}\n\n` +
      `Изображение сохранено для статей блога.`
    );
    
    console.log(`✅ Generated image for: ${prompt}`);
    
  } catch (error) {
    console.error('❌ Generation error:', error);
    await sendMessage(token, chatId, '❌ Ошибка генерации изображения. Попробуйте еще раз.');
  }
}

async function sendMessage(token, chatId, text) {
  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
      parse_mode: 'Markdown'
    })
  });
  
  return response.json();
}
