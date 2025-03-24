from telegram.ext import ApplicationBuilder
from handlers import setup_conversation_handlers, register_menu_commands
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()
setup_conversation_handlers(app)

# Register commands inside the app lifecycle
async def post_init(app):
    await register_menu_commands(app)

app.post_init = post_init

if __name__ == "__main__":
    app.run_polling()
