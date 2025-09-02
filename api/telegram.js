// api/telegram.js
const { Telegraf } = require('telegraf')

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN)

// Обработчики команд
bot.command('start', (ctx) => {
  ctx.reply('🤖 Бот работает через Vercel! Готов к генерации изображений.')
})

bot.on('text', (ctx) => {
  ctx.reply('✅ Сообщение получено! Бот работает корректно.')
})

// Обработка вебхука
module.exports = async (req, res) => {
  try {
    await bot.handleUpdate(req.body)
    res.status(200).send('OK')
  } catch (error) {
    console.error('Error:', error)
    res.status(500).send('Error')
  }
}
