// api/telegram.js
const { Telegraf } = require('telegraf')

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN)

// Добавьте логирование
bot.use((ctx, next) => {
  console.log('📨 Received:', ctx.message?.text)
  return next()
})

bot.command('start', (ctx) => {
  console.log('🚀 Start command received')
  ctx.reply('🤖 Бот работает! Готов к генерации изображений для статей.')
})

bot.on('text', (ctx) => {
  console.log('💬 Text message:', ctx.message.text)
  ctx.reply('✅ Сообщение получено! Бот подключен к вебхуку.')
})

// Обработка ошибок
bot.catch((err) => {
  console.error('❌ Bot error:', err)
})

module.exports = async (req, res) => {
  try {
    console.log('🌐 Webhook called at:', new Date().toISOString())
    await bot.handleUpdate(req.body)
    res.status(200).send('OK')
  } catch (error) {
    console.error('💥 Webhook error:', error)
    res.status(500).send('Error')
  }
}
