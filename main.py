from telegram.ext import ApplicationBuilder
from handlers import setup_conversation_handlers, register_menu_commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_conversation_handlers(app)
    await register_menu_commands(app)
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(start_bot())
