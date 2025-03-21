import os
import asyncio
import random
import logging
from datetime import datetime, time, timedelta, timezone
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Load environment variables
load_dotenv()

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("neuronudgebot.log"),
        logging.StreamHandler()
    ]
)

# Store subscribed users
SUBSCRIBED_USERS = set()

# Nudge messages
NUDGES = [
    "Hey {name}! Have you reviewed a TryHackMe room today? 🕵️‍♀️",
    "Reminder: CCNA and Security+ won't study themselves 😅",
    "Time to flex those cyber muscles 💪 Hack something small today!",
    "Don't forget to update your cybersecurity portfolio 🧠",
    "Feeling stuck? Do 15 mins of TryHackMe — small wins add up!",
    "NeuroNudge says: go conquer a THM challenge 🚀",
    "Review your notes or flashcards – tiny effort, big reward! 🧠",
    "Ping! Let’s get one thing done for your future self 👩‍💻"
]

# Define timezone offset for Singapore (UTC+8)
SGT_OFFSET = timedelta(hours=8)

def within_active_hours():
    now_utc = datetime.now(timezone.utc)
    now_sgt = now_utc + SGT_OFFSET
    return time(9, 0) <= now_sgt.time() <= time(17, 0)

async def send_nudge():
    if not SUBSCRIBED_USERS:
        logging.info("No subscribed users. Skipping nudge.")
        return
    
    for user_id, first_name in SUBSCRIBED_USERS:
        message = random.choice(NUDGES).format(name=first_name)
        try:
            await bot.send_message(chat_id=user_id, text=message)
            logging.info(f"Sent nudge to {first_name} ({user_id}): {message}")
        except Exception as e:
            logging.error(f"Failed to send nudge to {first_name} ({user_id}): {e}")

async def run_nudger():
    while True:
        if within_active_hours():
            await send_nudge()
            # Wait between 2 to 4 hours randomly
            wait_time = random.randint(300, 1800)
        else:
            logging.info("Outside active hours. Sleeping for 30 minutes.")
            wait_time = 1800  # 30 minutes

        await asyncio.sleep(wait_time)

# Telegram Command Handlers
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    first_name = update.message.chat.first_name
    SUBSCRIBED_USERS.add((user_id, first_name))
    await update.message.reply_text(f"🚀 NeuroNudge Bot activated! Welcome, {first_name}! You'll now receive study nudges between 9AM-5PM SGT.")
    logging.info(f"User {first_name} ({user_id}) subscribed.")

async def stop(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    first_name = update.message.chat.first_name
    SUBSCRIBED_USERS.discard((user_id, first_name))
    await update.message.reply_text("❌ You've unsubscribed from NeuroNudge nudges. Type /start to re-enable.")
    logging.info(f"User {first_name} ({user_id}) unsubscribed.")

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))

if __name__ == "__main__":
    logging.info("NeuroNudgeBot started.")
    app.run_polling()
    asyncio.run(run_nudger())
