import os
import asyncio
import random
import logging
from datetime import datetime, time, timedelta, timezone
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# Store subscribed users and their nudge frequency range
SUBSCRIBED_USERS = {}  # Format: {user_id: (first_name, min_frequency, max_frequency, study_topic, custom_nudges)}
#DEFAULT_MIN_FREQUENCY = 300   # 5 minutes
#DEFAULT_MAX_FREQUENCY = 1800  # 30 minutes
DEFAULT_MIN_FREQUENCY = 60   # 1 MINUTE FOR TESTING
DEFAULT_MAX_FREQUENCY = 180  # 3 minutes FOR TESTING

# Default nudge messages
DEFAULT_NUDGES = {
    "general": [
        "Hey {name}! Have you reviewed your study material today? 📚",
        "Reminder: Small, consistent efforts lead to big results! 💡",
        "Keep going! Stay focused on your goals 🚀",
        "Ping! Let’s get one thing done for your future self 👩‍💻"
    ],
    "cybersecurity": [
        "Hey {name}! Have you reviewed a TryHackMe room today? 🕵️‍♀️",
        "Reminder: CCNA and Security+ won't study themselves 😅",
        "Time to flex those cyber muscles 💪 Hack something small today!",
        "Don't forget to update your cybersecurity portfolio 🧠"
    ]
}

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
    
    for user_id, (first_name, min_freq, max_freq, study_topic, custom_nudges) in SUBSCRIBED_USERS.items():
        if custom_nudges:
            message = random.choice(custom_nudges)
        else:
            message = random.choice(DEFAULT_NUDGES.get(study_topic, DEFAULT_NUDGES["general"])).format(name=first_name)
        
        try:
            await bot.send_message(chat_id=user_id, text=message)
            logging.info(f"Sent nudge to {first_name} ({user_id}): {message}")
        except Exception as e:
            logging.error(f"Failed to send nudge to {first_name} ({user_id}): {e}")

async def run_nudger():
    while True:
        if within_active_hours():
            for user_id, (_, min_freq, max_freq, _, _) in SUBSCRIBED_USERS.items():
                await send_nudge()
                wait_time = random.randint(min_freq, max_freq)
                logging.info(f"Next nudge for {user_id} in {wait_time // 60} minutes.")
                await asyncio.sleep(wait_time)
        else:
            logging.info("Outside active hours. Sleeping for 30 minutes.")
            await asyncio.sleep(1800)  # Sleep for 30 mins

# Telegram Command Handlers
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    first_name = update.message.chat.first_name
    SUBSCRIBED_USERS[user_id] = (first_name, DEFAULT_MIN_FREQUENCY, DEFAULT_MAX_FREQUENCY, "general", [])
    await update.message.reply_text(f"🚀 NeuroNudge Bot activated! Welcome, {first_name}! You'll now receive study nudges between 9AM-5PM SGT every 5-30 mins.")
    logging.info(f"User {first_name} ({user_id}) subscribed with default settings.")

