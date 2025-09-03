export async function GET() {
  return Response.json({
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
