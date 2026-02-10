import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")

ROLES = {
    "professional": "You are a professional AI assistant.",
    "comedy": "You are a funny AI assistant.",
    "mod": "You are a strict moderator AI.",
}

BLOCKED_WORDS = ["sex", "porn", "xxx", "adult", "nude", "fuck"]
user_roles = {}

# ================= START MENU =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("👔 Professional", callback_data="professional"),
            InlineKeyboardButton("😂 Comedy", callback_data="comedy"),
        ],
        [InlineKeyboardButton("🛡 Moderator", callback_data="mod")],
    ]
    await update.message.reply_text(
        "Select AI personality:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================= SET ROLE =================
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_roles[query.from_user.id] = query.data
    await query.edit_message_text(f"Role set to {query.data}")

# ================= AI CHAT =================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id

    if any(word in user_text.lower() for word in BLOCKED_WORDS):
        await update.message.reply_text("❌ I can't respond to that.")
        return

    role = user_roles.get(user_id, "professional")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": ROLES[role]},
            {"role": "user", "content": user_text},
        ],
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20,
        )
        reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = "⚠️ AI server error. Try again."

    await update.message.reply_text(reply)

# ================= MAIN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(set_role))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("Bot running locally...")
app.run_polling()
