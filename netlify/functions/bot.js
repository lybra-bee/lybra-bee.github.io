// netlify/functions/bot.js
const { Telegraf } = require('telegraf')

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' }
  }

  const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN)
  
  bot.on('text', (ctx) => {
    ctx.reply('Сообщение получено!')
  })

  try {
    await bot.handleUpdate(JSON.parse(event.body))
    return { statusCode: 200, body: 'OK' }
  } catch (error) {
    return { statusCode: 500, body: 'Error' }
  }
}
