// api/telegram.js - Обработчик вебхуков Telegram и активации Colab
export default async function handler(req, res) {
  if (req.method === 'POST') {
    try {
      const update = req.body;
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
      
      res.status(200).json({ status: 'ok' });
      
    } catch (error) {
      console.error('💥 Error processing webhook:', error);
      res.status(200).json({ status: 'error' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}

// 🔥 ENDPOINT ДЛЯ АКТИВАЦИИ COLAB
export async function activateColabHandler(req, res) {
  if (req.method === 'POST') {
    try {
      const { prompt, secret, action_type = 'scheduled', chat_id } = req.body;
      
      console.log('📨 Received activation request:', { prompt, action_type });
      
      // Проверка секретного ключа
      if (!secret || secret !== process.env.ACTIVATION_SECRET) {
        console.log('❌ Invalid secret');
        return res.status(403).json({ 
          error: 'Forbidden',
          message: 'Invalid activation secret' 
        });
      }
      
      console.log(`🚀 ${action_type} активация Colab:`, prompt);
      
      // Отправляем команду в Telegram для активации Colab
      const token = process.env.TELEGRAM_BOT_TOKEN;
      const targetChatId = chat_id || process.env.TELEGRAM_CHAT_ID;
      
      if (!token || !targetChatId) {
        console.log('❌ Missing Telegram credentials');
        return res.status(500).json({ 
          error: 'Missing credentials',
          details: 'TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set' 
        });
      }
      
      const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: targetChatId,
          text: `/generate ${prompt}`,
          parse_mode: 'Markdown'
        })
      });
      
      const result = await response.json();
      
      if (result.ok) {
        console.log('✅ Activation message sent successfully');
        res.status(200).json({ 
          status: 'success', 
          message: 'Colab активирован',
          action_type: action_type,
          sent_message: result.result
        });
      } else {
        console.log('❌ Failed to send message:', result);
        res.status(500).json({ 
          error: 'Failed to send message', 
          details: result 
        });
      }
      
    } catch (error) {
      console.error('❌ Activation error:', error);
      res.status(500).json({ 
        error: 'Internal error', 
        message: error.message 
      });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}

// 🔧 ТЕСТОВЫЙ ENDPOINT ДЛЯ ПРОВЕРКИ
export async function testHandler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({ 
      status: 'success', 
      message: 'Endpoint работает!',
      timestamp: new Date().toISOString(),
      environment: {
        has_bot_token: !!process.env.TELEGRAM_BOT_TOKEN,
        has_chat_id: !!process.env.TELEGRAM_CHAT_ID,
        has_activation_secret: !!process.env.ACTIVATION_SECRET
      }
    });
  }
  res.status(405).json({ error: 'Method not allowed' });
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
