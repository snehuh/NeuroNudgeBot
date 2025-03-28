from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)
from storage import save_user, update_user_field, get_user
from scheduler import send_nudge

CATEGORY_SELECTION, TIME_SELECTION, FREQ_SELECTION = range(3)

categories = {
    "general": "🧠 General",
    "cyber": "🛡️ Cybersecurity",
    "both": "🌐 Both"
}

time_ranges = {
    "morning": "🕘 9AM–12PM",
    "afternoon": "🕐 1PM–5PM",
    "fullday": "⏰ 9AM–5PM"
}

frequencies = {
    "short": "Every 15–30 min",
    "medium": "Every 30 min – 2 hrs",
    "long": "Every 2–4 hrs"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(categories["general"], callback_data="category_general"),
            InlineKeyboardButton(categories["cyber"], callback_data="category_cyber")
        ],
        [InlineKeyboardButton(categories["both"], callback_data="category_both")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Hi {update.effective_user.first_name}! Welcome to *NudgeByAnu*.\n\n"
        "Let's get you started.\n\n"
        "*Choose your focus area:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CATEGORY_SELECTION

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected = query.data.replace("category_", "")

    await save_user(user_id, {
        "user_id": user_id,
        "category": selected,
        "first_name": query.from_user.first_name,
        "username": query.from_user.username
    })

    keyboard = [
        [
            InlineKeyboardButton(time_ranges["morning"], callback_data="time_morning"),
            InlineKeyboardButton(time_ranges["afternoon"], callback_data="time_afternoon")
        ],
        [InlineKeyboardButton(time_ranges["fullday"], callback_data="time_fullday")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✅ Focus area saved.\n\n*Choose your active time range:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return TIME_SELECTION

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected = query.data.replace("time_", "")

    await update_user_field(user_id, "time_range", selected)

    keyboard = [
        [InlineKeyboardButton(frequencies["short"], callback_data="freq_short")],
        [InlineKeyboardButton(frequencies["medium"], callback_data="freq_medium")],
        [InlineKeyboardButton(frequencies["long"], callback_data="freq_long")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"⏰ Time range saved.\n\n*How often do you want to receive nudges?*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return FREQ_SELECTION

async def handle_frequency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected = query.data.replace("freq_", "")

    await update_user_field(user_id, "frequency", selected)

    await query.edit_message_text(
        f"✅ You're all set!\n\nUse /startnudges to begin your nudges any time 🚀"
    )
    return ConversationHandler.END

async def handle_view_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)

    if not user:
        await query.edit_message_text("⚠️ No settings found. Please use /start to configure first.")
        return

    if query.data == "view_category":
        category = user.get("category", "Not set").capitalize()
        await query.edit_message_text(f"🧠 Your current focus area is: *{category}*", parse_mode="Markdown")

    elif query.data == "view_time":
        display_map = {
            "morning": "9AM–12PM",
            "afternoon": "1PM–5PM",
            "fullday": "9AM–5PM"
        }
        tr = user.get("time_range")
        time_range = display_map.get(tr, "Not set")
        await query.edit_message_text(f"⏰ Your active time window is: *{time_range}*", parse_mode="Markdown")

    elif query.data == "view_freq":
        display_map = {
            "short": "Every 15–30 min",
            "medium": "Every 30 min – 2 hrs",
            "long": "Every 2–4 hrs"
        }
        freq = user.get("frequency")
        frequency = display_map.get(freq, "Not set")
        await query.edit_message_text(f"⚙️ Your frequency is: *{frequency}*", parse_mode="Markdown")



async def startnudges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await get_user(user_id)

    # if no user record, create one with defaults
    user = {
        "user_id": user_id,
        "first_name": update.effective_user.first_name,
        "category": "general",
        "time_range": "fullday",
        "frequency": "medium"
    }
    await save_user(user_id, user)

    # defaults
    defaults = {
        "category": "general",
        "time_range": "fullday",
        "frequency": "medium"       
    }

    updated = False
    for key, val in defaults.items():
        if key not in user:
            user[key] = val
            await update_user_field(user_id, key, val)

    if updated:
        await update.message.reply_text("ℹ️ You hadn't completed setup — so we filled in some defaults for you.")

    await update.message.reply_text("✅ Nudges activated! I’ll ping you randomly within your set window.")
    context.job_queue.run_once(send_nudge, when=5, chat_id=user_id)


async def stopnudges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_jobs = context.job_queue.get_jobs_by_chat_id(update.effective_user.id)
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("🛑 Nudges stopped.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🧠 My Focus Area", callback_data="view_category"),
            InlineKeyboardButton("⏰ My Time Ranges", callback_data="view_time")
        ],
        [
            InlineKeyboardButton("⚙️ Frequency", callback_data="view_freq"),
            InlineKeyboardButton("❓ Help", callback_data="view_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Here’s your menu:", reply_markup=reply_markup)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧾 *NeuroNudgeBot Help*\n\n"
        "This bot sends you random productivity reminders within your chosen time range.\n\n"
        "Use /start to begin setup or /menu to manage your settings.",
        parse_mode="Markdown"
    )

async def register_menu_commands(app):
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("startnudges", startnudges))
    app.add_handler(CommandHandler("stopnudges", stopnudges))
    app.add_handler(CallbackQueryHandler(handle_view_buttons, pattern="^view_"))

    await app.bot.set_my_commands([
        BotCommand("start", "Begin setting up your nudges"),
        BotCommand("menu", "Open your personal menu"),
        BotCommand("startnudges", "Activate your nudge schedule"),
        BotCommand("stopnudges", "Stop all reminders"),
        BotCommand("help", "Show help and how to use this bot")
    ])

def setup_conversation_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY_SELECTION: [CallbackQueryHandler(handle_category_selection)],
            TIME_SELECTION: [CallbackQueryHandler(handle_time_selection)],
            FREQ_SELECTION: [CallbackQueryHandler(handle_frequency_selection)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
