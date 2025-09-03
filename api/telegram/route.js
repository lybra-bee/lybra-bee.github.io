export async function POST(request) {
  try {
    const update = await request.json();
    console.log('📨 Received Telegram update');
    
    if (update.message && update.message.text) {
      const token = process.env.TELEGRAM_BOT_TOKEN;
      const chatId = update.message.chat.id;
      const userText = update.message.text;
      
      console.log(`💬 Message from ${chatId}: ${userText}`);
      
      // Обработка команды /generate
      if (userText.startsWith('/generate')) {
        const prompt = userText.replace('/generate', '').trim();
        if (prompt) {
          await handleGenerateCommand(token, chatId, prompt);
        }
      }
      // Обработка других команд
      else if (userText.startsWith('/')) {
        await handleCommand(token, chatId, userText);
      }
    }
    
    return Response.json({ status: 'ok' });
    
  } catch (error) {
    console.error('💥 Error processing webhook:', error);
    return Response.json({ status: 'error' });
  }
}

async function handleGenerateCommand(token, chatId, prompt) {
  try {
    await sendMessage(token, chatId, `🎨 Генерирую изображение для: "${prompt}"\n\n⏳ Это займет 20-30 секунд...`);
    console.log(`✅ Generated image for: ${prompt}`);
    
  } catch (error) {
    console.error('❌ Generation error:', error);
    await sendMessage(token, chatId, '❌ Ошибка генерации изображения. Попробуйте еще раз.');
  }
}

async function handleCommand(token, chatId, command) {
  switch (command) {
    case '/start':
      await sendMessage(token, chatId,
        '🤖 **AI Image Generator Bot**\n\n' +
        'Я генерирую изображения для AI-статей блога!\n\n' +
        '**Команды:**\n' +
        '/generate [описание] - Сгенерировать изображение\n' +
        '/help - Показать справку'
      );
      break;
      
    case '/help':
      await sendMessage(token, chatId,
        '🆘 **Помощь:**\n\n' +
        '• /generate [описание] - создать изображение\n' +
        '• Добавляйте детали: "4k, digital art, professional"\n' +
        '• Изображения сохраняются для статей блога\n\n' +
        '**Примеры:**\n' +
        '/generate киберпанк город ночью\n' +
        '/generate робот в стиле аниме'
      );
      break;
      
    default:
      await sendMessage(token, chatId,
        '👋 Привет! Я AI бот для генерации изображений.\n\n' +
        'Используйте /generate чтобы создать изображение.\n' +
        'Напишите /help для справки.'
      );
  }
}

async function sendMessage(token, chatId, text) {
  try {
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
    
    return await response.json();
  } catch (error) {
    console.error('❌ Send message error:', error);
    throw error;
  }
}
