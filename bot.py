import os
import asyncio
import random
import logging
from datetime import datetime, time
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize the bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("neuronudgebot.log"),
        logging.StreamHandler()
    ]
)

# Nudge messages
NUDGES = [
    "Hey Sneha! Have you reviewed a TryHackMe room today? 🕵️‍♀️",
    "Reminder: CCNA and Security+ won't study themselves 😅",
    "Time to flex those cyber muscles 💪 Hack something small today!",
    "Don't forget to update your cybersecurity portfolio 🧠",
    "Feeling stuck? Do 15 mins of TryHackMe — small wins add up!",
    "NeuroNudge says: go conquer a THM challenge 🚀",
    "Review your notes or flashcards – tiny effort, big reward! 🧠",
    "Ping! Let’s get one thing done for your future self 👩‍💻"
]

# Define active hours
START_HOUR = 9
END_HOUR = 17

def within_active_hours():
    now = datetime.now().time()
    return time(START_HOUR, 0) <= now <= time(END_HOUR, 0)

async def send_nudge():
    message = random.choice(NUDGES)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f"Sent nudge: {message}")
    except Exception as e:
        logging.error(f"Failed to send nudge: {e}")

async def run_nudger():
    while True:
        if within_active_hours():
            await send_nudge()
            # Wait between 2 to 4 hours randomly
            wait_time = random.randint(7200, 14400)
        else:
            logging.info("Outside active hours. Sleeping for 30 minutes.")
            wait_time = 1800  # 30 minutes

        await asyncio.sleep(wait_time)

if __name__ == "__main__":
    logging.info("NeuroNudgeBot started.")
    asyncio.run(run_nudger())
