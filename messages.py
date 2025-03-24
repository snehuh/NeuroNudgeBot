import random

GENERAL_MESSAGES = [
    "Have you started on your tasks yet?",
    "Remember your goals today.",
    "Small steps count too!",
    "Take a breath, then take action.",
    "Hope you’re halfway there!"
]

CYBER_MESSAGES = [
    "Have you checked your password hygiene today?",
    "Stay sharp, stay secure.",
    "Two-factor everything.",
    "Don't click strange links!",
    "Update your software, always."
]

def get_random_message(category_key, user_name):
    if category_key == "both":
        pool = GENERAL_MESSAGES + CYBER_MESSAGES
    elif category_key == "general":
        pool = GENERAL_MESSAGES
    elif category_key == "cyber":
        pool = CYBER_MESSAGES
    else:
        pool = GENERAL_MESSAGES
    return f"Hi {user_name}, {random.choice(pool)}"
