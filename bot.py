import os
import random
import logging
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGODB_URI")

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["neuronudgebot"]
users_collection = db["users"]

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Default study messages
STUDY_MESSAGES = {
    "general": [
        "Stay focused! Take a deep breath and keep learning. 📚",
        "Small progress is still progress. Keep going! 🚀",
        "Your efforts today will pay off in the future! 🔥",
    ],
    "cybersecurity": [
        "Time for a security challenge! Try solving one now. 🔓",
        "Think like a hacker, defend like a pro! 🛡️",
        "Cybersecurity is a mindset. Stay sharp! 💻",
    ],
}

# Define active hours
SGT = timezone(timedelta(hours=8))
ACTIVE_HOURS = (9, 17)  # 9 AM - 5 PM SGT

# Utility: Safe Username Getter
def get_username_safe(user):
    return user.username if user.username else str(user.id)

# Command: /start
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.message.chat_id
    username = get_username_safe(user)

    user_data = {
        "first_name": user.first_name,
        "username": username,
        "chat_id": chat_id,
        "study_type": "general",
        "nudge_frequency": (5, 30),
        "custom_messages": [],
        "nudge_mode": "default"
    }

    existing_user = users_collection.find_one({"username": username})
    if not existing_user:
        users_collection.insert_one(user_data)
        logging.info(f"New user added: {user_data}")

    await update.message.reply_text(
        f"Hi {user.first_name}, welcome to NeuroNudge! 🚀\n"
        "I will send you study nudges throughout the day.\n"
        "Use /help to see available commands."
    )

# Command: /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📌 *NeuroNudgeBot Commands*\n"
        "/start - Activate the bot\n"
        "/setstudy - Choose study focus (buttons)\n"
        "/setfrequency - Choose nudge frequency (buttons)\n"
        "/setnudgemode - Select nudge content source\n"
        "/addnudge - Add your own motivational nudge\n"
        "/startnudges - Begin nudges\n"
        "/stop - Stop receiving nudges\n"
        "/status - View current settings\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Command: /setstudy
async def set_study_type(update: Update, context: CallbackContext):
    keyboard = [[
        InlineKeyboardButton("General", callback_data='study_general'),
        InlineKeyboardButton("Cybersecurity", callback_data='study_cybersecurity'),
    ]]
    await update.message.reply_text("Choose your study focus:", reply_markup=InlineKeyboardMarkup(keyboard))

# Callback for study selection
async def handle_study_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    study_type = query.data.replace("study_", "")
    username = get_username_safe(query.from_user)

    users_collection.update_one(
        {"username": username},
        {"$set": {"study_type": study_type}},
        upsert=True
    )
    await query.edit_message_text(f"✅ Study type updated to {study_type.capitalize()}")

# Command: /setfrequency
async def set_frequency(update: Update, context: CallbackContext):
    keyboard = [[
        InlineKeyboardButton("Every 5-15 mins", callback_data='freq_5_15'),
        InlineKeyboardButton("Every 15-30 mins", callback_data='freq_15_30')
    ], [
        InlineKeyboardButton("Every 30-60 mins", callback_data='freq_30_60')
    ]]
    await update.message.reply_text("Choose your preferred nudge frequency:", reply_markup=InlineKeyboardMarkup(keyboard))

# Callback for frequency
async def handle_frequency_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    username = get_username_safe(query.from_user)

    freq_map = {
        'freq_5_15': (5, 15),
        'freq_15_30': (15, 30),
        'freq_30_60': (30, 60)
    }
    choice = query.data
    if choice in freq_map:
        users_collection.update_one(
            {"username": username},
            {"$set": {"nudge_frequency": freq_map[choice]}}
        )
        await query.edit_message_text(f"✅ Nudge frequency set to {freq_map[choice][0]}-{freq_map[choice][1]} minutes")

# Command: /setnudgemode
async def set_nudge_mode(update: Update, context: CallbackContext):
    keyboard = [[
        InlineKeyboardButton("Default Only", callback_data='nudge_default'),
        InlineKeyboardButton("Custom Only", callback_data='nudge_custom'),
        InlineKeyboardButton("Mixed Mode", callback_data='nudge_mixed')
    ]]
    await update.message.reply_text("Select your nudge content preference:", reply_markup=InlineKeyboardMarkup(keyboard))

# Callback for nudge mode
async def handle_nudge_mode_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    username = get_username_safe(query.from_user)
    mode = query.data.replace("nudge_", "")

    users_collection.update_one(
        {"username": username},
        {"$set": {"nudge_mode": mode}},
        upsert=True
    )
    await query.edit_message_text(f"✅ Nudge mode set to: {mode.replace('_', ' ').title()}")

# Command: /addnudge
async def add_nudge(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me the message you want to add to your nudges:", reply_markup=ReplyKeyboardRemove())
    return 1

# Handler to save user message
async def save_custom_nudge(update: Update, context: CallbackContext):
    user = update.effective_user
    username = get_username_safe(user)
    new_message = update.message.text.strip()

    if new_message:
        users_collection.update_one(
            {"username": username},
            {"$push": {"custom_messages": new_message}}
        )
        await update.message.reply_text("✅ Your custom nudge has been saved!")
    return -1

# Nudge Scheduler
async def send_nudge(context: CallbackContext):
    job = context.job
    username = job.data["username"]
    chat_id = job.chat_id

    user_doc = users_collection.find_one({"username": username})
    study_type = user_doc.get("study_type", "general")
    mode = user_doc.get("nudge_mode", "default")
    custom_msgs = user_doc.get("custom_messages", [])

    messages = []
    if mode == "default":
        messages = STUDY_MESSAGES[study_type]
    elif mode == "custom":
        if custom_msgs:
            messages = custom_msgs
        else:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ You selected *custom* nudges but haven’t added any. I’ll use default ones for now.", parse_mode="Markdown")
            messages = STUDY_MESSAGES[study_type]
    elif mode == "mixed":
        messages = STUDY_MESSAGES[study_type] + custom_msgs
        if not messages:
            messages = STUDY_MESSAGES[study_type]

    if messages:
        message = random.choice(messages)
        await context.bot.send_message(chat_id=chat_id, text=f"NeuroNudge says: {message} 🚀")

# Register bot
# Update all existing users with new fields if missing
def initialize_user_fields():
    users_collection.update_many(
        {},
        {
            "$set": {
                "custom_messages": [],
                "nudge_mode": "default"
            }
        }
    )

def main():
    initialize_user_fields()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setstudy", set_study_type))
    app.add_handler(CallbackQueryHandler(handle_study_choice, pattern="^study_"))
    app.add_handler(CommandHandler("setfrequency", set_frequency))
    app.add_handler(CallbackQueryHandler(handle_frequency_choice, pattern="^freq_"))
    app.add_handler(CommandHandler("setnudgemode", set_nudge_mode))
    app.add_handler(CallbackQueryHandler(handle_nudge_mode_choice, pattern="^nudge_"))
    app.add_handler(CommandHandler("addnudge", add_nudge))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_custom_nudge))

    app.run_polling()

if __name__ == "__main__":
    main()
