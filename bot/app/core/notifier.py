from app.bot.bot import bot

async def notify_user(user_id, text):
    await bot.send_message(user_id, text)
