// 🔥 ENDPOINT ДЛЯ АКТИВАЦИИ COLAB ИЗ GITHUB ACTIONS
export async function activateColabHandler(req, res) {
  if (req.method === 'POST') {
    try {
      const { prompt, secret, action_type = 'scheduled' } = req.body;
      
      // Проверка секретного ключа
      if (secret !== process.env.ACTIVATION_SECRET) {
        return res.status(403).json({ error: 'Forbidden' });
      }
      
      console.log(`🚀 ${action_type === 'manual' ? 'Ручная' : 'Плановая'} активация Colab:`, prompt);
      
      // Отправляем команду в Telegram для активации Colab
      const token = '8006769060:AAEGAKhjUeuAXfnsQWtdLcKpAjkJrrGQ1Fk';
      const CHAT_ID = process.env.ADMIN_CHAT_ID; // Ваш chat_id
      
      await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: CHAT_ID,
          text: `/generate ${prompt}`,
          parse_mode: 'Markdown'
        })
      });
      
      res.status(200).json({ 
        status: 'success', 
        message: 'Colab активирован',
        action_type: action_type
      });
      
    } catch (error) {
      console.error('❌ Activation error:', error);
      res.status(500).json({ error: 'Internal error' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
