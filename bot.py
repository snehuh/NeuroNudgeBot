import os
import random
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext
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


### 1️⃣ START COMMAND
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.message.chat_id

    user_data = {
        "first_name": user.first_name,
        "username": user.username,
        "chat_id": chat_id,
        "study_type": "general",
        "nudge_frequency": (5, 30)
    }

    # Check if user exists
    existing_user = users_collection.find_one({"username": user.username})
    if not existing_user:
        users_collection.insert_one(user_data)
        logging.info(f"New user added: {user_data}")

    await update.message.reply_text(
        f"Hi {user.first_name}, welcome to NeuroNudge! 🚀\n"
        "I will send you study nudges throughout the day.\n"
        "Use /help to see available commands."
    )


### 2️⃣ HELP COMMAND
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📌 *NeuroNudgeBot Commands*\n"
        "/start - Activate the bot\n"
        "/setstudy <cybersecurity/general> - Choose study focus\n"
        "/setfrequency <min> <max> - Set nudge frequency (mins)\n"
        "/status - View current settings\n"
        "/stop - Stop receiving nudges\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


### 3️⃣ GET USER SETTINGS
def get_user_settings(username):
    user = users_collection.find_one({"username": username})
    if user:
        return user["study_type"], user["nudge_frequency"]
    return "general", (5, 30)


### 4️⃣ SET STUDY TYPE
async def set_study_type(update: Update, context: CallbackContext):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /setstudy <cybersecurity/general>")
        return

    study_type = context.args[0].lower()
    if study_type not in ["cybersecurity", "general"]:
        await update.message.reply_text("Invalid type. Choose 'cybersecurity' or 'general'.")
        return

    users_collection.update_one({"username": user.username}, {"$set": {"study_type": study_type}})
    await update.message.reply_text(f"Your study type has been updated to {study_type} ✅")


### 5️⃣ SET NUDGE FREQUENCY
async def set_nudge_frequency(update: Update, context: CallbackContext):
    user = update.effective_user
    try:
        min_freq, max_freq = map(int, context.args)
        if min_freq < 1 or max_freq > 120 or min_freq > max_freq:
            raise ValueError

        users_collection.update_one({"username": user.username}, {"$set": {"nudge_frequency": (min_freq, max_freq)}})
        await update.message.reply_text(f"Nudge frequency updated to {min_freq}-{max_freq} minutes ✅")

    except ValueError:
        await update.message.reply_text("Invalid input. Use: /setfrequency <min> <max> (1-120 mins)")


### 6️⃣ SEND NUDGE (RANDOM INTERVALS)
async def send_nudge(context: CallbackContext):
    job = context.job
    username = job.data["username"]
    chat_id = job.chat_id

    study_type, _ = get_user_settings(username)

    current_time = datetime.now(SGT).hour
    if not (ACTIVE_HOURS[0] <= current_time < ACTIVE_HOURS[1]):
        logging.info("Outside active hours. Sleeping...")
        return

    message = random.choice(STUDY_MESSAGES[study_type])
    await context.bot.send_message(chat_id=chat_id, text=f"NeuroNudge says: {message} 🚀")


### 7️⃣ START NUDGES
async def start_nudges(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.message.chat_id

    _, nudge_frequency = get_user_settings(user.username)

    min_time, max_time = nudge_frequency
    delay = random.randint(min_time, max_time) * 60

    context.job_queue.run_repeating(send_nudge, interval=delay, first=5, chat_id=chat_id, name=str(chat_id),
                                    data={"username": user.username})

    await update.message.reply_text(f"✅ Nudges activated! Frequency: {min_time}-{max_time} mins")


### 8️⃣ STOP NUDGES
async def stop(update: Update, context: CallbackContext):
    jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id))
    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("🚫 Nudges stopped.")


### 9️⃣ CHECK USER STATUS
async def status(update: Update, context: CallbackContext):
    user = update.effective_user
    study_type, nudge_frequency = get_user_settings(user.username)
    
    await update.message.reply_text(
        f"📊 *Your Settings:*\n"
        f"🔹 Study Type: {study_type.capitalize()}\n"
        f"🔹 Nudge Frequency: {nudge_frequency[0]}-{nudge_frequency[1]} mins",
        parse_mode="Markdown"
    )


### 🔟 BOT SETUP
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setstudy", set_study_type))
    app.add_handler(CommandHandler("setfrequency", set_nudge_frequency))
    app.add_handler(CommandHandler("startnudges", start_nudges))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))

    app.run_polling()


if __name__ == "__main__":
    main()
