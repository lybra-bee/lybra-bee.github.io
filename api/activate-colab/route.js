export async function POST(request) {
  try {
    const { prompt, secret, action_type = 'scheduled', chat_id } = await request.json();
    
    console.log('📨 Received activation request:', { prompt, action_type });
    
    // Проверка секретного ключа
    if (!secret || secret !== process.env.ACTIVATION_SECRET) {
      console.log('❌ Invalid secret');
      return Response.json({ error: 'Forbidden' }, { status: 403 });
    }
    
    console.log(`🚀 ${action_type} активация Colab:`, prompt);
    
    // Отправляем команду в Telegram для активации Colab
    const token = process.env.TELEGRAM_BOT_TOKEN;
    const targetChatId = chat_id || process.env.TELEGRAM_CHAT_ID;
    
    if (!token || !targetChatId) {
      console.log('❌ Missing Telegram credentials');
      return Response.json({ error: 'Missing credentials' }, { status: 500 });
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
      return Response.json({
        status: 'success',
        message: 'Colab активирован',
        action_type: action_type
      });
    } else {
      console.log('❌ Failed to send message:', result);
      return Response.json({ error: 'Failed to send message', details: result }, { status: 500 });
    }
    
  } catch (error) {
    console.error('❌ Activation error:', error);
    return Response.json({ error: 'Internal error', message: error.message }, { status: 500 });
  }
}
