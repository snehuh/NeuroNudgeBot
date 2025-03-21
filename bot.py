import time
import random
import logging
from telegram import Bot
from dotenv import load_dotenv
import os

''' Neuro Nudge Bot: The Bot that reminds you of you of your tasks at random intervals to surprise you

This is the first version of this bot and it is very static with the bare minimum functions

To be done later:
1. Communicate to bot what your task is 
2. Create custom messages to remind you
3. Increase or decrease frequency - total number 
4. Add any images along with the message

And more!

'''

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Messages for random nudges
NUDGES = [
    "Hey! Have you worked on your cybersecurity studies today? 👀",
    "Quick check-in! Did you complete any TryHackMe rooms yet? 💻",
    "Don't forget about your CCNA/CompTIA Security+ progress! Keep pushing! 🚀",
    "Time for a small study session? Even 15 minutes counts! 📖",
    "Hey, just a friendly nudge—keep your momentum going! 💡",
    "How’s your cybersecurity portfolio coming along? Need help? 🎯"
]

#logging
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_nudge():
    message = random.choice(NUDGES)
    bot.send_message(chat_id=TELEGRAN_CHAT_ID, text=message)
    logging.info(f"Sent nudge: {message}")


if __name__ == "__main__":
    while True:
        #sends a nudge every 0.5 to 2 hours randomly
        wait_time = random.randint(1800,7200)  #seconds
        send_nudge()
        time.sleep(wait_time)