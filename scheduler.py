import random
from datetime import datetime, timedelta, time
from telegram.ext import ContextTypes
from storage import get_user
from messages import get_random_message

TIME_WINDOWS = {
    "morning": (time(9, 0), time(12, 0)),
    "afternoon": (time(13, 0), time(17, 0)),
    "fullday": (time(9, 0), time(17, 0))
}

FREQ_WINDOWS = {
    "short": (15, 30),
    "medium": (30, 120),
    "long": (120, 240)
}

async def send_nudge(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.chat_id
    try:
        user = get_user(user_id)
        if not user:
            return

        now = datetime.now().time()
        start, end = TIME_WINDOWS.get(user["time_range"], (time(9, 0), time(17, 0)))
        if not (start <= now <= end):
            return

        message = get_random_message(user["category"], user.get("first_name", "there"))
        await context.bot.send_message(chat_id=user_id, text=message)

        min_min, max_min = FREQ_WINDOWS.get(user["frequency"], (60, 120))
        delay = random.randint(min_min, max_min) * 60
        context.job_queue.run_once(send_nudge, delay=delay, chat_id=user_id)

    except Exception as e:
        print(f"[ERROR] Failed to send nudge to {user_id}: {e}")