async def stop(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in SUBSCRIBED_USERS:
        first_name = SUBSCRIBED_USERS[user_id][0]
        del SUBSCRIBED_USERS[user_id]
        await update.message.reply_text("❌ You've unsubscribed from NeuroNudge nudges. Type /start to re-enable.")
        logging.info(f"User {first_name} ({user_id}) unsubscribed.")

async def set_study_topic(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    first_name = update.message.chat.first_name
    
    if len(context.args) != 1:
        await update.message.reply_text("⚙️ Usage: /settopic <topic>. Example: /settopic cybersecurity")
        return
    
    study_topic = context.args[0].lower()
    SUBSCRIBED_USERS[user_id] = (first_name, *SUBSCRIBED_USERS[user_id][1:3], study_topic, [])
    
    await update.message.reply_text(f"✅ {first_name}, you've set your study focus to {study_topic}.")
    logging.info(f"User {first_name} ({user_id}) set study topic to {study_topic}.")

async def add_custom_nudge(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if len(context.args) < 1:
        await update.message.reply_text("⚙️ Usage: /addnudge <your custom nudge>")
        return
    
    custom_nudge = " ".join(context.args)
    SUBSCRIBED_USERS[user_id][4].append(custom_nudge)
    await update.message.reply_text("✅ Your custom nudge has been added!")

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("settopic", set_study_topic))
app.add_handler(CommandHandler("addnudge", add_custom_nudge))

if __name__ == "__main__":
    logging.info("NeuroNudgeBot started.")
    app.run_polling()
    asyncio.run(run_nudger())
import os
import asyncio
import random
import logging
from datetime import datetime, time, timedelta, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Get environment variables securely
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not TELEGRAM_BOT_TOKEN or not MONGODB_URI:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or MONGODB_URI. Check your .env file.")

# Initialize the bot securely
bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Set up logging securely
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("neuronudgebot.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client["neuronudgebot"]
users_collection = db["users"]

# Default nudge messages
DEFAULT_NUDGES = {
    "general": [
        "Hey {name}! Have you reviewed your study material today? 📚",
        "Reminder: Small, consistent efforts lead to big results! 💡",
        "Keep going! Stay focused on your goals 🚀",
        "Ping! Let’s get one thing done for your future self 👩‍💻"
    ],
    "cybersecurity": [
        "Hey {name}! Have you reviewed a TryHackMe room today? 🕵️‍♀️",
        "Reminder: CCNA and Security+ won't study themselves 😅",
        "Time to flex those cyber muscles 💪 Hack something small today!",
        "Don't forget to update your cybersecurity portfolio 🧠"
    ]
}

# Define timezone offset for Singapore (UTC+8)
SGT_OFFSET = timedelta(hours=8)

def within_active_hours():
    now_utc = datetime.now(timezone.utc)
    now_sgt = now_utc + SGT_OFFSET
    return time(9, 0) <= now_sgt.time() <= time(17, 0)

def get_user(user_id):
    return users_collection.find_one({"user_id": user_id})

def save_user(user_id, first_name, study_topic="general", min_freq=300, max_freq=1800, custom_nudges=[]):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "first_name": first_name,
            "study_topic": study_topic,
            "min_freq": min_freq,
            "max_freq": max_freq,
            "custom_nudges": custom_nudges
        }},
        upsert=True
    )

def get_user_nudges(user_id):
    user = get_user(user_id)
    if user and "custom_nudges" in user and user["custom_nudges"]:
        return user["custom_nudges"]
    return DEFAULT_NUDGES.get(user["study_topic"], DEFAULT_NUDGES["general"])

async def send_nudge():
    users = users_collection.find()
    for user in users:
        user_id = user["user_id"]
        first_name = user["first_name"]
        message = random.choice(get_user_nudges(user_id)).format(name=first_name)
        try:
            await bot.send_message(chat_id=user_id, text=message)
            logging.info(f"Sent nudge to {first_name} ({user_id}): {message}")
        except Exception as e:
            logging.error(f"Failed to send nudge to {first_name} ({user_id}): {e}")

async def run_nudger():
    while True:
        if within_active_hours():
            await send_nudge()
            await asyncio.sleep(random.randint(300, 1800))
        else:
            logging.info("Outside active hours. Sleeping for 30 minutes.")
            await asyncio.sleep(1800)

async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    first_name = update.message.chat.first_name
    save_user(user_id, first_name)
    keyboard = [[
        InlineKeyboardButton("General 📚", callback_data="settopic_general"),
        InlineKeyboardButton("Cybersecurity 🛡️", callback_data="settopic_cybersecurity")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🚀 NeuroNudge Bot activated! Welcome, {first_name}! You'll now receive study nudges between 9AM-5PM SGT every 5-30 mins.\n\n"
        "Choose your study focus:",
        reply_markup=reply_markup
    )
    logging.info(f"User {first_name} ({user_id}) subscribed with default settings.")

async def stop(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    users_collection.delete_one({"user_id": user_id})
    await update.message.reply_text("❌ You've unsubscribed from NeuroNudge nudges. Type /start to re-enable.")
    logging.info(f"User ({user_id}) unsubscribed.")

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.message.chat_id
    topic = query.data.split("_")[1]
    save_user(user_id, get_user(user_id)["first_name"], study_topic=topic)
    await query.answer()
    await query.message.reply_text(f"✅ You've set your study focus to {topic.capitalize()}.")
    logging.info(f"User ({user_id}) set study topic to {topic}.")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CallbackQueryHandler(button_callback))

if __name__ == "__main__":
    logging.info("NeuroNudgeBot started.")
    app.run_polling()
    asyncio.run(run_nudger())