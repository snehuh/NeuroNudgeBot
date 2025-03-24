from telegram.ext import ApplicationBuilder
from handlers import setup_conversation_handlers, register_menu_commands
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()
setup_conversation_handlers(app)
register_menu_commands(app)

if __name__ == "__main__":
    app.run_polling()
