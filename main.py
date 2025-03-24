from telegram.ext import ApplicationBuilder
from handlers import setup_conversation_handlers, register_menu_commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_conversation_handlers(app)
    await register_menu_commands(app)
    await app.run_polling()  # this manages its own loop safely

if __name__ == "__main__":
    asyncio.run(main())
